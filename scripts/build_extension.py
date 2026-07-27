from __future__ import annotations

import argparse
import hashlib
import os
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "extension"
DEFAULT_SOURCE_DIR = DEFAULT_OUTPUT_DIR / "source"
RUNTIME_FILES = (
    Path("blender_manifest.toml"),
    Path("LICENSE"),
    Path("__init__.py"),
)
RUNTIME_DIRS = (Path("achievements"),)
EXCLUDED_DIR_NAMES = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}
UTF8_TEXT_FILENAMES = {"LICENSE"}
UTF8_TEXT_SUFFIXES = {".py", ".toml"}
EXTENSION_FAILURE_MARKERS = (
    "traceback (most recent call last):",
    "error:",
    "warning:",
    "warn:",
)
EXTENSION_SUCCESS_MARKERS = {
    "validate": ("Success parsing TOML",),
    "build": ("complete", "created:"),
    "server-generate": ("found 1 packages.",),
}
DEFAULT_EXTENSION_TIMEOUT_SECONDS = 180


@dataclass(frozen=True, slots=True)
class ExtensionCommandExecution:
    """One successful isolated Blender extension command execution."""

    name: str
    command: tuple[str, ...]
    output: str


def _is_excluded(relative_path: Path) -> bool:
    return any(part in EXCLUDED_DIR_NAMES for part in relative_path.parts) or (
        relative_path.suffix in EXCLUDED_SUFFIXES
    )


def validate_payload_paths(paths: Iterable[Path]) -> tuple[Path, ...]:
    """Validate and deterministically order extension payload paths."""
    normalized: list[Path] = []
    seen: set[str] = set()
    seen_casefolded: set[str] = set()

    for raw_path in paths:
        path = Path(raw_path)
        path_text = path.as_posix()
        if (
            path.is_absolute()
            or path.drive
            or not path.parts
            or any(part in {"", ".", ".."} for part in path.parts)
        ):
            raise ValueError(f"Unsafe release payload path: {path_text!r}")
        if path_text in seen or path_text.casefold() in seen_casefolded:
            raise ValueError(f"Duplicate release payload path: {path_text}")
        if path not in RUNTIME_FILES:
            if len(path.parts) < 2 or path.parts[0] != RUNTIME_DIRS[0].as_posix():
                raise ValueError(f"Unexpected release payload path: {path_text}")
            if _is_excluded(path):
                raise ValueError(f"Excluded release payload path: {path_text}")
        seen.add(path_text)
        seen_casefolded.add(path_text.casefold())
        normalized.append(path)

    missing = [path.as_posix() for path in RUNTIME_FILES if path not in normalized]
    package_init = RUNTIME_DIRS[0] / "__init__.py"
    if package_init not in normalized:
        missing.append(package_init.as_posix())
    if missing:
        raise ValueError(f"Missing required release payload paths: {', '.join(missing)}")

    return tuple(sorted(normalized, key=lambda path: path.as_posix()))


