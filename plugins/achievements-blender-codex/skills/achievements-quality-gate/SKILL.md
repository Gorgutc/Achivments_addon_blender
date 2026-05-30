---
name: achievements-quality-gate
description: Run the required checks before claiming work is complete.
---

# Achievements Quality Gate

Use before completion claims.

Run relevant commands:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run ruff check .`
- `uv run pytest`
- `uv run python scripts/run_blender_smoke.py --suite register` for deep or ship gates when Blender is available.

Report any skipped command and why.
