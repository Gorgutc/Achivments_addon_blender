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
- Active identity and candidate paths use 0.2.3. The historical 0.2.2 ZIP is immutable pre-PR16 evidence, never a current install/build artifact. Stage A full validation outputs are ephemeral and authorize no retention, canonical artifact, or publication. Stage B needs separate explicit owner candidate-retention acceptance for one exact audited local candidate SHA, still non-canonical and not publication. Stage C needs separate explicit owner publication acceptance for `v0.2.3` and GitHub Release from that exact retained candidate; this session grants none.
- Loader guidance requires package-relative imports and forbids shipped runtime `sys.path` mutation.
- Manifest guidance uses `files = "Store progress and load local reward assets"` and does not claim `network` permission.