def _working_tree_payload_paths(root: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for relative_path in RUNTIME_FILES:
        source = root / relative_path
        if source.is_symlink():
            raise ValueError(f"Symlink is not allowed in release payload: {relative_path}")
        if not source.is_file():
            raise ValueError(f"Missing required release file: {relative_path}")
        paths.append(relative_path)

    for relative_dir in RUNTIME_DIRS:
        source_dir = root / relative_dir
        if source_dir.is_symlink():
            raise ValueError(f"Symlink is not allowed in release payload: {relative_dir}")
        if not source_dir.is_dir():
            raise ValueError(f"Missing required release directory: {relative_dir}")
        for source in sorted(source_dir.rglob("*")):
            relative_path = source.relative_to(root)
            if source.is_symlink():
                raise ValueError(f"Symlink is not allowed in release payload: {relative_path}")
            if not source.is_file() or _is_excluded(relative_path):
                continue
            paths.append(relative_path)
    return validate_payload_paths(paths)


def _run_git(root: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(root), *args],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ValueError(f"Git command failed ({' '.join(args)}): {detail}")
    return result.stdout


def _git_pathspecs() -> tuple[str, ...]:
    return tuple(path.as_posix() for path in (*RUNTIME_FILES, *RUNTIME_DIRS))


def _assert_clean_runtime(root: Path) -> None:
    status = _run_git(
        root,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        *_git_pathspecs(),
    )
    if status:
        readable = status.replace(b"\0", b"\n").decode("utf-8", errors="replace").strip()
        raise ValueError(
            "Revision packaging requires a clean tracked and untracked runtime payload:\n"
            f"{readable}"
        )


def _git_payload_paths(root: Path, revision: str) -> tuple[Path, ...]:
    _run_git(root, "rev-parse", "--verify", f"{revision}^{{commit}}")
    _assert_clean_runtime(root)
    tree = _run_git(root, "ls-tree", "-r", "-z", revision, "--", *_git_pathspecs())
    paths: list[Path] = []
    for raw_entry in tree.split(b"\0"):
        if not raw_entry:
            continue
        try:
            metadata, raw_name = raw_entry.split(b"\t", 1)
            mode, object_type, _object_id = metadata.split(b" ", 2)
            name = raw_name.decode("utf-8")
        except (UnicodeDecodeError, ValueError) as exc:
            raise ValueError("Could not parse Git release payload tree") from exc
        relative_path = Path(name)
        if mode == b"120000":
            raise ValueError(f"Symlink is not allowed in release payload: {name}")
        if object_type != b"blob":
            raise ValueError(f"Non-file Git object is not allowed in release payload: {name}")
        if _is_excluded(relative_path):
            continue
        paths.append(relative_path)
    return validate_payload_paths(paths)


def release_payload_paths(
    root: Path = ROOT,
    *,
    revision: str | None = None,
) -> tuple[Path, ...]:
    root = root.resolve()
    if revision is None:
        return _working_tree_payload_paths(root)
    return _git_payload_paths(root, revision)


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def ensure_generated_subdir(path: Path, *, generated_root: Path = REPORTS_DIR) -> Path:
    if path.is_symlink():
        raise ValueError(f"Release source directory must not be a symlink: {path}")
    resolved_path = path.resolve()
    resolved_root = generated_root.resolve()
    if resolved_path == resolved_root or not is_relative_to(resolved_path, resolved_root):
        raise ValueError(
            f"Release source directory must be under generated reports root "
            f"{resolved_root}: {resolved_path}"
        )
    return resolved_path


def _is_utf8_runtime_text(relative_path: Path) -> bool:
    return relative_path.name in UTF8_TEXT_FILENAMES or (
        relative_path.suffix in UTF8_TEXT_SUFFIXES
    )


def _working_tree_bytes(root: Path, relative_path: Path) -> bytes:
    source = root / relative_path
    if source.is_symlink():
        raise ValueError(f"Symlink is not allowed in release payload: {relative_path}")
    data = source.read_bytes()
    if not _is_utf8_runtime_text(relative_path):
        return data
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"Runtime text file is not valid UTF-8: {relative_path}") from exc
    return text.replace("\r\n", "\n").replace("\r", "\n").encode("utf-8")


def _git_blob_bytes(root: Path, revision: str, relative_path: Path) -> bytes:
    return _run_git(root, "cat-file", "blob", f"{revision}:{relative_path.as_posix()}")


def _source_tree_paths(source_dir: Path) -> tuple[Path, ...]:
    paths: list[Path] = []
    for source in sorted(source_dir.rglob("*")):
        relative_path = source.relative_to(source_dir)
        if source.is_symlink():
            raise ValueError(f"Symlink is not allowed in prepared source: {relative_path}")
        if source.is_file():
            paths.append(relative_path)
    return tuple(paths)


