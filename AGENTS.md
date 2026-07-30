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
- `achievements_v01 (4).py` was retired in the approved 0.2.0 technical closeout; ADR 0002 preserves its baseline blob, hashes, and recovery procedure. Do not reintroduce a second runtime without an explicit owner decision.
- The add-on currently defines 105 achievements, 9 lessons, JSON persistence under `~/BlenderAchievements/`, handlers, timers, GPU draw UI, and reward loading from `.blend` assets.
- Current source-candidate identity is 0.2.3 and `bl_info["blender"] == (5, 0, 0)`. Stage A full validation outputs are ephemeral and authorize no retention, canonical artifact, or publication. Stage B needs separate explicit owner candidate-retention acceptance for one exact audited local candidate SHA, still non-canonical and not publication. Stage C needs separate explicit owner publication acceptance for `v0.2.3` and GitHub Release from that exact retained candidate; this session grants none.
- Shipped runtime imports stay inside the Blender extension namespace; do not add the extension directory to `sys.path` or use absolute intra-package `achievements.*` imports.
- Extension removal is routed through Blender's native `Extensions` UI; add-on-owned operators must not self-uninstall or delete `~/BlenderAchievements`.
- `subsurface_skin` checks exact active Subsurface Weight, and `denoiser_render` requires a completed Cycles-render event.
- Complex predicates live in pure `achievements/predicates/`; root `_check_complex_step` remains the Blender adapter.
- Unlock hashes are local integrity markers. Current-schema missing or malformed markers must fail closed and must not be backfilled.

Required delivery gate:
1. Run the relevant static verifier commands.
2. Run fast Python checks where the task touches infra or scripts.
3. Run Blender smoke for ship/deep gates when Blender is available.
4. Spawn or reuse review agents where available.
5. Complete `/review` fallback if the slash command itself is unavailable.
