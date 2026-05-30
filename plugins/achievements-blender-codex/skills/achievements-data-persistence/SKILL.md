---
name: achievements-data-persistence
description: Protect progress JSON persistence and user data boundaries.
---

# Achievements Data Persistence

Use for data path, JSON schema, save/load, and test isolation work.

Rules:
- Never write tests against real `~/BlenderAchievements`.
- Preserve current JSON schema unless the task explicitly migrates it.
- Verify temp-home isolation in Blender smoke.
- Do not track generated progress files.
