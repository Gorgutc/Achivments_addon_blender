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
- Complex-predicate coverage must be a strict catalog-pair to registry bijection,
  not a source-text search.
- Pure predicate and integrity modules must import without `bpy`.
- Static checks must require package-relative root-to-support-module imports,
  reject shipped runtime `sys.path` access or mutation, require manifest
  `files = "Store progress and load local reward assets"`, and reject manifest
  `network` permission.
- Root runtime lint may use only narrow bootstrap exceptions; new modules receive
  the full configured Ruff rules and legacy duplicates must not be excluded.
- CI Blender smoke is blocking for 5.0.1, 5.1.2, and 5.2.0 with no skipped rows,
  repository URL variables, or `continue-on-error` targets.
- Release packaging tests cover Git-blob parity, LF/CRLF behavior, dirty and
  untracked payload rejection, allowlists, and repeated deterministic digests.
