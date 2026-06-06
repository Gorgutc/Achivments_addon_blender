# Verification

Fast gate:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run ruff check .`
- `uv run pytest`

Blender discovery:
- `uv run python scripts/find_blender.py`

Deep Blender gate:
- `uv run python scripts/run_blender_smoke.py --suite register`
- `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress`
- `uv run python scripts/run_blender_smoke.py --suite persistence`
- `uv run python scripts/run_blender_smoke.py --suite rewards`

Static verifier rules:
- Parse add-on source with `ast`; do not import `bpy`.
- Validate 105 achievements and 9 lessons.
- Validate unique achievement, lesson, and complex IDs.
- Validate category, stat key, difficulty, reward, and lesson references.
- Validate complex ID coverage in `_check_complex_step`.
- Validate duplicate file hash while the duplicate remains tracked.
- Validate that real user progress files are not tracked.

Blender smoke rules:
- Always run with temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Use background mode and factory startup.
- Verify register/unregister lifecycle and cleanup.
- Verify repeated register/unregister stress cleanup and hot-reload idempotency.
- Verify persistence schema, current `schema_version`, atomic save, hash migration, and corrupt JSON quarantine/recovery under a temporary profile.
- Verify material, mesh, and geo node reward fallbacks under a temporary profile.
