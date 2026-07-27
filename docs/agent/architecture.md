# Current Architecture

`Achievements` is a Blender add-on with one root runtime entrypoint and pure catalog, engine, event, integrity, lifecycle, persistence, predicate, rewards, UI, and sync helpers.

Frozen source facts:
- Canonical runtime entrypoint: `__init__.py`.
- Catalog source of truth: `achievements/catalog.py`.
- Rule/progress evaluation helper source: `achievements/engine.py`.
- Activity/session helper source: `achievements/events.py`.
- Registration lifecycle helper source: `achievements/lifecycle.py`.
- JSON persistence helper source: `achievements/persistence.py`.
- Unlock-integrity helper source: `achievements/integrity.py`.
- Complex predicate source: `achievements/predicates/`; root `_check_complex_step` is the Blender adapter.
- Reward planning helper source: `achievements/rewards.py`.
- UI contract and layout planning helper source: `achievements/ui.py`.
- Offline sync planning helper source: `achievements/sync.py`.
- Legacy duplicate `achievements_v01 (4).py` was retired by ADR 0002; static verification requires one canonical runtime.
- Achievement catalog: 105 achievements in `achievements/catalog.py`.
- Lesson catalog: 9 lessons in `achievements/catalog.py`.
- Progress storage: current-schema JSON files under `~/BlenderAchievements/`.
- Runtime surfaces: Blender handlers, timers, UI-planned Scene properties, GPU draw UI, lifecycle helper wiring, engine-backed stat/complex orchestration, activity/session tracking, reward planning, and reward loading from `.blend` assets.
- Cloud/sync surface: currently a pure offline stub only. `achievements/sync.py` defines queue, disabled backend, payload filtering, and deterministic conflict decisions; production networking is not wired into normal add-on use.
- Full frozen application contract: `docs/agent/frozen-application-contract.md`.

The 0.2.0 technical closeout aligns `bl_info` with Blender 5.0+, removes stale 100-achievement runtime strings, and preserves catalog IDs, persistence schema, Blender public surfaces, UI layout, and reward fallbacks. Real content assets, tutorial URLs, production cloud, and remaining UI/GPU decomposition are separate epics.

The 0.2.1 maintenance slice adds crash-safe navigation to Blender-owned extension removal, keeps user progress outside the extension lifecycle, corrects Subsurface Weight detection, and makes denoiser completion an explicit render event. Persistence schema and all 105 catalog IDs remain unchanged.
