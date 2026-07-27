from __future__ import annotations

import hashlib
import importlib.util
import stat
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_build_extension_module():
    script = ROOT / "scripts" / "build_extension.py"
    spec = importlib.util.spec_from_file_location("build_extension", script)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_release_payload_contract_excludes_repo_infra_and_duplicate():
    build_extension = load_build_extension_module()

    payload = set(build_extension.release_payload_paths(ROOT))

    assert Path("blender_manifest.toml") in payload
    assert Path("LICENSE") in payload
    assert Path("__init__.py") in payload
    assert Path("achievements") / "__init__.py" in payload
    assert Path("achievements") / "catalog.py" in payload
    assert Path("achievements") / "rewards.py" in payload
    assert Path("achievements_v01 (4).py") not in payload
    assert Path("README.md") not in payload
    assert Path("AGENTS.md") not in payload
    for path in payload:
        assert path.parts[0] not in {
            ".agents",
            ".codex",
            ".github",
            "docs",
            "plugins",
            "reports",
            "scripts",
            "tests",
        }
        assert "__pycache__" not in path.parts
        assert path.suffix not in {".pyc", ".pyo"}


def test_license_is_the_complete_official_gpl_v3_text():
    license_bytes = (ROOT / "LICENSE").read_bytes()
    normalized_license = license_bytes.replace(b"\r\n", b"\n")

    assert b"\r" not in normalized_license
    assert hashlib.sha256(normalized_license).hexdigest() == (
        "8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903"
    )
    assert b"GNU GENERAL PUBLIC LICENSE" in license_bytes
    assert b"Version 3, 29 June 2007" in license_bytes
    assert b"17. Interpretation of Sections 15 and 16." in license_bytes
    assert b"How to Apply These Terms to Your New Programs" in license_bytes


def test_prepare_release_source_copies_exact_payload(tmp_path):
    build_extension = load_build_extension_module()
    source_dir = tmp_path / "source"

    payload = set(
        build_extension.prepare_release_source(ROOT, source_dir, generated_root=tmp_path)
    )
    copied = {
        path.relative_to(source_dir)
        for path in source_dir.rglob("*")
        if path.is_file()
    }

    assert copied == payload
    assert (source_dir / "blender_manifest.toml").is_file()
    assert (source_dir / "LICENSE").is_file()
    assert (source_dir / "__init__.py").is_file()
    assert (source_dir / "achievements" / "catalog.py").is_file()
    assert not (source_dir / "README.md").exists()
    assert not (source_dir / "tests").exists()


def test_prepare_release_source_rejects_repo_paths():
    build_extension = load_build_extension_module()

    with pytest.raises(ValueError, match="generated reports root"):
        build_extension.prepare_release_source(ROOT, ROOT / "achievements")


def test_extension_commands_are_explicit(tmp_path):
    build_extension = load_build_extension_module()
    blender = Path("blender")
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "dist"

    validate_cmd = build_extension.extension_validate_command(blender, source_dir)
    build_cmd = build_extension.extension_build_command(blender, source_dir, output_dir)
    server_cmd = build_extension.extension_server_generate_command(blender, output_dir)

    assert validate_cmd == [
        "blender",
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "validate",
        str(source_dir),
    ]
    assert build_cmd == [
        "blender",
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "build",
        "--source-dir",
        str(source_dir),
        "--output-dir",
        str(output_dir),
    ]
    assert server_cmd == [
        "blender",
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "server-generate",
        "--repo-dir",
        str(output_dir),
        "--html",
    ]


def test_extension_commands_use_repo_relative_paths_for_workspace_outputs():
    build_extension = load_build_extension_module()
    blender = Path("blender")
    source_dir = ROOT / "reports" / "extension" / "source"
    output_dir = ROOT / "reports" / "extension"

    validate_cmd = build_extension.extension_validate_command(blender, source_dir)
    build_cmd = build_extension.extension_build_command(blender, source_dir, output_dir)
    server_cmd = build_extension.extension_server_generate_command(blender, output_dir)

    assert str(ROOT) not in validate_cmd
    assert str(ROOT) not in build_cmd
    assert str(ROOT) not in server_cmd
    assert validate_cmd[-1] == str(Path("reports") / "extension" / "source")
    assert build_cmd[7] == str(Path("reports") / "extension" / "source")
    assert build_cmd[9] == str(Path("reports") / "extension")
    assert server_cmd[7] == str(Path("reports") / "extension")


