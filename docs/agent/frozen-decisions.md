# Frozen Decisions

Frozen after the user-approved Achievements 0.2.0 technical closeout:
- Root `__init__.py` remains the only canonical Blender runtime entrypoint.
- `achievements_v01 (4).py` is intentionally absent; ADR 0002 preserves exact recovery evidence.
- Treat 105 achievements and 9 lessons as the current code truth.
- Treat `docs/agent/frozen-application-contract.md` as the active frozen map for current rules, design, functions, data surfaces, and future change boundaries.
- Keep `SCHEMA_VERSION == "1.0.0"`; only legacy payloads may backfill missing unlock hashes.
- Do not copy Node/npm/pnpm package-manager workflows or web checks from sibling repositories; Python `uv` tooling is allowed here.
- Do not touch real user progress data.

Frozen after the approved Achievements 0.2.1 maintenance slice:
- Keep progress reset separate from extension removal. Removal routes through Blender's native `Extensions` UI and preserves `~/BlenderAchievements/`; nested self-uninstall is prohibited.
- Treat `subsurface_skin` as exact active Principled Subsurface Weight and `denoiser_render` as a completed Cycles-render event predicate, not passive configuration state.

Frozen after the approved Achievements 0.2.2 policy closeout:
- Require `bl_info["blender"] == (5, 0, 0)` and current add-on version `0.2.2`.
- Keep root-to-support-module imports package-relative inside `bl_ext.<repository>.achievements`; shipped runtime code must not add the extension directory to `sys.path` or depend on a top-level `achievements` alias.
- Require exactly `files = "Store progress and load local reward assets"` under manifest `[permissions]`; do not request `network` permission while production networking remains disabled.
- Preserve the 0.2.1 extension-removal, Subsurface Weight, and completed-render behavior without content, predicate, UI, persistence, reward, or cloud expansion.
- Treat 105-achievement runtime and active documentation text as current truth.

Frozen after the owner-approved 2026-07-28 active-time correctness decision:
- Use the ADR 0005 non-refreshing 120-second monotonic activity window. Only existing real activity sources open or extend it; timer, persistence, register/load, popup/draw, and flush do not.
- Keep activity anchors runtime-only and absent from JSON. Preserve historical `time_spent`, unlocks, hashes, and claimed rewards forward-only under unchanged `SCHEMA_VERSION = "1.0.0"`.
- Keep `daily_sessions` as the existing open-day/session tracker, independent from active-time seconds. Any streak-semantics change is a separate owner decision.
- Keep speed-model and calendar predicates on their existing wall-clock domain.

Frozen after the owner-approved XP reachability decision in ADR 0006:
- Keep difficulty awards `5/10/20`, exact bands `20/40/80/120/140/170/200/230/260/290`, starts `0/20/60/140/260/400/570/770/1000/1260`, and cap `1550`; level 10 progresses through `1549`, and only `105/105` at `1550` displays `MAX`.
- Keep XP derived from unlocked catalog IDs with no persistence migration, preserve the no-downlevel and maximum `+3` promotion bounds, and keep pure progression in `achievements/levels.py` behind root compatibility aliases.

Default future-change rule:
- Change only the named behavior, function, data field, or UI surface requested by the user.
- Preserve unrelated catalog entries, category IDs, stat keys, reward semantics, UI layout, persistence schema, and lifecycle cleanup.
- If a change intentionally violates the frozen application contract, call that out before editing and keep the diff scoped to that explicit request.

These decisions are not permanent product decisions. They protect preparation and future maintenance work from accidentally changing add-on behavior.
