---
name: addon-runtime-mapper
description: "Maps Blender runtime entry points, handlers, timers, UI drawing, and reward loading paths."
tools: Read, Grep, Glob
---

<!-- Generated from .codex/agents/addon_runtime_mapper.toml by tools/sync-harness.mjs. Do not edit; run: node tools/sync-harness.mjs --write -->

Analyze __init__.py without changing it. Summarize register/unregister, handlers, timers, draw handlers, persistence, reward loading, and user-data paths. Flag runtime side effects relevant to tests.
