# Quality Tooling

This repository uses small Python tools rather than stack-wide package tooling from sibling repositories.

Authoritative commands:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run python scripts/verify_predicates.py`
- `uv run python scripts/find_blender.py`
- `uv run python scripts/build_extension.py --revision HEAD --source-dir reports/extension-validation/<run-id>/<version>/source --output-dir reports/extension-validation/<run-id>/<version> --server-generate --run-blender --blender "<path-to-that-blender>"`
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
- `scripts/build_extension.py --revision HEAD --run-blender` prepares a committed
  Git-blob release source and executes Blender `extension validate`, `extension
  build`, and optional `extension server-generate` with `--factory-startup`.
- The wrapper uses one disposable profile with temporary `HOME`, `USERPROFILE`,
  and `BLENDER_USER_RESOURCES`, and fails closed on unexpected output.
- Give every `server-generate` gate a fresh, never-used per-run output directory
  with a new `<run-id>`. The helper rejects stale ZIP/index entries and never
  deletes an older baseline.
- The default `reports/extension/` is not a server-gate workspace while its
  `achievements-0.1.0.zip` baseline is present. Audit a candidate from a fresh
  output first, then select one exact verified `achievements-0.2.0.zip` and
  deliberately byte-copy it to the canonical directory. The destination must
  not already exist; verify identical source/destination SHA-256 and never
  rebuild or overwrite the canonical ZIP.
- Treat per-version self-built ZIPs as build evidence only. Use the same exact
  frozen canonical SHA for install/enable and register/unregister smoke on all
  three supported Blender versions.
- Packaging tests freeze LF/CRLF behavior, dirty/untracked rejection, exact Git bytes, member allowlists, and repeatable member digests.
