from __future__ import annotations

import argparse
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

MIN_VERSION = (5, 0, 0)
WINDOWS_CANDIDATES = [
    Path(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 5.0\blender.exe"),
    Path(r"C:\Program Files\Blender Foundation\Blender 4.5\blender.exe"),
]


def candidate_paths() -> list[Path]:
    paths: list[Path] = []
    env_path = os.environ.get("BLENDER_BIN")
    if env_path:
        paths.append(Path(env_path))
    path_candidate = shutil.which("blender")
    if path_candidate:
        paths.append(Path(path_candidate))
    if os.name == "nt":
        paths.extend(WINDOWS_CANDIDATES)
    return paths


def version_line(path: Path) -> str:
    result = subprocess.run(
        [str(path), "--version"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        timeout=20,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout.strip() or f"{path} returned {result.returncode}")
    return result.stdout.splitlines()[0].strip()


def parse_blender_version(version: str) -> tuple[int, int, int]:
    match = re.match(r"Blender\s+(\d+)\.(\d+)(?:\.(\d+))?", version)
    if match is None:
        raise ValueError(f"Cannot parse Blender version from: {version}")
    major, minor, patch = match.groups(default="0")
    return int(major), int(minor), int(patch)


def find_blender() -> tuple[Path, str]:
    errors: list[str] = []
    for path in candidate_paths():
        try:
            resolved = path.expanduser().resolve()
        except OSError:
            resolved = path.expanduser()
        if not resolved.is_file():
            continue
        try:
            version = version_line(resolved)
            if parse_blender_version(version) < MIN_VERSION:
                errors.append(f"{resolved}: {version} is below Blender 5.0")
                continue
            return resolved, version
        except Exception as exc:  # noqa: BLE001 - report all candidate failures.
            errors.append(f"{resolved}: {exc}")
    details = "\n".join(errors) if errors else "No candidate executable found."
    raise SystemExit(f"Blender executable not found.\n{details}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Find a usable Blender executable.")
    parser.add_argument("--path-only", action="store_true", help="Print only the executable path.")
    args = parser.parse_args()

    path, version = find_blender()
    if args.path_only:
        print(path)
    else:
        print(f"{version} - {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
