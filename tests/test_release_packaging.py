from __future__ import annotations

import importlib.util
import sys
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
        "--command",
        "extension",
        "validate",
        str(source_dir),
    ]
    assert build_cmd == [
        "blender",
        "--background",
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
    assert build_cmd[6] == str(Path("reports") / "extension" / "source")
    assert build_cmd[8] == str(Path("reports") / "extension")
    assert server_cmd[6] == str(Path("reports") / "extension")


def test_release_helper_prints_commands_without_running_blender():
    script = ROOT / "scripts" / "build_extension.py"
    text = script.read_text(encoding="utf-8")

    assert "--run-blender" not in text
    assert "subprocess" not in text
    assert "run_command" not in text


def test_shell_command_formatting_quotes_paths_with_spaces():
    build_extension = load_build_extension_module()
    command = [
        r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe",
        "--background",
        "--command",
        "extension",
        "validate",
        r"reports\extension\source",
    ]

    assert build_extension.format_shell_command(command, platform_name="nt") == (
        "& 'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe' "
        "'--background' '--command' 'extension' 'validate' "
        "'reports\\extension\\source'"
    )
    assert build_extension.format_shell_command(command, platform_name="posix") == (
        "'C:\\Program Files\\Blender Foundation\\Blender 5.1\\blender.exe' "
        "--background --command extension validate 'reports\\extension\\source'"
    )
