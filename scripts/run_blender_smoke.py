from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from find_blender import find_blender

ROOT = Path(__file__).resolve().parents[1]
SUITES = {
    "engine": ROOT / "tests" / "blender" / "smoke_engine.py",
    "lifecycle_stress": ROOT / "tests" / "blender" / "smoke_lifecycle_stress.py",
    "persistence": ROOT / "tests" / "blender" / "smoke_persistence.py",
    "register": ROOT / "tests" / "blender" / "smoke_register.py",
    "rewards": ROOT / "tests" / "blender" / "smoke_rewards.py",
    "ui_visual": ROOT / "tests" / "blender" / "smoke_ui_visual.py",
}
FAILURE_MARKERS = ("Traceback (most recent call last):", ":FAIL]")


def build_command(blender: Path, suite: str) -> list[str]:
    script = SUITES[suite]
    return [str(blender), "--background", "--factory-startup", "--python", str(script)]


def smoke_env(temp_home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(temp_home)
    env["USERPROFILE"] = str(temp_home)
    env["BLENDER_USER_RESOURCES"] = str(temp_home / "blender-user-resources")
    env["ACHIEVEMENTS_ADDON_ROOT"] = str(ROOT)
    env["ACHIEVEMENTS_VISUAL_QA_DIR"] = str(Path(tempfile.gettempdir()) / "achievements-ui-visual-qa")
    return env


def smoke_result_code(suite: str, process_code: int, output: str) -> int:
    expected_pass = f"[smoke_{suite}:PASS]"
    if process_code != 0:
        return process_code
    if expected_pass not in output or any(marker in output for marker in FAILURE_MARKERS):
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Blender background smoke suites.")
    parser.add_argument("--suite", choices=sorted(SUITES), required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    blender, version = find_blender()
    command = build_command(blender, args.suite)

    if args.dry_run:
        preview_home = ROOT / ".tmp-blender-smoke-home"
        env = smoke_env(preview_home)
        print(version)
        print(" ".join(command))
        print(f"HOME={env['HOME']}")
        print(f"USERPROFILE={env['USERPROFILE']}")
        print(f"BLENDER_USER_RESOURCES={env['BLENDER_USER_RESOURCES']}")
        print(f"ACHIEVEMENTS_VISUAL_QA_DIR={env['ACHIEVEMENTS_VISUAL_QA_DIR']}")
        return 0

    temp_home = Path(tempfile.mkdtemp(prefix="achievements-blender-smoke-"))
    try:
        result = subprocess.run(
            command,
            cwd=ROOT,
            env=smoke_env(temp_home),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
            timeout=120,
        )
    finally:
        shutil.rmtree(temp_home, ignore_errors=True)
    print(result.stdout)
    return_code = smoke_result_code(args.suite, result.returncode, result.stdout)
    if return_code != 0:
        print(
            f"[smoke-runner:FAIL] suite {args.suite} did not produce a clean "
            f"[smoke_{args.suite}:PASS] marker"
        )
    if temp_home.exists():
        print(f"[smoke-runner:WARN] temporary profile cleanup incomplete: {temp_home}")
    return return_code


if __name__ == "__main__":
    sys.exit(main())
