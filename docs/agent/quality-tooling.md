# Quality Tooling

This repository uses small Python tools rather than stack-wide package tooling from sibling repositories.

Authoritative commands:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run python scripts/find_blender.py`
- `uv run python scripts/run_blender_smoke.py --suite register`
- `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress`
- `uv run ruff check .`
- `uv run pytest`

`ruff check .` is configured for infrastructure code. The current add-on source and duplicate are excluded during this preparation phase because this task does not edit add-on code.

Hooks run fast static checks only. Blender smoke is intentionally reserved for manual deep and ship gates.
