---
name: achievements-context-keeper
description: Preserve current add-on facts and known drift while moving between tasks.
---

# Achievements Context Keeper

Use when summarizing or resuming work.

Keep these facts visible:
- 105 achievements and 9 lessons.
- Root `__init__.py` is the sole runtime; ADR 0002 retired `achievements_v01 (4).py` and preserves exact recovery evidence.
- Progress lives under `~/BlenderAchievements`.
- Blender smoke must use temporary user directories.
- Preparation tasks do not edit add-on code.
