# Current Handoff

## Goal

Iteration 9: UI Split And Visual QA.

Extract pure UI contract and layout-planning helpers while preserving the root `__init__.py` Blender adapter for `bpy`, popup drawing, GPU overlays, operators, header callbacks, and side effects.

## Changed Files

- `README.md`
- `__init__.py`
- `achievements/ui.py`
- `achievements_v01 (4).py`
- `docs/agent/architecture.md`
- `docs/agent/frozen-application-contract.md`
- `docs/agent/verification.md`
- `docs/handoff/current.md`
- `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`
- `scripts/run_blender_smoke.py`
- `scripts/verify_codex_plugin.py`
- `tests/blender/smoke_ui_visual.py`
- `tests/test_ui.py`
- `tests/test_infra_scripts.py`

## Done

- Added `achievements/ui.py` as a pure helper module with no `bpy`, no user-data path access, and no import-time Blender side effects.
- Added `TabSpec`, `ScenePropertySpec`, `GridPagePlan`, and `OverlayFrame` contracts.
- Moved UI tab specs, Scene property specs, pagination plans, popup dialog width, notification frame geometry, pinned overlay frame geometry, reward labels, storage filters, category filtering, and long RU/EN text budgeting into `achievements/ui.py`.
- Root popup tabs, pagination, item filtering, Scene property registration, notification geometry, pinned overlay geometry, and card/overlay text labels now delegate to `achievements/ui.py`.
- Preserved tabs `Задания / Выполнено / Уроки / Хранилище`, 2x5 grid, 10 cards per page, storage grouping, notification stacking, pinned overlay positioning, and byte-identical duplicate contract.
- Added `tests/test_ui.py` for pure UI contract coverage, including long RU/EN text budgets.
- Added Blender smoke suite `ui_visual` and `tests/blender/smoke_ui_visual.py` for tab-state acceptance, overlay no-overlap geometry, and generated visual contract artifact coverage for header button, popup tabs/cards, pinned overlay, and notifications.
- Updated `README.md`, architecture docs, frozen contract, verification docs, verifier registry, roadmap, and handoff for Iteration 9.
- Kept `__init__.py` and `achievements_v01 (4).py` byte-identical after root runtime edits.

## Remaining

- Start Iteration 10: Cloud Stub.
- Add sync models, disabled backend interface, offline queue, deterministic conflict policy, and tests.
- Keep networking disabled by default and keep pinned UI state out of sync unless a future task explicitly changes that.
- Continue updating README whenever structure, commands, or user/developer workflow changes.

## Verification

- Baseline before Iteration 9 changes:
  - `uv run python scripts/verify_frozen.py` passed: `35/35 PASS`.
  - `uv run python scripts/verify_codex_plugin.py` passed: `89/89 PASS`.
  - `uv run ruff check .` passed.
  - `uv run pytest` passed: `30 passed`.
- RED checks:
  - `uv run pytest tests/test_ui.py` failed before implementation because `achievements/ui.py` did not exist.
  - `uv run pytest tests/test_ui.py::test_long_ru_and_en_text_is_budgeted_for_cards_and_overlays` failed before text-budget helpers existed.
  - `uv run pytest tests/test_infra_scripts.py::test_blender_smoke_dry_run_uses_temp_home_and_ui_visual_suite tests/test_infra_scripts.py::test_verify_codex_plugin_passes_current_infra_contract` failed before `ui_visual` and `achievements/ui.py` were registered in tooling.
- Targeted GREEN checks:
  - `uv run pytest tests/test_ui.py` passed: `5 passed`.
  - `uv run pytest tests/test_ui.py tests/test_infra_scripts.py::test_verify_codex_plugin_passes_current_infra_contract tests/test_infra_scripts.py::test_blender_smoke_dry_run_uses_temp_home_and_ui_visual_suite` passed: `6 passed`.
  - `uv run python scripts/run_blender_smoke.py --suite register` passed.
  - `uv run python scripts/run_blender_smoke.py --suite ui_visual` passed and saved `ui_visual_contract.png` under the temp visual QA artifact directory.
- Final gate:
  - `uv run python scripts/verify_frozen.py` passed: `35/35 PASS`.
  - `uv run python scripts/verify_codex_plugin.py` passed: `90/90 PASS`.
  - `uv run ruff check .` passed.
  - `uv run pytest` passed: `36 passed`.
  - `uv run python scripts/run_blender_smoke.py --suite register` passed.
  - `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress` passed.
  - `uv run python scripts/run_blender_smoke.py --suite persistence` passed.
  - `uv run python scripts/run_blender_smoke.py --suite engine` passed.
  - `uv run python scripts/run_blender_smoke.py --suite rewards` passed.
  - `uv run python scripts/run_blender_smoke.py --suite ui_visual` passed.
- Blender smoke suite `ui_visual` passed with visual contract artifact coverage.

## Agents And Review

- `addon_runtime_mapper`/Avicenna audited UI boundaries, contracts, duplicate risk, and UTF-8 text risks; its duplicate and text-contract findings were addressed.
- `blender_ui_visual_qa`/Banach audited screenshot/visual QA options and recommended a separate non-flaky `ui_visual` suite; that suite was added.
- `verification_reviewer`/Parfit reviewed the staged Iteration 9 diff, found no UI split code blocker, confirmed no dead delegated blocks remained, and flagged only the stale pending review line that was corrected before final gates.
- Final `/review` fallback status: PASS. Requirements match Iteration 9, duplicate contract is restored, `achievements/ui.py` is pure, root delegates UI contract planning while retaining Blender adapter side effects, `ui_visual` smoke provides visual evidence, and residual risks are listed below.

## Blockers

None.

## Residual Risks

- `achievements/ui.py` plans UI contracts and geometry, but actual `bpy.types.Operator` classes, `layout.*` drawing, preview icons, `gpu`/`blf`, draw handlers, and save/unpin side effects intentionally remain in the root runtime adapter.
- `ui_visual` currently generates a deterministic visual contract artifact rather than driving a foreground Blender window screenshot; this keeps the gate stable in background smoke but is less representative than a real interactive screenshot.
- Long text is budgeted by character count, not by Blender font pixel measurement; a future foreground visual QA task can add `blf.dimensions` or OCR/pixel checks.
- Current root source still contains old user-facing "100 achievements" runtime strings and `bl_info["blender"] == (4, 5, 0)`; these remain known frozen drift.
- No production cloud/backend work has started; Cloud remains a future stub iteration.

## Next Start Prompt

Continue from Iteration 10: Cloud Stub. Read `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`, `docs/handoff/current.md`, `docs/agent/frozen-application-contract.md`, and `docs/agent/frozen-decisions.md`. Do not touch real `~/BlenderAchievements` data. Start with failing tests for disabled sync backend models, offline queue behavior, deterministic conflict policy, and pinned UI state exclusion. Keep normal unit tests free of `bpy`, keep normal use network-free, and keep `__init__.py` plus `achievements_v01 (4).py` byte-identical for any root runtime edits.