def test_release_helper_defaults_to_print_only(monkeypatch, tmp_path, capsys):
    build_extension = load_build_extension_module()
    monkeypatch.setattr(
        build_extension,
        "prepare_release_source",
        lambda *_args, **_kwargs: (Path("__init__.py"),),
    )
    monkeypatch.setattr(build_extension, "find_blender_path", lambda: Path("blender"))

    def unexpected_execution(*_args, **_kwargs):
        raise AssertionError("default packaging mode must not launch Blender")

    monkeypatch.setattr(build_extension, "run_extension_commands", unexpected_execution)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_extension.py",
            "--source-dir",
            str(tmp_path / "source"),
            "--output-dir",
            str(tmp_path / "output"),
        ],
    )

    assert build_extension.main() == 0
    output = capsys.readouterr().out
    assert "--factory-startup" in output
    assert "Commands were not executed" in output
    assert "--run-blender" in output


def test_shell_command_formatting_quotes_paths_with_spaces():
    build_extension = load_build_extension_module()
    command = [
        r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "validate",
        r"reports\extension\source",
    ]

    assert build_extension.format_shell_command(command, platform_name="nt") == (
        "& 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe' "
        "'--background' '--factory-startup' '--command' 'extension' 'validate' "
        "'reports\\extension\\source'"
    )
    assert build_extension.format_shell_command(command, platform_name="posix") == (
        "'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe' "
        "--background --factory-startup --command extension validate "
        "'reports\\extension\\source'"
    )


def test_extension_runner_uses_one_disposable_isolated_profile(tmp_path):
    build_extension = load_build_extension_module()
    blender = Path("blender")
    source_dir = tmp_path / "source"
    output_dir = tmp_path / "output"
    commands = (
        build_extension.extension_validate_command(blender, source_dir),
        build_extension.extension_build_command(blender, source_dir, output_dir),
        build_extension.extension_server_generate_command(blender, output_dir),
    )
    outputs = {
        "validate": 'Success parsing TOML in "source"\n',
        "build": 'building: achievements-0.2.1.zip\ncomplete\ncreated: "candidate.zip"\n',
        "server-generate": "found 1 packages.\n",
    }
    calls = []

    def fake_runner(command, **kwargs):
        name = build_extension.extension_command_name(command)
        calls.append((tuple(command), dict(kwargs)))
        return subprocess.CompletedProcess(command, 0, stdout=outputs[name])

    executions = build_extension.run_extension_commands(
        commands,
        temp_parent=tmp_path,
        runner=fake_runner,
    )

    assert [execution.name for execution in executions] == [
        "validate",
        "build",
        "server-generate",
    ]
    assert len(calls) == 3
    profiles = {call[1]["env"]["HOME"] for call in calls}
    assert len(profiles) == 1
    profile = Path(profiles.pop())
    assert all(call[1]["env"]["USERPROFILE"] == str(profile) for call in calls)
    assert all(
        call[1]["env"]["BLENDER_USER_RESOURCES"]
        == str(profile / "blender-user-resources")
        for call in calls
    )
    assert all("--factory-startup" in call[0] for call in calls)
    assert all(call[1]["stderr"] is subprocess.STDOUT for call in calls)
    assert not profile.exists()


def test_extension_runner_warns_when_windows_style_cleanup_is_incomplete(
    monkeypatch,
    tmp_path,
    capsys,
):
    build_extension = load_build_extension_module()
    command = build_extension.extension_validate_command(Path("blender"), tmp_path / "source")
    profiles = []

    def fake_runner(command, **kwargs):
        profiles.append(Path(kwargs["env"]["HOME"]))
        return subprocess.CompletedProcess(
            command,
            0,
            stdout='Success parsing TOML in "source"\n',
        )

    real_rmtree = build_extension.shutil.rmtree
    monkeypatch.setattr(build_extension.shutil, "rmtree", lambda *_args, **_kwargs: None)
    try:
        executions = build_extension.run_extension_commands(
            (command,),
            temp_parent=tmp_path,
            runner=fake_runner,
        )
        assert [execution.name for execution in executions] == ["validate"]
        assert profiles[0].exists()
        assert "temporary profile cleanup incomplete" in capsys.readouterr().err
    finally:
        for profile in profiles:
            real_rmtree(profile, ignore_errors=True)