def prepare_release_source(
    root: Path = ROOT,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    *,
    clean: bool = True,
    generated_root: Path = REPORTS_DIR,
    revision: str | None = None,
) -> tuple[Path, ...]:
    root = root.resolve()
    payload = release_payload_paths(root, revision=revision)
    payload_bytes = {
        relative_path: (
            _working_tree_bytes(root, relative_path)
            if revision is None
            else _git_blob_bytes(root, revision, relative_path)
        )
        for relative_path in payload
    }

    source_dir = ensure_generated_subdir(source_dir, generated_root=generated_root)
    if not clean and source_dir.exists():
        existing = set(_source_tree_paths(source_dir))
        unexpected = sorted(existing - set(payload), key=lambda path: path.as_posix())
        if unexpected:
            details = ", ".join(path.as_posix() for path in unexpected)
            raise ValueError(f"Prepared source contains unexpected files: {details}")
    if clean and source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True, exist_ok=True)

    for relative_path, data in payload_bytes.items():
        target = source_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)

    copied = _source_tree_paths(source_dir)
    if set(copied) != set(payload):
        unexpected = sorted(set(copied) - set(payload), key=lambda path: path.as_posix())
        missing = sorted(set(payload) - set(copied), key=lambda path: path.as_posix())
        details = [*(f"unexpected={path.as_posix()}" for path in unexpected)]
        details.extend(f"missing={path.as_posix()}" for path in missing)
        raise ValueError(f"Prepared source payload mismatch: {', '.join(details)}")
    return payload


def payload_member_digests(
    source_dir: Path,
    payload: Iterable[Path],
) -> dict[str, str]:
    validated = validate_payload_paths(payload)
    return {
        relative_path.as_posix(): hashlib.sha256(
            (source_dir / relative_path).read_bytes()
        ).hexdigest()
        for relative_path in validated
    }


def _validate_archive_member_name(name: str) -> Path:
    if "\\" in name or name.endswith("/"):
        raise ValueError(f"Unsafe extension archive member: {name!r}")
    pure_path = PurePosixPath(name)
    if (
        pure_path.is_absolute()
        or not pure_path.parts
        or ":" in pure_path.parts[0]
        or any(part in {"", ".", ".."} for part in pure_path.parts)
        or pure_path.as_posix() != name
    ):
        raise ValueError(f"Unsafe extension archive member: {name!r}")
    return Path(*pure_path.parts)


def extension_archive_member_digests(
    archive_path: Path,
    expected_payload: Iterable[Path],
    *,
    expected_bytes: Mapping[Path, bytes] | None = None,
) -> dict[str, str]:
    expected = validate_payload_paths(expected_payload)
    expected_set = set(expected)
    member_data: dict[Path, bytes] = {}
    seen_names: set[str] = set()
    seen_casefolded: set[str] = set()

    with zipfile.ZipFile(archive_path) as archive:
        for member in archive.infolist():
            name = member.filename
            if name in seen_names or name.casefold() in seen_casefolded:
                raise ValueError(f"Duplicate extension archive member: {name}")
            seen_names.add(name)
            seen_casefolded.add(name.casefold())
            relative_path = _validate_archive_member_name(name)
            unix_mode = (member.external_attr >> 16) & 0xFFFF
            if unix_mode and stat.S_ISLNK(unix_mode):
                raise ValueError(f"Symlink is not allowed in extension archive: {name}")
            if stat.S_IFMT(unix_mode) and not stat.S_ISREG(unix_mode):
                raise ValueError(
                    f"Non-regular file is not allowed in extension archive: {name}"
                )
            member_data[relative_path] = archive.read(member)

    actual_set = set(member_data)
    if actual_set != expected_set:
        unexpected = sorted(actual_set - expected_set, key=lambda path: path.as_posix())
        missing = sorted(expected_set - actual_set, key=lambda path: path.as_posix())
        details = [*(f"unexpected={path.as_posix()}" for path in unexpected)]
        details.extend(f"missing={path.as_posix()}" for path in missing)
        raise ValueError(f"Extension archive payload mismatch: {', '.join(details)}")

    if expected_bytes is not None:
        for relative_path in expected:
            if relative_path not in expected_bytes:
                raise ValueError(
                    f"Missing expected bytes for extension archive member: {relative_path}"
                )
            if member_data[relative_path] != expected_bytes[relative_path]:
                raise ValueError(f"Extension archive member bytes differ: {relative_path}")

    return {
        relative_path.as_posix(): hashlib.sha256(member_data[relative_path]).hexdigest()
        for relative_path in expected
    }


