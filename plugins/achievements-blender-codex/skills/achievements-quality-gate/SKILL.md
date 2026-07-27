---
name: achievements-quality-gate
description: Run the required checks before claiming work is complete.
---

# Achievements Quality Gate

Use before completion claims.

Run relevant commands:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run python scripts/verify_predicates.py`
- `uv run ruff check .`
- `uv run pytest`
- all six `scripts/run_blender_smoke.py` suites for deep or ship gates, using
  temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Blender extension validate/build/server-generate plus install/enable and
  register/unregister smoke on 5.0.1, 5.1.2, and 5.2.0 for a release candidate.

Report any skipped command and why.
