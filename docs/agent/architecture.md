# Current Architecture

`Achievements` is currently a single-file Blender add-on with a byte-identical tracked duplicate.

Frozen source facts:
- Canonical source: `__init__.py`.
- Duplicate source: `achievements_v01 (4).py`.
- Achievement catalog: 105 achievements.
- Lesson catalog: 9 lessons.
- Progress storage: JSON files under `~/BlenderAchievements/`.
- Runtime surfaces: Blender handlers, timers, Scene properties, GPU draw UI, and reward loading from `.blend` assets.
- Full frozen application contract: `docs/agent/frozen-application-contract.md`.

The preparation layer must document these facts and avoid changing add-on behavior. Future add-on work should first decide whether to remove the duplicate file, align `bl_info` with Blender 5.0+, and update stale 100-achievement text.
