---
name: achievements-frozen-decisions
description: Check the active post-0.2.0 frozen contract before making edits.
---

# Achievements Frozen Decisions

Use before edits that might touch source truth.

Frozen after the approved 0.2.0 technical closeout:
- Preparation-only tasks do not edit add-on runtime behavior.
- No user progress edits.
- The retired duplicate stays absent unless the owner explicitly reverses ADR 0002.
- Release packaging uses the committed-Git revision contract and fixed payload allowlist.
- Catalog IDs, Scene properties, operators, handlers, UI layout, persistence keys, and `SCHEMA_VERSION = "1.0.0"` remain stable unless explicitly requested.
- No web-stack rule import.

Before future add-on behavior edits, read `docs/agent/frozen-application-contract.md` and identify the exact frozen surface affected.

If a task conflicts with these decisions, notify the user before proceeding.
