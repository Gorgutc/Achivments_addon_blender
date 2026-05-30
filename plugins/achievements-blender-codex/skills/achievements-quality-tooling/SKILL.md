---
name: achievements-quality-tooling
description: Maintain verifier scripts, pytest, ruff, and Blender smoke command design.
---

# Achievements Quality Tooling

Use for changes under `scripts/`, `tests/`, `pyproject.toml`, and hook files.

Expectations:
- Static verifier must not import `bpy`.
- Codex verifier must validate plugin, skills, agents, docs, hooks, and stale instruction terms.
- Blender smoke wrapper must isolate user directories.
- Normal pytest should stay fast and avoid requiring Blender except dry-run checks.
