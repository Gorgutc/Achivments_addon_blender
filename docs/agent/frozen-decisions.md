# Frozen Decisions

Frozen after the user-approved Achievements 0.2.0 technical closeout:
- Root `__init__.py` remains the only canonical Blender runtime entrypoint.
- `achievements_v01 (4).py` is intentionally absent; ADR 0002 preserves exact recovery evidence.
- Treat 105 achievements and 9 lessons as the current code truth.
- Treat `docs/agent/frozen-application-contract.md` as the active frozen map for current rules, design, functions, data surfaces, and future change boundaries.
- Require `bl_info["blender"] == (5, 0, 0)` and add-on version `0.2.0`.
- Treat 105-achievement runtime and active documentation text as current truth.
- Keep `SCHEMA_VERSION == "1.0.0"`; only legacy payloads may backfill missing unlock hashes.
- Do not copy Node/npm/pnpm package-manager workflows or web checks from sibling repositories; Python `uv` tooling is allowed here.
- Do not touch real user progress data.

Default future-change rule:
- Change only the named behavior, function, data field, or UI surface requested by the user.
- Preserve unrelated catalog entries, category IDs, stat keys, reward semantics, UI layout, persistence schema, and lifecycle cleanup.
- If a change intentionally violates the frozen application contract, call that out before editing and keep the diff scoped to that explicit request.

These decisions are not permanent product decisions. They protect preparation and future maintenance work from accidentally changing add-on behavior.
