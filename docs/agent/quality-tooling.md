# Quality Tooling

This repository uses small Python tools rather than stack-wide package tooling from sibling repositories.

Authoritative commands:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run python scripts/verify_predicates.py`
- `uv run python scripts/find_blender.py`
- `uv run python scripts/build_extension.py --revision HEAD --output-dir reports/extension --server-generate`
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
- `.github/workflows/blender-smoke.yml` runs all six Blender smoke suites on fixed blocking targets Blender 5.0.1, 5.1.2, and 5.2.0.
- The Blender matrix has no repository URL variable, skipped row, canary, or `continue-on-error` target.

`ruff check .` covers the runtime and infrastructure. Root `__init__.py` has only narrow bootstrap exceptions for `E402`/`I001`; pure modules receive the full configured rules. There is no duplicate-source exclusion.

Hooks run fast static checks only. Blender smoke is intentionally reserved for manual deep and ship gates plus the dedicated Blender smoke workflow.

Release packaging:
- `scripts/build_extension.py --revision HEAD` prepares a committed Git-blob release source and prints the Blender extension validate/build/server-generate commands.
- Run `blender --background --command extension validate`, `extension build`, and `extension server-generate` directly from the shell.
- Packaging tests freeze LF/CRLF behavior, dirty/untracked rejection, exact Git bytes, member allowlists, and repeatable member digests.
