# Current Handoff

## Goal

Iteration 2: Runtime And Documentation Alignment.

Align active documentation and tooling with the accepted runtime/source-of-truth decisions without changing add-on behavior.

## Changed Files

- `README.md`
- `achievements_100_list.md`
- `docs/agent/architecture.md`
- `docs/agent/archive-policy.md`
- `docs/agent/frozen-application-contract.md`
- `docs/agent/frozen-decisions.md`
- `docs/agent/packaging-release.md`
- `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`
- `docs/handoff/current.md`
- `scripts/find_blender.py`
- `tests/test_infra_scripts.py`

Branch also contains Iteration 1 baseline artifacts:

- `docs/handoff/iteration-handoff-template.md`
- `scripts/verify_codex_plugin.py`

## Done

- Updated `README.md` from the stale Blender 4.5 / 5.0 / 5.1 wording to the active policy: Blender 5.0+ floor, Blender 5.1 stable validation target, Blender 5.2 alpha canary.
- Updated `README.md` to state the current catalog scope: 105 achievements and 9 lessons.
- Removed README guidance that named a non-existent release ZIP and told users to rename `__init__.py`.
- Clarified README asset sections as expected user/release-packaged assets, not tracked repository files.
- Removed the stale Blender 4.5 Windows discovery candidate and added a Blender 5.2 canary candidate in `scripts/find_blender.py`.
- Aligned agent docs with the user decision that `achievements_v01 (4).py` remains a permanent byte-identical duplicate unless the user explicitly changes that policy.
- Added a warning to `achievements_100_list.md` that it is a stale reference and not the active catalog source.
- Expanded the roadmap with explicit TЗ-holder sections: sources, product concept, constraints, requirements, and open questions.
- Added pytest coverage for the runtime/docs alignment contract.
- Marked Iteration 2 complete in the tracked roadmap.

## Remaining

- Start Iteration 3: Skeleton And Extension Draft.
- Keep `__init__.py` and `achievements_v01 (4).py` byte-identical if any add-on source edit becomes necessary.
- Introduce package skeleton and draft extension manifest only after tests prove current behavior is pinned.

## Verification

- `uv run pytest tests/test_infra_scripts.py::test_runtime_docs_alignment_matches_current_policy` failed before the docs/tooling alignment, proving the guard.
- `uv run pytest tests/test_infra_scripts.py::test_runtime_docs_alignment_matches_current_policy tests/test_infra_scripts.py::test_iteration_plan_and_handoff_artifacts_are_present` passed after the alignment updates.
- Review found that `find_blender.py` preferred Blender 5.2 canary before Blender 5.1 stable; `uv run pytest tests/test_infra_scripts.py::test_runtime_docs_alignment_matches_current_policy` failed after adding an order guard, proving the issue.
- `uv run pytest tests/test_infra_scripts.py::test_runtime_docs_alignment_matches_current_policy` passed after making Blender 5.1 the preferred Windows candidate and keeping Blender 5.2 as canary fallback.
- Review found duplicate-policy drift in `docs/agent/archive-policy.md` and `docs/agent/frozen-application-contract.md`; `uv run pytest tests/test_infra_scripts.py::test_runtime_docs_alignment_matches_current_policy` failed after expanding the guard, proving the issue.
- `uv run pytest tests/test_infra_scripts.py::test_runtime_docs_alignment_matches_current_policy` passed after aligning those docs with the permanent byte-identical duplicate policy.
- Completion audit found the roadmap needed explicit TЗ-holder structure; `uv run pytest tests/test_infra_scripts.py::test_iteration_plan_and_handoff_artifacts_are_present` failed after adding the guard, proving the gap.
- `uv run pytest tests/test_infra_scripts.py::test_iteration_plan_and_handoff_artifacts_are_present` passed after adding roadmap sections for sources, product concept, constraints, requirements, and open questions.
- Active docs/tooling no longer present Blender 4.5 as a supported runtime, no longer name the old ZIP artifact, and no longer present duplicate removal as the default future policy.
- `uv run python scripts/verify_frozen.py` passed: `32/32 PASS`.
- `uv run python scripts/verify_codex_plugin.py` passed: `80/80 PASS`.
- `uv run ruff check .` passed.
- `uv run pytest` passed: `6 passed`.
- `uv run python scripts/find_blender.py` found Blender 5.1.2.
- Blender smoke suites `register`, `persistence`, and `rewards` passed. `rewards` still logged the known non-fatal complex-step errors documented below.

## Agents And Review

- `instruction_drift_auditor` reported README runtime drift, `find_blender.py` 4.5 candidate drift, duplicate-policy inconsistency, incomplete 9-lessons README coverage, and ambiguous handoff wording; addressed in this iteration.
- `code_deadwood_auditor` reported README ZIP/runtime/asset drift and stale `achievements_100_list.md`; addressed in this iteration.
- `blender_api_compat_guardian` reported that `find_blender.py` preferred Blender 5.2 canary before Blender 5.1 stable; addressed by adding an order guard and preferring Blender 5.1.
- `instruction_drift_auditor` reported duplicate-policy drift in `archive-policy.md` and `frozen-application-contract.md`; addressed by extending test coverage and aligning both documents.
- `tech_stack_cartographer`, `addon_runtime_mapper`, `registration_lifecycle_guardian`, and `data_persistence_guardian` reported PASS for their final review scopes.
- `/review` slash command is not callable in this environment; documented fallback review was performed.
- Final `/review` fallback status: PASS. Requirements match Iterations 1-2, diff is docs/tooling/tests only, add-on runtime files and real user data are untouched, fast gate and Blender smoke passed, and residual risks are listed below.

## Blockers

None.

## Residual Risks

- Add-on source text still contains old user-facing "100 achievements" strings and `bl_info["blender"] == (4, 5, 0)`; these are intentionally left as known code-text drift because changing source requires synchronizing the permanent duplicate and belongs in a later add-on-source iteration.
- `smoke_rewards` still logs known non-fatal complex-step errors for compositor/render-pass checks while returning PASS; Iteration 7 must make this an explicit test target.
- No production cloud/backend work has started; Cloud remains a future stub iteration.

## Next Start Prompt

Continue `codex/implement-iterative-plan-baseline` from Iteration 3: Skeleton And Extension Draft. Read `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`, `docs/handoff/current.md`, `docs/agent/frozen-application-contract.md`, and `docs/agent/frozen-decisions.md`. Do not touch real `~/BlenderAchievements` data. Before any add-on behavior change, add tests first and keep `__init__.py` plus `achievements_v01 (4).py` byte-identical unless the user explicitly changes the duplicate policy.
