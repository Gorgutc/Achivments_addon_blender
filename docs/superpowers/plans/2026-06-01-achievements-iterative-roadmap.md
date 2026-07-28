# Achievements Iterative Roadmap Implementation Plan

> **SUPERSEDED — HISTORICAL PLAN ONLY.** This roadmap records the pre-0.2.0 implementation sequence and is not an active instruction source. Use `AGENTS.md`, `docs/agent/*`, `docs/handoff/current.md`, and ADRs 0002–0006 for current policy. ADR 0002 retired `achievements_v01 (4).py`; do not restore it from obsolete statements below.

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` for implementation tasks with scoped review agents, or `superpowers:executing-plans` when subagents are unavailable. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current Achievements Blender add-on prototype into a maintainable Blender 5.x product through small, reviewable iterations.

**Architecture:** Preserve the current `__init__.py` behavior while gradually extracting a modular `achievements/` package. Keep local-first persistence, all 105 achievements, all 9 lessons, and the permanent byte-identical duplicate file contract for `achievements_v01 (4).py`.

**Tech Stack:** Blender 5.0+ policy, Blender 5.1 stable validation target, Blender 5.2 alpha canary, Python through Blender's bundled runtime, `uv`, `ruff`, `pytest`, Blender background smoke tests.

---

## Sources

- GitHub repository: `https://github.com/Gorgutc/Achivments_addon_blender`, default branch `main`, local `main` and `origin/main` audited at `4fdafd45c442d59a6b7d8457fe369754798d23b3`.
- Repository instructions and orchestration sources: `AGENTS.md`, `.codex/config.toml`, `.codex/hooks.json`, `.codex/agents/*`, `.codex/plugins/achievements/*`, `docs/agent/*`, `scripts/verify_frozen.py`, and `scripts/verify_codex_plugin.py`.
- Drive concept document: `Исследование идеи аддона достижений для Blender 5.x.md`, file ID `198tPsyvohUoVkImaLhOD05q1tIgCWL1X`.
- Drive iteration prompt package: `master-prompt и task-prompts для Codex для Blender add-on Achievements.md`, file ID `14_uK24navom4tmBFr0EabYQYHH-Ra4fg`.

## Product Concept

Build `Achievements` as an offline-first Blender add-on that turns Blender learning and production work into a structured achievement system. The product surface is the Blender 3D Viewport header entry, a popup with task/done/lesson/storage tabs, XP/levels, visual notifications, pinned progress, tutorial links, and reward claiming for material, mesh, and geo-node assets.

The MVP preserves the current full catalog rather than reducing scope: all 105 achievements, all 9 lessons, existing Russian user-facing text, existing reward semantics, and existing local JSON persistence under `~/BlenderAchievements/`.

## Constraints

- Do not edit or delete real user progress under `~/BlenderAchievements/` or any generated `achievements_data.json`.
- Do not change add-on behavior in preparation or documentation-only iterations.
- Keep `__init__.py` as the canonical active add-on source until a tested migration proves parity.
- Keep `achievements_v01 (4).py` as a permanent byte-identical duplicate unless the user explicitly changes that policy.
- Keep normal unit tests free of `bpy`; Blender-specific behavior belongs in background smoke suites.
- Use explicit subagents for independent audit, review, and verification tasks when the environment exposes them.
- Run `/review` before final delivery; if the slash command is unavailable, perform the documented fallback review from `docs/agent/code-review.md`.
- Treat Blender 5.1 stable as the primary validation target and Blender 5.2 alpha as canary.

## Requirements

- Preserve the existing achievement and lesson catalog IDs, categories, difficulties, Russian texts, reward data, lesson links, stat keys, complex IDs, complex steps, and counts.
- Maintain local-first persistence and later harden it with schema versioning, idempotent migrations, atomic writes, backup/quarantine, corrupt JSON recovery, and temp-profile smoke coverage.
- Split the current single-file implementation into focused modules only through reviewable iterations with tests and Blender smoke parity.
- Preserve UI contracts for tabs `Задания / Выполнено / Уроки / Хранилище`, card layout, pinned overlay, notifications, pagination, storage grouping, and long RU/EN text behavior.
- Preserve reward fallback behavior for missing `.blend` assets and defer bundled asset licensing decisions until the rewards/release iterations.
- Add only a cloud stub/queue/conflict layer until a separate production backend task exists; no normal-use network calls.
- Keep handoff current after every iteration with enough detail for another session to resume without reconstructing context.

## Operating Decisions

- Runtime policy: Blender 5.0+ remains the active repository compatibility floor.
- Primary validation target: Blender 5.1 stable.
- Canary target: Blender 5.2 alpha. Canary failures do not block Blender 5.1 stable delivery unless a task explicitly promotes 5.2 to a release target.
- Catalog scope: migrate all 105 achievements and all 9 lessons.
- Duplicate contract: `achievements_v01 (4).py` remains a permanent tracked byte-identical duplicate unless the user explicitly changes that policy.
- Data safety: never edit or delete real `~/BlenderAchievements` data or generated `achievements_data.json`.
- Unit tests must not import `bpy`; Blender-only behavior is verified through background smoke suites.

## Iteration 1: Plan Artifact And Handoff Baseline

- [x] Add a tracked implementation roadmap at `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`.
- [x] Add a reusable handoff template at `docs/handoff/iteration-handoff-template.md`.
- [x] Add the first current handoff at `docs/handoff/current.md`.
- [x] Add a pytest guard that fails when the plan or handoff artifacts are missing.
- [x] Update Codex verifier coverage so required handoff artifacts remain tracked.

**Acceptance:** The plan and handoff files exist, pytest verifies required sections, add-on behavior is unchanged, and no real user data is touched.

