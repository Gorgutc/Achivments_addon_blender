from __future__ import annotations

import argparse
import os
import shlex
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS_DIR = ROOT / "reports"
DEFAULT_OUTPUT_DIR = ROOT / "reports" / "extension"
DEFAULT_SOURCE_DIR = DEFAULT_OUTPUT_DIR / "source"
RUNTIME_FILES = (
    Path("blender_manifest.toml"),
    Path("__init__.py"),
)
RUNTIME_DIRS = (Path("achievements"),)
EXCLUDED_DIR_NAMES = {"__pycache__"}
EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


def release_payload_paths(root: Path = ROOT) -> tuple[Path, ...]:
    paths: list[Path] = []
    for relative_path in RUNTIME_FILES:
        source = root / relative_path
        if source.is_file():
            paths.append(relative_path)

    for relative_dir in RUNTIME_DIRS:
        source_dir = root / relative_dir
        if not source_dir.is_dir():
            continue
        for source in sorted(source_dir.rglob("*")):
            if not source.is_file():
                continue
            relative_path = source.relative_to(root)
            if any(part in EXCLUDED_DIR_NAMES for part in relative_path.parts):
                continue
            if relative_path.suffix in EXCLUDED_SUFFIXES:
                continue
            paths.append(relative_path)
    return tuple(paths)


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def ensure_generated_subdir(path: Path, *, generated_root: Path = REPORTS_DIR) -> Path:
    resolved_path = path.resolve()
    resolved_root = generated_root.resolve()
    if resolved_path == resolved_root or not is_relative_to(resolved_path, resolved_root):
        raise ValueError(
            f"Release source directory must be under generated reports root "
            f"{resolved_root}: {resolved_path}"
        )
    return resolved_path


def prepare_release_source(
    root: Path = ROOT,
    source_dir: Path = DEFAULT_SOURCE_DIR,
    *,
    clean: bool = True,
    generated_root: Path = REPORTS_DIR,
) -> tuple[Path, ...]:
    payload = release_payload_paths(root)
    source_dir = ensure_generated_subdir(source_dir, generated_root=generated_root)
    if clean and source_dir.exists():
        shutil.rmtree(source_dir)
    source_dir.mkdir(parents=True, exist_ok=True)

    for relative_path in payload:
        source = root / relative_path
        target = source_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return payload


def blender_cli_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def extension_validate_command(blender: Path, source_dir: Path) -> list[str]:
    return [
        str(blender),
        "--background",
        "--command",
        "extension",
        "validate",
        blender_cli_path(source_dir),
    ]


def extension_build_command(blender: Path, source_dir: Path, output_dir: Path) -> list[str]:
    return [
        str(blender),
        "--background",
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
        "--command",
        "extension",
        "server-generate",
        "--repo-dir",
        blender_cli_path(output_dir),
        "--html",
    ]


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
    parser.add_argument("--server-generate", action="store_true")
    parser.add_argument("--no-clean", action="store_true")
    args = parser.parse_args()

    source_dir = args.source_dir.resolve()
    output_dir = args.output_dir.resolve()
    blender = args.blender.resolve() if args.blender else find_blender_path()
    output_dir.mkdir(parents=True, exist_ok=True)

    payload = prepare_release_source(ROOT, source_dir, clean=not args.no_clean)
    commands = [
        extension_validate_command(blender, source_dir),
        extension_build_command(blender, source_dir, output_dir),
    ]
    if args.server_generate:
        commands.append(extension_server_generate_command(blender, output_dir))

    print(f"Prepared {len(payload)} release files in {source_dir}")
    for command in commands:
        print(format_shell_command(command))
    return 0


if __name__ == "__main__":
    sys.exit(main())