def test_server_generation_rejects_stale_output_without_deleting_it(tmp_path):
    build_extension = load_build_extension_module()
    output_dir = tmp_path / "extension-validation"
    source_dir = output_dir / "source"
    source_dir.mkdir(parents=True)

    build_extension.validate_fresh_server_output(output_dir, source_dir)

    old_baseline = output_dir / "achievements-0.1.0.zip"
    old_baseline.write_bytes(b"owner baseline")
    with pytest.raises(ValueError, match="fresh per-run output directory") as exc_info:
        build_extension.validate_fresh_server_output(output_dir, source_dir)

    assert old_baseline.name in str(exc_info.value)
    assert old_baseline.read_bytes() == b"owner baseline"


@pytest.mark.parametrize(
    ("name", "returncode", "output", "message"),
    [
        ("validate", 1, "Success parsing TOML\n", "exit code 1"),
        (
            "validate",
            0,
            "Success parsing TOML\nTraceback (most recent call last):\n",
            "failure marker",
        ),
        ("build", 0, "complete\n", "missing expected success marker"),
        (
            "validate",
            0,
            "Success parsing TOML\nerror: lowercase failure\n",
            "failure marker",
        ),
        (
            "server-generate",
            0,
            "WARN: duplicate extension id\nfound 1 packages.\n",
            "failure marker",
        ),
    ],
)
def test_extension_result_validation_fails_closed(name, returncode, output, message):
    build_extension = load_build_extension_module()
    result = subprocess.CompletedProcess(["blender"], returncode, stdout=output)

    with pytest.raises(RuntimeError, match=message):
        build_extension.validate_extension_command_result(name, result)


def test_extension_runner_rejects_non_isolated_commands(tmp_path):
    build_extension = load_build_extension_module()
    unsafe = ["blender", "--background", "--command", "extension", "validate", "source"]

    with pytest.raises(ValueError, match="--factory-startup"):
        build_extension.run_extension_commands((unsafe,), temp_parent=tmp_path)


def write_minimal_payload(root: Path, *, line_ending: bytes = b"\n") -> None:
    root.mkdir(parents=True)
    package = root / "achievements"
    package.mkdir()
    (root / "blender_manifest.toml").write_bytes(b'version = "0.2.1"' + line_ending)
    (root / "LICENSE").write_bytes(b"GNU GPL v3" + line_ending)
    (root / "__init__.py").write_bytes(b"ROOT = True" + line_ending)
    (package / "__init__.py").write_bytes(b"PACKAGE = True" + line_ending)


def run_git(root: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=True,
    )


