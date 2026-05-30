---
name: achievements-blender-runtime
description: Work safely with Blender runtime, background mode, and temporary user directories.
---

# Achievements Blender Runtime

Use for Blender execution or smoke testing.

Rules:
- Locate Blender with `scripts/find_blender.py`.
- Use `--background --factory-startup`.
- Set temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Keep runtime smoke scripts in `tests/blender/`.
- Do not rely on normal Python to import `bpy`.
