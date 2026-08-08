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
- Exercise installed extension imports through Blender's dynamic `bl_ext.<repository>.achievements` namespace; do not repair import failures by mutating runtime `sys.path`.
- Confirm the installed manifest requests `files = "Store progress and load local reward assets"` and no `network` permission.