def blender_cli_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def extension_validate_command(blender: Path, source_dir: Path) -> list[str]:
    return [
        str(blender),
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "validate",
        blender_cli_path(source_dir),
    ]


def extension_build_command(blender: Path, source_dir: Path, output_dir: Path) -> list[str]:
    return [
        str(blender),
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "build",
        "--source-dir",
        blender_cli_path(source_dir),
        "--output-dir",
        blender_cli_path(output_dir),
    ]


def extension_server_generate_command(blender: Path, output_dir: Path) -> list[str]:
    return [
        str(blender),
        "--background",
        "--factory-startup",
        "--command",
        "extension",
        "server-generate",
        "--repo-dir",
        blender_cli_path(output_dir),
        "--html",
    ]


def extension_command_name(command: Sequence[str]) -> str:
    """Return and validate the Blender extension subcommand name."""
    try:
        command_index = command.index("--command")
        extension_name = command[command_index + 1]
        subcommand = command[command_index + 2]
    except (ValueError, IndexError) as exc:
        raise ValueError(f"Malformed Blender extension command: {tuple(command)!r}") from exc
    if extension_name != "extension" or subcommand not in EXTENSION_SUCCESS_MARKERS:
        raise ValueError(f"Unsupported Blender extension command: {tuple(command)!r}")
    if "--background" not in command or "--factory-startup" not in command:
        raise ValueError(
            "Blender extension commands must use --background and --factory-startup"
        )
    return subcommand


