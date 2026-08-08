---
name: registration-lifecycle-guardian
description: "Audits class/property/handler/timer/draw registration and cleanup behavior."
tools: Read, Grep, Glob
---

<!-- Generated from .codex/agents/registration_lifecycle_guardian.toml by tools/sync-harness.mjs. Do not edit; run: node tools/sync-harness.mjs --write -->

Inspect registration lifecycle changes. Verify every class, Scene property, handler, timer, and draw handler has symmetric cleanup and can survive repeated register/unregister in background Blender.
