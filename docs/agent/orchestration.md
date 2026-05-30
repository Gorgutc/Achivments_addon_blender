# Agent Orchestration

Use explicit spawned subagents for independent work when the environment exposes them. If no spawn tool is available, record that limitation and use the `/review` fallback from `docs/agent/code-review.md`.

Default split:
- `tech_stack_cartographer`: repository map and stack boundaries.
- `addon_runtime_mapper`: runtime lifecycle and side effects.
- `blender_api_compat_guardian`: Blender 5.0+ compatibility.
- `registration_lifecycle_guardian`: register/unregister safety.
- `data_persistence_guardian`: temp data and JSON schema safety.
- `quality_tooling_architect`: verifier and command design.
- `code_quality_guardian`: Python correctness and tests.
- `code_deadwood_auditor`: duplicates and stale material.
- `instruction_drift_auditor`: active instruction consistency.
- `verification_reviewer`: final evidence review.
- `blender_ui_visual_qa`: optional visual QA when Blender UI evidence exists.

The primary agent owns implementation. Subagents should produce read-only findings unless explicitly assigned scoped edits.
