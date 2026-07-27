---
name: achievements-instruction-drift
description: Audit active instructions for stale stack assumptions and contradictions.
---

# Achievements Instruction Drift

Use when editing instructions, docs, hooks, skills, or agents.

Check:
- Active docs describe Blender/Python, not unrelated stacks.
- Command names match scripts.
- Hooks remain fast.
- `/review` remains required before delivery.
- Explicit subagent usage remains required where available.
- Active identity and candidate paths use 0.2.2; 0.2.1 appears only in preserved historical maintenance or immutable-artifact context.
- Loader guidance requires package-relative imports and forbids shipped runtime `sys.path` mutation.
- Manifest guidance uses `files = "Store progress and load local reward assets"` and does not claim `network` permission.
