# Current Architecture

`Achievements` is a Blender add-on with one root runtime entrypoint and pure catalog, engine, event, integrity, lifecycle, persistence, predicate, rewards, UI, and sync helpers.

Frozen source facts:
- Canonical runtime entrypoint: `__init__.py`.
- Catalog source of truth: `achievements/catalog.py`.
- Rule/progress evaluation helper source: `achievements/engine.py`.
- XP/level calculation and formatting source: `achievements/levels.py`; root names remain compatibility aliases.
- Activity/session helper source: `achievements/events.py`.
- Registration lifecycle helper source: `achievements/lifecycle.py`.
- JSON persistence helper source: `achievements/persistence.py`.
- Unlock-integrity helper source: `achievements/integrity.py`.
- Complex predicate source: `achievements/predicates/`; root `_check_complex_step` is the Blender adapter.
- Reward planning helper source: `achievements/rewards.py`.
- UI contract and layout planning helper source: `achievements/ui.py`.
- Offline sync planning helper source: `achievements/sync.py`.
- Installed extension namespace: Blender loads the root as `bl_ext.<repository>.achievements`; root-to-support-module imports are package-relative and the runtime never mutates `sys.path`.
- Manifest permissions: `blender_manifest.toml` declares only `files = "Store progress and load local reward assets"`; it does not request network access.
- Legacy duplicate `achievements_v01 (4).py` was retired by ADR 0002; static verification requires one canonical runtime.
- Achievement catalog: 105 achievements in `achievements/catalog.py`.
- Lesson catalog: 9 lessons in `achievements/catalog.py`.
- Progress storage: current-schema JSON files under `~/BlenderAchievements/`.
- Runtime surfaces: Blender handlers, timers, UI-planned Scene properties, GPU draw UI, lifecycle helper wiring, engine-backed stat/complex orchestration, activity/session tracking, reward planning, and reward loading from `.blend` assets.
- Cloud/sync surface: currently a pure offline stub only. `achievements/sync.py` defines queue, disabled backend, payload filtering, and deterministic conflict decisions; production networking is not wired into normal add-on use.
- Full frozen application contract: `docs/agent/frozen-application-contract.md`.

The 0.2.0 technical closeout aligns `bl_info` with Blender 5.0+, removes stale 100-achievement runtime strings, and preserves catalog IDs, persistence schema, Blender public surfaces, UI layout, and reward fallbacks. Real content assets, tutorial URLs, production cloud, and remaining UI/GPU decomposition are separate epics.

The 0.2.1 maintenance slice adds crash-safe navigation to Blender-owned extension removal, keeps user progress outside the extension lifecycle, corrects Subsurface Weight detection, and makes denoiser completion an explicit render event. Persistence schema and all 105 catalog IDs remain unchanged.

The 0.2.2 policy closeout keeps support imports inside Blender's installed extension namespace, removes the runtime `sys.path` alias, and declares the narrow file permission needed for local progress and reward assets. ADR 0004 records these loader and manifest boundaries. It does not change catalog, persistence, predicates, UI, reward fallbacks, or the disabled production-networking state.

The 2026-07-28 active-time correctness slice uses the ADR 0005 non-refreshing 120-second activity window. Existing real Blender events open or extend a union of monotonic runtime-only windows; timer/`save_data` flushes credit each whole second once without becoming activity. Blender `save_pre` remains a real event. Register/load/reset and rollback clear the runtime anchors. Persistence remains schema `1.0.0` and preserves historical progress forward-only. `daily_sessions` remains the separate open-day tracker, and speed-model/calendar logic stays on wall clock.

The owner-approved ADR 0006 balance slice keeps difficulty awards at `5/10/20` and replaces the unreachable exponential scale with exact bands `20/40/80/120/140/170/200/230/260/290`. Their starts are `0/20/60/140/260/400/570/770/1000/1260`, the final cap equals the catalog maximum `1550 XP`, level 10 remains in progress through `1549`, and only `105/105` displays `MAX`. XP remains derived from unlocked catalog IDs, so persistence schema `1.0.0` and existing payloads do not migrate. Across every reachable XP total, the new level never decreases and rises by at most three.

The ADR 0007 reward-correctness slice separates Blender action proof from claim persistence. Asset actions must satisfy a type-specific postcondition before `save_data` builds a prospective claim payload; the atomic JSON write precedes runtime mutation. Marked Material/Object/GeometryNodeTree witnesses make a failed write retry idempotent, while failed/no-op applications roll back new Blender ID deltas, material slots and active indices, and partial modifier state. Persisted rewards retain explicit reapply behavior. Schema `1.0.0`, version `0.2.2`, catalog, asset paths, files-only permissions, and disabled production networking remain unchanged.
