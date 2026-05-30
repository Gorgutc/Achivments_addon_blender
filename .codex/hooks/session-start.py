from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    print("Achievements Blender add-on context")
    print(f"root={ROOT}")
    print("canonical_addon=__init__.py")
    print("target_runtime=Blender 5.0+")
    print("fast_checks=uv run python scripts/verify_frozen.py; uv run python scripts/verify_codex_plugin.py")
    print("deep_check=uv run python scripts/run_blender_smoke.py --suite register")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
