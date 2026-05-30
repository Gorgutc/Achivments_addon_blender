---
name: achievements-frozen-decisions
description: Check frozen preparation decisions before making edits.
---

# Achievements Frozen Decisions

Use before edits that might touch source truth.

Frozen during preparation:
- No add-on-code edits.
- No user progress edits.
- No duplicate-file cleanup.
- No release packaging changes.
- No web-stack rule import.

Before future add-on behavior edits, read `docs/agent/frozen-application-contract.md` and identify the exact frozen surface affected.

If a task conflicts with these decisions, notify the user before proceeding.