def extension_cli_env(
    profile_root: Path,
    *,
    base_env: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Return an environment isolated from every real Blender user profile."""
    profile_root = profile_root.resolve()
    blender_user_resources = profile_root / "blender-user-resources"
    blender_user_resources.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ if base_env is None else base_env)
    env["HOME"] = str(profile_root)
    env["USERPROFILE"] = str(profile_root)
    env["BLENDER_USER_RESOURCES"] = str(blender_user_resources)
    return env


def validate_extension_command_result(
    name: str,
    result: subprocess.CompletedProcess[str],
) -> None:
    """Fail closed unless Blender reports the expected clean success output."""
    if name not in EXTENSION_SUCCESS_MARKERS:
        raise ValueError(f"Unsupported Blender extension command result: {name}")
    output = result.stdout or ""
    normalized_output = output.casefold()
    failures: list[str] = []
    if result.returncode != 0:
        failures.append(f"exit code {result.returncode}")
    present_failure = next(
        (marker for marker in EXTENSION_FAILURE_MARKERS if marker in normalized_output),
        None,
    )
    if present_failure is not None:
        failures.append(f"failure marker {present_failure!r}")
    missing_success = [
        marker for marker in EXTENSION_SUCCESS_MARKERS[name] if marker not in output
    ]
    if missing_success:
        failures.append(f"missing expected success marker(s): {', '.join(missing_success)}")
    if failures:
        detail = "; ".join(failures)
        raise RuntimeError(f"Blender extension {name} failed closed: {detail}\n{output}")


def validate_fresh_server_output(output_dir: Path, source_dir: Path) -> None:
    """Require a server-generation output containing only this run's source tree."""
    output_dir = output_dir.resolve()
    source_dir = source_dir.resolve()
    if not output_dir.exists():
        return
    allowed_source = source_dir if is_relative_to(source_dir, output_dir) else None
    stale: list[Path] = []
    for entry in output_dir.iterdir():
        if entry.is_symlink():
            stale.append(entry)
            continue
        if allowed_source is not None and entry.resolve() == allowed_source:
            continue
        stale.append(entry)
    if stale:
        details = ", ".join(entry.name for entry in sorted(stale, key=lambda path: path.name))
        raise ValueError(
            "server-generate requires a fresh per-run output directory; "
            f"unexpected existing entries: {details}"
        )


def run_extension_commands(
    commands: Iterable[Sequence[str]],
    *,
    cwd: Path = ROOT,
    temp_parent: Path | None = None,
    timeout_seconds: int = DEFAULT_EXTENSION_TIMEOUT_SECONDS,
    runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
) -> tuple[ExtensionCommandExecution, ...]:
    """Run Blender extension commands in one disposable, isolated profile."""
    prepared = tuple(tuple(str(part) for part in command) for command in commands)
    if not prepared:
        raise ValueError("At least one Blender extension command is required")
    command_names = tuple(extension_command_name(command) for command in prepared)
    execute = subprocess.run if runner is None else runner
    parent = None if temp_parent is None else str(temp_parent.resolve())
    executions: list[ExtensionCommandExecution] = []
    profile_root = Path(
        tempfile.mkdtemp(
            prefix="achievements-extension-cli-",
            dir=parent,
        )
    )
    try:
        env = extension_cli_env(profile_root)
        for name, command in zip(command_names, prepared, strict=True):
            result = execute(
                list(command),
                cwd=cwd,
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                check=False,
                timeout=timeout_seconds,
            )
            validate_extension_command_result(name, result)
            executions.append(
                ExtensionCommandExecution(
                    name=name,
                    command=command,
                    output=result.stdout or "",
                )
            )
    finally:
        shutil.rmtree(profile_root, ignore_errors=True)
        if profile_root.exists():
            print(
                f"[extension-cli:WARN] temporary profile cleanup incomplete: {profile_root}",
                file=sys.stderr,
            )

    return tuple(executions)


def powershell_quote(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def format_shell_command(command: list[str], *, platform_name: str | None = None) -> str:
    platform = os.name if platform_name is None else platform_name
    if platform == "nt":
        return "& " + " ".join(powershell_quote(str(part)) for part in command)
    return shlex.join(str(part) for part in command)


def find_blender_path() -> Path:
    scripts_dir = Path(__file__).resolve().parent
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    from find_blender import find_blender

    blender, _version = find_blender()
    return blender


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Achievements Blender extension.")
    parser.add_argument("--source-dir", type=Path, default=DEFAULT_SOURCE_DIR)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--blender", type=Path, default=None)
    parser.add_argument(
        "--revision",
        default=None,
        help="Package exact committed Git blobs and reject dirty or untracked runtime files.",
    )
    parser.add_argument("--server-generate", action="store_true")
    parser.add_argument(
        "--run-blender",
        action="store_true",
        help=(
            "Execute validate/build/server-generate in an isolated temporary Blender "
            "profile and fail closed on unexpected output."
        ),
    )
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()

    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    blender = args.blender.resolve() if args.blender else find_blender_path()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = prepare_release_source(
        ROOT,
        source_dir,
        clean=not args.no_clean,
        revision=args.revision,
    )
    commands = [
        extension_validate_command(blender, source_dir),
        extension_build_command(blender, source_dir, output_dir),
    ]
    if args.server_generate:
        commands.append(extension_server_generate_command(blender, output_dir))

    mode = f"Git revision {args.revision}" if args.revision else "working tree"
    print(f"Prepared {len(payload)} release files from {mode} in {source_dir}")
    for command in commands:
        print(format_shell_command(command))
    if not args.run_blender:
        print(
            "Commands were not executed. Re-run with --run-blender for isolated "
            "HOME/USERPROFILE/BLENDER_USER_RESOURCES validation."
        )
        return 0

    try:
        if args.server_generate:
            validate_fresh_server_output(output_dir, source_dir)
        executions = run_extension_commands(commands)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as exc:
        print(f"[extension-cli:FAIL] {exc}", file=sys.stderr)
        return 1
    for execution in executions:
        print(execution.output, end="" if execution.output.endswith("\n") else "\n")
        print(f"[extension-cli:PASS] {execution.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
