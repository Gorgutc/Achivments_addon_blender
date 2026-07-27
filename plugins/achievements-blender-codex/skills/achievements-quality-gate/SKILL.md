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
- Blender `extension validate`, `extension build`, and
  `extension server-generate` through `build_extension.py --run-blender`, plus
  install/enable and register/unregister smoke on 5.0.1, 5.1.2, and 5.2.0 for a
  release candidate. Require `--factory-startup`, a disposable profile with
  temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`, and a fresh
  never-used per-run output directory with a new `<run-id>` for each server
  gate. Per-version self-built ZIPs are build evidence only; use one exact
  frozen canonical SHA for all three install/enable/register-unregister smokes.
- Verify the 0.2.2 identity, package-relative installed namespace imports,
  absence of shipped runtime `sys.path` mutation, manifest
  `files = "Store progress and load local reward assets"`, and absence of
  manifest `network` permission.

Report any skipped command and why.
