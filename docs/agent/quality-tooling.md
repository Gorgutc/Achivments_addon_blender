# Quality Tooling

This repository uses small Python tools rather than stack-wide package tooling from sibling repositories.

Authoritative commands:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run python scripts/find_blender.py`
- `uv run python scripts/run_blender_smoke.py --suite register`
- `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress`
- `uv run python scripts/run_blender_smoke.py --suite persistence`
- `uv run python scripts/run_blender_smoke.py --suite engine`
- `uv run python scripts/run_blender_smoke.py --suite rewards`
- `uv run python scripts/run_blender_smoke.py --suite ui_visual`
- `uv run ruff check .`
- `uv run pytest`

GitHub Actions:
- `.github/workflows/fast-gate.yml` mirrors `verify_frozen`, `verify_codex_plugin`, `ruff`, and `pytest` on Python 3.13.
- `.github/workflows/blender-smoke.yml` runs the Blender smoke suites on Python 3.13 with Blender 5.1 stable as the blocking target.
- The Blender 5.2 alpha matrix entry is a canary and stays non-blocking through `continue-on-error`; its URL comes from repository variable `BLENDER_5_2_ALPHA_URL`.

`ruff check .` is configured for infrastructure code. The current add-on source and duplicate are excluded during this preparation phase because this task does not edit add-on code.

Hooks run fast static checks only. Blender smoke is intentionally reserved for manual deep and ship gates plus the dedicated Blender smoke workflow.
