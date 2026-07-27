# Verification

Fast gate:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run python scripts/verify_predicates.py`
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
- Fixed blocking targets download Blender 5.0.1, 5.1.2, and 5.2.0 from official Blender release paths.
- Every target runs `register`, `lifecycle_stress`, `persistence`, `engine`, `rewards`, and `ui_visual`; no target is skipped or non-blocking.
- Blender smoke jobs set `BLENDER_BIN`; the smoke runner still creates temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES` for each suite.

Release packaging gate:
- For each supported Blender version, use a fresh per-run repository directory:
  `uv run python scripts/build_extension.py --revision HEAD --source-dir reports/extension-validation/<run-id>/<version>/source --output-dir reports/extension-validation/<run-id>/<version> --server-generate --run-blender --blender "<path-to-that-blender>"`.
  Replace `<run-id>` on every rerun so the output is fresh and never-used.
- The isolated wrapper executes `extension validate`, `extension build`, and
  optional `extension server-generate` with `--factory-startup` and temporary
  `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`. Require all requested
  `[extension-cli:PASS]` markers and no traceback/error/warning output.
- `[extension-cli:WARN]` is nonfatal helper cleanup telemetry but invalidates
  release acceptance even when the helper exits zero. Resolve the residue and
  rerun with a new `<run-id>`.
- `server-generate` requires a fresh per-run output containing only its direct
  staged `source/` before execution. The helper rejects stale ZIP/index entries
  and never deletes an older baseline implicitly.
- `reports/extension/` is unsuitable for a server gate while older canonical ZIPs
  are present. After all version-specific build gates pass, select one exact
  verified `achievements-0.2.2.zip`, freeze its SHA-256/member digests, and
  deliberately byte-copy it from a fresh output to
  `reports/extension/achievements-0.2.2.zip`. The destination must not already
  exist; confirm identical source/destination SHA-256. Never rebuild or
  overwrite the canonical ZIP, implicitly clean the canonical directory, or
  replace the immutable 0.2.1 or 0.2.0 predecessors.
- Per-version self-built ZIPs are build evidence only. Run install/enable and
  register/unregister smoke on Blender 5.0.1, 5.1.2, and 5.2.0 against the same
  exact frozen canonical SHA.
- Inspect `reports/extension/achievements-0.2.2.zip`: only manifest, `LICENSE`, root runtime, and `achievements/` are allowed. Confirm Git-byte equality, no symlink/traversal/duplicate entries, member digests, final SHA-256, and size.

Static verifier rules:
- Parse add-on source with `ast`; do not import `bpy`.
- Validate 105 achievements and 9 lessons.
- Validate unique achievement, lesson, and complex IDs.
- Validate category, stat key, difficulty, reward, and lesson references.
- Validate strict catalog `(complex_id, step_check)` to predicate-registry bijection.
- Require `achievements_v01 (4).py` to be absent and preserve its recovery evidence in ADR 0002.
- Validate version `0.2.2`, Blender minimum `(5, 0, 0)`, and 105-achievement active text.
- Validate package-relative root-to-support-module imports and reject shipped runtime imports through a top-level `achievements` alias.
- Reject shipped runtime access to or mutation of `sys.path`.
- Require `[permissions].files = "Store progress and load local reward assets"` in `blender_manifest.toml` and reject a manifest `network` permission.
- Validate local integrity helpers and legacy-only missing-hash backfill without changing `SCHEMA_VERSION`.
- Validate that real user progress files are not tracked.
- Validate that sync helpers are present as tracked infra and covered by normal unit tests.

Blender smoke rules:
- Always run with temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Use background mode and factory startup.
- Verify register/unregister lifecycle and cleanup.
- Verify repeated register/unregister stress cleanup and hot-reload idempotency.
- Verify persistence schema, current `schema_version`, atomic save, legacy hash migration, current-schema missing/forged hash denial, and corrupt JSON quarantine/recovery under a temporary profile.
- Verify factory defaults do not unlock `subsurface_skin` or `denoiser_render`, only exact active Subsurface Weight matches, and denoiser unlock requires the supplied completed Cycles-render scene.
- Verify engine complex checks do not emit `[Achievements] complex step check error` markers for compositor and render-pass checks.
- Verify material, mesh, and geo node reward fallbacks plus reward claim persistence under a temporary profile.
- Verify UI visual contract geometry, tab state, popup/card contract artifact generation, notification stacking, and pinned-overlay no-overlap under a temporary profile.
- For a release candidate, run extension validate/build/server-generate plus ZIP install/enable, namespace-correct import, native extension-management routing, register/unregister, and external Blender-owned removal on Blender 5.0.1, 5.1.2, and 5.2.0. Removal must preserve a sentinel `~/BlenderAchievements/` tree in the disposable profile.

Sync stub rules:
- Normal sync tests run in `uv run pytest`; no Blender smoke is required while sync remains unwired to runtime.
- `achievements/sync.py` must stay free of `bpy`, user-home path assumptions, and production network imports.
- Disabled backends must expose no transport hook and must not make network calls.
- Pinned UI state stays local-only unless a later explicit task changes that behavior.