def init_runtime_git_repo(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    write_minimal_payload(root, line_ending=b"\r\n")
    (root / "achievements" / "payload.bin").write_bytes(b"\x00\r\n\xff")
    run_git(root, "init")
    run_git(root, "config", "user.email", "packaging-tests@example.invalid")
    run_git(root, "config", "user.name", "Packaging Tests")
    run_git(root, "config", "core.autocrlf", "false")
    run_git(root, "add", ".")
    run_git(root, "commit", "-m", "fixture")
    return root


def minimal_archive_payload() -> dict[Path, bytes]:
    return {
        Path("blender_manifest.toml"): b'manifest\n',
        Path("LICENSE"): b"license\n",
        Path("__init__.py"): b"root\n",
        Path("achievements/__init__.py"): b"package\n",
    }


def write_archive(path: Path, members: list[tuple[str, bytes]], *, stored: bool = False) -> None:
    compression = zipfile.ZIP_STORED if stored else zipfile.ZIP_DEFLATED
    with zipfile.ZipFile(path, "w", compression=compression) as archive:
        for name, data in members:
            archive.writestr(name, data)


def test_working_tree_mode_normalizes_only_known_utf8_runtime_files(tmp_path):
    build_extension = load_build_extension_module()
    root = tmp_path / "repo"
    write_minimal_payload(root, line_ending=b"\r\n")
    binary = b"\x00\r\n\xff"
    opaque_text = b"opaque\r\nbytes\r"
    (root / "achievements" / "payload.bin").write_bytes(binary)
    (root / "achievements" / "payload.txt").write_bytes(opaque_text)
    generated_root = tmp_path / "generated"
    source_dir = generated_root / "source"

    build_extension.prepare_release_source(
        root,
        source_dir,
        generated_root=generated_root,
    )

    for relative_path in (
        Path("blender_manifest.toml"),
        Path("LICENSE"),
        Path("__init__.py"),
        Path("achievements/__init__.py"),
    ):
        data = (source_dir / relative_path).read_bytes()
        assert b"\r" not in data
        assert data.endswith(b"\n")
    assert (source_dir / "achievements" / "payload.bin").read_bytes() == binary
    assert (source_dir / "achievements" / "payload.txt").read_bytes() == opaque_text


def test_revision_mode_copies_exact_git_blob_bytes(tmp_path):
    build_extension = load_build_extension_module()
    root = init_runtime_git_repo(tmp_path)
    generated_root = tmp_path / "generated"
    source_dir = generated_root / "source"

    payload = build_extension.prepare_release_source(
        root,
        source_dir,
        generated_root=generated_root,
        revision="HEAD",
    )

    for relative_path in payload:
        blob = run_git(root, "show", f"HEAD:{relative_path.as_posix()}").stdout
        assert (source_dir / relative_path).read_bytes() == blob
    assert (source_dir / "__init__.py").read_bytes().endswith(b"\r\n")


def test_revision_mode_rejects_dirty_and_untracked_runtime_files(tmp_path):
    build_extension = load_build_extension_module()
    root = init_runtime_git_repo(tmp_path)
    original = (root / "__init__.py").read_bytes()
    generated_root = tmp_path / "generated"

    (root / "__init__.py").write_bytes(b"dirty\n")
    with pytest.raises(ValueError, match="clean tracked and untracked runtime payload"):
        build_extension.prepare_release_source(
            root,
            generated_root / "dirty-source",
            generated_root=generated_root,
            revision="HEAD",
        )

    (root / "__init__.py").write_bytes(original)
    (root / "achievements" / "untracked.py").write_text("UNTRACKED = True\n", encoding="utf-8")
    with pytest.raises(ValueError, match="clean tracked and untracked runtime payload"):
        build_extension.prepare_release_source(
            root,
            generated_root / "untracked-source",
            generated_root=generated_root,
            revision="HEAD",
        )


def test_prepare_release_source_rejects_stale_unexpected_output(tmp_path):
    build_extension = load_build_extension_module()
    root = tmp_path / "repo"
    write_minimal_payload(root)
    generated_root = tmp_path / "generated"
    source_dir = generated_root / "source"
    source_dir.mkdir(parents=True)
    (source_dir / "unexpected.txt").write_text("stale\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Prepared source contains unexpected files"):
        build_extension.prepare_release_source(
            root,
            source_dir,
            clean=False,
            generated_root=generated_root,
        )
    assert (source_dir / "unexpected.txt").read_text(encoding="utf-8") == "stale\n"
    assert not (source_dir / "__init__.py").exists()


def test_archive_member_digests_are_repeatable_across_zip_metadata(tmp_path):
    build_extension = load_build_extension_module()
    expected = minimal_archive_payload()
    first = tmp_path / "first.zip"
    second = tmp_path / "second.zip"
    members = [(path.as_posix(), data) for path, data in expected.items()]
    write_archive(first, members)
    write_archive(second, list(reversed(members)), stored=True)

    first_digests = build_extension.extension_archive_member_digests(
        first,
        expected,
        expected_bytes=expected,
    )
    second_digests = build_extension.extension_archive_member_digests(
        second,
        expected,
        expected_bytes=expected,
    )

    assert first_digests == second_digests
    assert list(first_digests) == sorted(path.as_posix() for path in expected)


@pytest.mark.parametrize("unsafe_name", ["../escape.py", "/absolute.py"])
def test_archive_rejects_path_traversal_and_non_posix_names(tmp_path, unsafe_name):
    build_extension = load_build_extension_module()
    expected = minimal_archive_payload()
    archive_path = tmp_path / "unsafe.zip"
    members = [(path.as_posix(), data) for path, data in expected.items()]
    members.append((unsafe_name, b"unsafe"))
    write_archive(archive_path, members)

    with pytest.raises(ValueError, match="Unsafe extension archive member"):
        build_extension.extension_archive_member_digests(archive_path, expected)


def test_archive_member_name_validator_rejects_backslashes():
    build_extension = load_build_extension_module()

    with pytest.raises(ValueError, match="Unsafe extension archive member"):
        build_extension._validate_archive_member_name("a\\b.py")

    with pytest.raises(ValueError, match="Unsafe extension archive member"):
        build_extension._validate_archive_member_name("C:/escape.py")


def test_archive_rejects_duplicate_members(tmp_path):
    build_extension = load_build_extension_module()
    expected = minimal_archive_payload()
    archive_path = tmp_path / "duplicate.zip"
    members = [(path.as_posix(), data) for path, data in expected.items()]
    members.append(("__init__.py", b"duplicate"))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)
        write_archive(archive_path, members)

    with pytest.raises(ValueError, match="Duplicate extension archive member"):
        build_extension.extension_archive_member_digests(archive_path, expected)


