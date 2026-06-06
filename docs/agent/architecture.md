# Current Architecture

`Achievements` is currently a Blender add-on with a root runtime entrypoint, pure catalog/engine/event/lifecycle/persistence/rewards/ui/sync helper modules, and a byte-identical tracked duplicate of the root entrypoint.

Frozen source facts:
- Canonical runtime entrypoint: `__init__.py`.
- Catalog source of truth: `achievements/catalog.py`.
- Rule/progress evaluation helper source: `achievements/engine.py`.
- Activity/session helper source: `achievements/events.py`.
- Registration lifecycle helper source: `achievements/lifecycle.py`.
- JSON persistence helper source: `achievements/persistence.py`.
- Reward planning helper source: `achievements/rewards.py`.
- UI contract and layout planning helper source: `achievements/ui.py`.
- Offline sync planning helper source: `achievements/sync.py`.
- Duplicate source: `achievements_v01 (4).py`.
- Achievement catalog: 105 achievements in `achievements/catalog.py`.
- Lesson catalog: 9 lessons in `achievements/catalog.py`.
- Progress storage: current-schema JSON files under `~/BlenderAchievements/`.
- Runtime surfaces: Blender handlers, timers, UI-planned Scene properties, GPU draw UI, lifecycle helper wiring, engine-backed stat/complex orchestration, activity/session tracking, reward planning, and reward loading from `.blend` assets.
- Cloud/sync surface: currently a pure offline stub only. `achievements/sync.py` defines queue, disabled backend, payload filtering, and deterministic conflict decisions; production networking is not wired into normal add-on use.
- Full frozen application contract: `docs/agent/frozen-application-contract.md`.

The preparation layer must document these facts and avoid changing unrelated add-on behavior. The duplicate is a permanent byte-identical duplicate unless the user explicitly changes that policy in a later task. Future add-on work should align `bl_info` with the Blender 5.0+ floor and update stale 100-achievement runtime strings without changing runtime behavior accidentally.
