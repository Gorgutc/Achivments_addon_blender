---
name: achievements-frozen-decisions
description: Check the active frozen contract before making edits.
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
- Blender minimum remains 5.0; ADR 0008 supersedes only the active source identity.
- Root-to-support-module imports remain package-relative inside Blender's installed extension namespace; shipped runtime code does not mutate `sys.path` or depend on a top-level `achievements` alias.
- The manifest requests only `files = "Store progress and load local reward assets"`; production networking remains disabled and no `network` permission is declared.
- The immutable 0.2.1 and 0.2.0 ZIPs remain historical evidence and are never overwritten or relabeled.

Frozen by the owner-approved 2026-07-28 correctness decisions:
- ADR 0005 freezes a non-refreshing 120-second monotonic activity window opened only by real Blender activity sources. Timer, persistence, register/load, popup/draw, and flush remain passive; runtime anchors stay out of JSON, schema `1.0.0` stays unchanged, and `daily_sessions` remains a separate open-day tracker.
- ADR 0006 freezes XP awards `5/10/20`, bands `20/40/80/120/140/170/200/230/260/290`, starts `0/20/60/140/260/400/570/770/1000/1260`, cap `1550`, level-10 progress through `1549`, `MAX` only at `105/105`, derived/no-migration XP, and pure `achievements/levels.py` behind root aliases.

Frozen by the 2026-07-29 reward-correctness decision:
- ADR 0007 freezes confirmed Blender action before a prospective claim, atomic JSON write before runtime claim mutation, and idempotent marked-witness recovery after save failure.
- Failed/no-op application stays claim-free and rolls back new Blender ID deltas and partial slot/modifier state. Geo-node application preserves Blender-supported non-mesh targets and requires a real `NODES` modifier with the assigned GeometryNodeTree.
- Already-persisted rewards retain explicit reapply. Schema `1.0.0`, catalog/assets, and files-only permissions stay unchanged; recovery markers are not authentication.

Frozen by the owner-approved 2026-07-30 release-identity decision:
- ADR 0008 sets `0.2.3` as an unpublished source candidate. Stage A full validation outputs are ephemeral and authorize no retention, canonical artifact, or publication. Stage B needs separate explicit owner candidate-retention acceptance for one exact audited local candidate SHA, still non-canonical and not publication. Stage C needs separate explicit owner publication acceptance for `v0.2.3` and GitHub Release from that exact retained candidate; this session grants none.
- The historical `achievements-0.2.2.zip` is immutable pre-PR16 evidence, never a current install/build artifact. Catalog, behavior, schema, persistence, assets, progress, package allowlist, files-only permission, and disabled networking remain unchanged.

Before future add-on behavior edits, read `docs/agent/frozen-application-contract.md` and identify the exact frozen surface affected.

If a task conflicts with these decisions, notify the user before proceeding.