def test_archive_rejects_symlink_members(tmp_path):
    build_extension = load_build_extension_module()
    expected = minimal_archive_payload()
    archive_path = tmp_path / "symlink.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path, data in expected.items():
            archive.writestr(path.as_posix(), data)
        symlink = zipfile.ZipInfo("achievements/link.py")
        symlink.create_system = 3
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(symlink, b"target.py")

    with pytest.raises(ValueError, match="Symlink is not allowed"):
        build_extension.extension_archive_member_digests(archive_path, expected)


def test_archive_rejects_non_regular_members(tmp_path):
    build_extension = load_build_extension_module()
    expected = minimal_archive_payload()
    archive_path = tmp_path / "fifo.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        for path, data in expected.items():
            if path != Path("__init__.py"):
                archive.writestr(path.as_posix(), data)
                continue
            fifo = zipfile.ZipInfo(path.as_posix())
            fifo.create_system = 3
            fifo.external_attr = (stat.S_IFIFO | 0o644) << 16
            archive.writestr(fifo, data)

    with pytest.raises(ValueError, match="Non-regular file is not allowed"):
        build_extension.extension_archive_member_digests(archive_path, expected)


def test_archive_rejects_unexpected_and_byte_mismatched_members(tmp_path):
    build_extension = load_build_extension_module()
    expected = minimal_archive_payload()
    unexpected_path = tmp_path / "unexpected.zip"
    members = [(path.as_posix(), data) for path, data in expected.items()]
    write_archive(unexpected_path, [*members, ("achievements/debug.py", b"debug\n")])

    with pytest.raises(ValueError, match="Extension archive payload mismatch"):
        build_extension.extension_archive_member_digests(unexpected_path, expected)

    mismatched_path = tmp_path / "mismatched.zip"
    mismatched = [
        (name, b"changed\n" if name == "__init__.py" else data) for name, data in members
    ]
    write_archive(mismatched_path, mismatched)
    with pytest.raises(ValueError, match="member bytes differ"):
        build_extension.extension_archive_member_digests(
            mismatched_path,
            expected,
            expected_bytes=expected,
        )


def test_blender_ci_matrix_is_fixed_and_fully_blocking():
    workflow = (ROOT / ".github" / "workflows" / "blender-smoke.yml").read_text(
        encoding="utf-8"
    )

    for version in ("5.0.1", "5.1.2", "5.2.0"):
        assert f"blender-{version}-linux-x64.tar.xz" in workflow
    for forbidden in (
        "continue-on-error",
        "BLENDER_5_2_ALPHA_URL",
        "matrix.canary",
        "skip_smoke",
        "Skipping optional",
    ):
        assert forbidden not in workflow
    assert workflow.count("scripts/run_blender_smoke.py --suite") == 6
