# Repository Agent Instructions

Authority order:
1. System and developer instructions.
2. Task-specific user instructions.
3. This repository `AGENTS.md`.
4. `.codex/config.toml`, `.codex/hooks.json`, and repo-local plugin skills.
5. Historical docs and archived notes.

Scope: this repository contains the `Achievements` Blender add-on. The current implementation is a Python-only Blender add-on, not a web project. Do not import web-stack rules from sibling repositories. Patterns from `Gorgutc/PL_RU` and `Gorgutc/codex` are reused only as Codex orchestration patterns.

Core rules:
- Target runtime policy for future add-on work is Blender 5.0+ and Python through Blender's bundled runtime.
- Do not modify add-on code in preparation-only tasks unless the user explicitly asks for add-on behavior changes.
- Do not edit or delete real user progress under `~/BlenderAchievements` or any generated `achievements_data.json`.
- Use explicit spawned subagents for independent review, audit, and verification tasks when the environment exposes them. If no spawn tool is available, document the fallback review path instead of treating the absence itself as an add-on blocker.
- Run `/review` before final delivery. If no slash command is callable, perform an explicit review fallback covering requirements, diff, checks, blockers, and residual risks.
- Prefer `uv run python ...`, `uv run ruff check .`, and `uv run pytest` for repo tooling.
- Blender smoke checks must use temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Hooks may run fast static checks. They must not run heavy Blender smoke checks after every edit.

Known frozen facts:
- Canonical active add-on file is `__init__.py`.
- `achievements_v01 (4).py` is currently a byte-identical duplicate and is tracked as a drift risk.
- The add-on currently defines 105 achievements, 9 lessons, JSON persistence under `~/BlenderAchievements/`, handlers, timers, GPU draw UI, and reward loading from `.blend` assets.
- Current `bl_info["blender"] == (4, 5, 0)` is known policy drift for later add-on-code work.

Required delivery gate:
1. Run the relevant static verifier commands.
2. Run fast Python checks where the task touches infra or scripts.
3. Run Blender smoke for ship/deep gates when Blender is available.
4. Spawn or reuse review agents where available.
5. Complete `/review` fallback if the slash command itself is unavailable.
