---
name: achievements-frozen-decisions
description: Check the active 0.2.2 frozen contract before making edits.
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

Frozen by the approved 0.2.1 maintenance slice:
- Progress reset and extension removal remain separate; removal preserves user data and is completed in Blender's native `Extensions` UI.
- Add-on-owned operators never invoke self-uninstall.
- Subsurface requires exact active Weight, and denoiser requires a completed Cycles-render event.

Frozen by the approved 0.2.2 policy closeout:
- Current identity is 0.2.2 with Blender minimum 5.0.
- Root-to-support-module imports remain package-relative inside Blender's installed extension namespace; shipped runtime code does not mutate `sys.path` or depend on a top-level `achievements` alias.
- The manifest requests only `files = "Store progress and load local reward assets"`; production networking remains disabled and no `network` permission is declared.
- The immutable 0.2.1 and 0.2.0 ZIPs remain historical evidence and are never overwritten or relabeled.

Before future add-on behavior edits, read `docs/agent/frozen-application-contract.md` and identify the exact frozen surface affected.

If a task conflicts with these decisions, notify the user before proceeding.