## Iteration 2: Runtime And Documentation Alignment

- [x] Align README and agent docs with the active decisions: Blender 5.0+ compatibility floor, Blender 5.1 stable validation target, Blender 5.2 alpha canary, 105 achievements, 9 lessons.
- [x] Keep old 100-achievement text documented only as known drift until the exact code strings are intentionally updated.
- [x] If metadata changes affect add-on source, update `__init__.py` and `achievements_v01 (4).py` together and update verifiers in the same task. No add-on source metadata was changed in this iteration.

**Acceptance:** Active docs and verifiers agree on runtime policy and source-of-truth files; duplicate hash remains valid.

## Iteration 3: Skeleton And Extension Draft

- [x] Introduce a modular `achievements/` package without changing runtime behavior.
- [x] Keep `__init__.py` as the Blender entrypoint and delegate only when smoke tests prove parity.
- [x] Add a draft `blender_manifest.toml` early so extension packaging constraints shape later work.

**Acceptance:** Register/unregister smoke passes, package import is safe in normal Python, and imports do not create real user data.

## Iteration 4: Catalog Migration

- [x] Extract all achievement and lesson definitions into schema-driven catalog modules.
- [x] Preserve IDs, Russian user-facing strings, categories, rewards, lesson links, and complex steps.
- [x] Add catalog validators for IDs, counts, references, reward types, stat keys, and complex step coverage.

**Acceptance:** Verifiers still confirm 105 achievements, 9 lessons, unique IDs, category counts, difficulty counts, and reward counts.

## Iteration 5: Lifecycle And Event Layer

- [x] Split handlers, timers, activity tracking, scene snapshots, and debounce into runtime modules.
- [x] Harden hot reload: repeated `register()` without `unregister()` and repeated `unregister()` must not leak or crash.
- [x] Add repeated lifecycle stress smoke coverage.

**Acceptance:** `register`, repeated lifecycle stress, and cleanup assertions pass with no duplicate header, timer, or draw handlers.

## Iteration 6: Persistence Hardening

- [x] Add `schema_version`, state model, and idempotent migrations.
- [x] Replace direct JSON writes with same-directory temp-file writes, flush/fsync, `os.replace`, and backup handling.
- [x] Add corrupt JSON quarantine/recovery behavior and fixtures for current schema migration.

**Acceptance:** Persistence smoke passes under a temporary profile; corrupt JSON tests pass; real user data remains untouched.

## Iteration 7: Engine And Rule Evaluation

- [x] Extract stat and complex achievement evaluation into pure modules.
- [x] Add proof/result types and progress calculation interfaces.
- [x] Cover compositor and render-pass checks that currently log `[Achievements] complex step check error` during `smoke_rewards`.

**Acceptance:** Pure unit tests cover rule evaluation, Blender fixtures cover complex checks, and CI does not mask runtime error markers.

## Iteration 8: Rewards Layer

- [x] Extract reward manifest, verifier, cache, importer, and manager modules.
- [x] Preserve fallback behavior for missing material, mesh, and geo node `.blend` assets.
- [x] Record asset licensing decisions before bundling any release assets.

**Acceptance:** Rewards smoke passes, reward claims persist correctly, fallbacks remain intentional, and no real user data is mutated in tests.

## Iteration 9: UI Split And Visual QA

- [x] Split Scene properties, operators, popup tabs/cards, notifications, and pinned overlay into UI modules.
- [x] Preserve tabs: `Задания`, `Выполнено`, `Уроки`, `Хранилище`.
- [x] Run screenshot-based visual QA for header button, popup layout, pinned overlay, notifications, and long text.

**Acceptance:** Blender smoke passes and `blender_ui_visual_qa` approves visual evidence.

## Iteration 10: Cloud Stub

- [x] Add sync models, disabled backend interface, queue, and deterministic conflict policy.
- [x] Keep networking disabled by default.
- [x] Exclude pinned UI state from sync unless a future task explicitly changes that.

**Acceptance:** Offline behavior remains complete, queue tests pass, conflict outcomes are documented and deterministic.

## Iteration 11: QA And CI

- [x] Expand unit coverage for catalog, persistence, engine, rewards, and sync stub.
- [x] Add GitHub Actions fast gate: `verify_frozen`, `verify_codex_plugin`, `ruff`, `pytest`.
- [x] Add Blender 5.1 stable smoke gate and Blender 5.2 alpha canary gate.
- [x] Align CI tooling with Python 3.13 while preserving the repository's local Python 3.11+ compatibility policy.

**Acceptance:** Local and CI command names agree, stable gates are blocking, and canary gates are clearly marked.

## Iteration 12: Release

- [x] Finalize extension manifest metadata and release documentation.
- [x] Add validate/build commands for Blender extension packaging.
- [x] Add optional static extension repository generation only after release packaging is stable.

**Acceptance:** Extension validate/build commands pass, full fast and Blender gates pass, `/review` or fallback is recorded, and handoff is complete.

## Open Questions

- Which asset licenses are acceptable for any bundled reward `.blend` files in an official extension package?
- Should Blender 5.2 alpha ever become a blocking target, or remain non-blocking canary until a future explicit release decision?
- What production backend, identity model, and conflict authority should be used if Cloud moves beyond the disabled offline-first stub?
- Should the permanent duplicate policy ever be changed, and if so what replacement archival/verifier policy should be approved first?

## Handoff Gate

After each iteration, update `docs/handoff/current.md` from `docs/handoff/iteration-handoff-template.md` with:

- iteration goal
- changed files
- work completed
- work remaining
- verification commands and results
- agents and review outcome
- blockers
- residual risks
- next start prompt

Do not start the next risky runtime iteration until the current handoff has enough detail for another agent or chat to resume without reconstructing context.
