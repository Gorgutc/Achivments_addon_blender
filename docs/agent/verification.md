# Verification

Fast gate:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run ruff check .`
- `uv run pytest`

GitHub Actions fast gate:
- `.github/workflows/fast-gate.yml` mirrors the fast gate on Python 3.13.
- The workflow runs on pull requests, pushes to `main`, and manual `workflow_dispatch`.
- The workflow is blocking for PR readiness.

Blender discovery:
- `uv run python scripts/find_blender.py`

Deep Blender gate:
- `uv run python scripts/run_blender_smoke.py --suite register`
- `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress`
- `uv run python scripts/run_blender_smoke.py --suite persistence`
- `uv run python scripts/run_blender_smoke.py --suite engine`
- `uv run python scripts/run_blender_smoke.py --suite rewards`
- `uv run python scripts/run_blender_smoke.py --suite ui_visual`

GitHub Actions Blender smoke:
- `.github/workflows/blender-smoke.yml` runs on pull requests, pushes to `main`, and manual `workflow_dispatch`.
- `blender-5-1-stable` downloads Blender 5.1.2 from the official Blender 5.1 release path and is blocking.
- `blender-5-2-alpha-canary` reads the download URL from repository variable `BLENDER_5_2_ALPHA_URL` and is non-blocking through `continue-on-error`.
- Both matrix targets run the same smoke suites: `register`, `lifecycle_stress`, `persistence`, `engine`, `rewards`, and `ui_visual`.
- Blender smoke jobs set `BLENDER_BIN`; the smoke runner still creates temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES` for each suite.

Static verifier rules:
- Parse add-on source with `ast`; do not import `bpy`.
- Validate 105 achievements and 9 lessons.
- Validate unique achievement, lesson, and complex IDs.
- Validate category, stat key, difficulty, reward, and lesson references.
- Validate complex ID coverage in `_check_complex_step`.
- Validate duplicate file hash while the duplicate remains tracked.
- Validate that real user progress files are not tracked.
- Validate that sync helpers are present as tracked infra and covered by normal unit tests.

Blender smoke rules:
- Always run with temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Use background mode and factory startup.
- Verify register/unregister lifecycle and cleanup.
- Verify repeated register/unregister stress cleanup and hot-reload idempotency.
- Verify persistence schema, current `schema_version`, atomic save, hash migration, and corrupt JSON quarantine/recovery under a temporary profile.
- Verify engine complex checks do not emit `[Achievements] complex step check error` markers for compositor and render-pass checks.
- Verify material, mesh, and geo node reward fallbacks plus reward claim persistence under a temporary profile.
- Verify UI visual contract geometry, tab state, popup/card contract artifact generation, notification stacking, and pinned-overlay no-overlap under a temporary profile.

Sync stub rules:
- Normal sync tests run in `uv run pytest`; no Blender smoke is required while sync remains unwired to runtime.
- `achievements/sync.py` must stay free of `bpy`, user-home path assumptions, and production network imports.
- Disabled backends must expose no transport hook and must not make network calls.
- Pinned UI state stays local-only unless a later explicit task changes that behavior.
