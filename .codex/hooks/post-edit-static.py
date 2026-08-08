from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMMANDS = [
    [sys.executable, "scripts/verify_frozen.py"],
    [sys.executable, "scripts/verify_codex_plugin.py"],
]


def main() -> int:
    outputs: list[str] = []
    failed: list[str] = []
    for command in COMMANDS:
        result = subprocess.run(
            command,
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        outputs.append(result.stdout)
        if result.returncode != 0:
            failed.append(" ".join(command[1:]))
    if failed:
        # Blocking convention shared by both harnesses: diagnostics on stderr
        # plus exit 2. Claude Code feeds a hook's stderr back to the model only
        # on exit 2 - stdout with exit 1 is invisible to it - and the Codex
        # hooks block the same way.
        for output in outputs:
            sys.stderr.write(output)
        sys.stderr.write(f"post-edit-static: FAIL - {', '.join(failed)}\n")
        sys.stderr.write("Fix the regression or revert the edit before continuing.\n")
        return 2
    for output in outputs:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
