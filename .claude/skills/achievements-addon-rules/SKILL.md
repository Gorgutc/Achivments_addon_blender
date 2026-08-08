---
name: achievements-addon-rules
description: Apply Blender add-on rules for Python, bpy, registration, persistence, and rewards.
---

# Achievements Add-on Rules

Use for any work that touches or reasons about add-on behavior.

Rules:
- Treat `__init__.py` as canonical unless the user changes that decision.
- Use Blender 5.0+ as the target policy for new work.
- Keep root-to-support-module imports package-relative inside Blender's `bl_ext.<repository>.achievements` namespace. Do not add the extension directory to `sys.path` or depend on a top-level `achievements` alias in shipped runtime code.
- Keep manifest file access explicit as `files = "Store progress and load local reward assets"`; do not request `network` permission while production networking is disabled.
- Preserve achievement IDs, lesson IDs, reward references, and persistence schema unless the task explicitly changes them.
- Avoid importing `bpy` in normal Python tests.
- Use Blender background smoke for runtime lifecycle checks.
