# Frozen Decisions

Frozen for preparation work:
- Do not edit `__init__.py`.
- Do not edit `achievements_v01 (4).py`.
- Treat 105 achievements and 9 lessons as the current code truth.
- Treat `achievements_v01 (4).py` as a known duplicate drift risk.
- Treat `bl_info["blender"] == (4, 5, 0)` as known drift against the future Blender 5.0+ policy.
- Treat old 100-achievement text as known documentation/code text drift.
- Do not copy Node/npm/pnpm package-manager workflows or web checks from sibling repositories; Python `uv` tooling is allowed here.
- Do not touch real user progress data.

These decisions are not permanent product decisions. They protect this preparation task from accidentally changing add-on behavior.
