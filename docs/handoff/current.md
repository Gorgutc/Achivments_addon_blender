# Current Handoff

## Goal

Iteration 3: Skeleton And Extension Draft.

Introduce the first modular package shell and a draft Blender extension manifest without changing runtime behavior.

## Changed Files

- `achievements/__init__.py`
- `achievements/metadata.py`
- `blender_manifest.toml`
- `docs/agent/packaging-release.md`
- `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`
- `docs/handoff/current.md`
- `scripts/verify_codex_plugin.py`
- `tests/test_infra_scripts.py`

## Done

- Added `achievements/` as a safe Python package shell with metadata only.
- Package import is safe in normal Python: it does not import `bpy`, does not call `Path.home()`, and does not create `BlenderAchievements` directories.
- Added draft `blender_manifest.toml` using Blender extension manifest fields: `schema_version`, `id`, `version`, `name`, `tagline`, `maintainer`, `type`, `blender_version_min`, and SPDX license.
- No add-on runtime behavior was delegated to the new package; root `__init__.py` remains the Blender entrypoint.
- Left `achievements_v01 (4).py` untouched, preserving the permanent byte-identical duplicate contract.
- Updated `scripts/verify_codex_plugin.py` so the package skeleton and draft manifest are required tracked infra.
- Added pytest coverage for package import safety, manifest metadata, and verifier output.
- Updated packaging notes to say the draft manifest exists but release packaging is still non-blocking and not ready for archives.
- Marked Iteration 3 complete in the tracked roadmap.

## Remaining

- Start Iteration 4: Catalog Migration.
- Keep `__init__.py` and `achievements_v01 (4).py` byte-identical if any add-on source edit becomes necessary.
- Extract all 105 achievements and 9 lessons into schema-driven catalog modules only after tests pin current catalog counts, IDs, reward data, lesson links, stat keys, complex IDs, and complex steps.
- Keep normal unit tests free of `bpy`; Blender-only catalog parity belongs in focused smoke or fixture tests.

## Verification

- `uv run pytest tests/test_infra_scripts.py::test_iteration_3_package_skeleton_and_manifest_are_safe_to_import tests/test_infra_scripts.py::test_verify_codex_plugin_passes_current_infra_contract` failed before implementation because the Iteration 3 package, manifest, and verifier coverage were missing.
- `uv run pytest tests/test_infra_scripts.py::test_iteration_3_package_skeleton_and_manifest_are_safe_to_import tests/test_infra_scripts.py::test_verify_codex_plugin_passes_current_infra_contract` passed after adding the skeleton, manifest, and verifier coverage.
- `uv run pytest tests/test_infra_scripts.py::test_iteration_plan_and_handoff_artifacts_are_present tests/test_infra_scripts.py::test_runtime_docs_alignment_matches_current_policy` failed before updating the roadmap, handoff, and packaging notes for Iteration 3.
- `uv run python scripts/verify_frozen.py` passed.
- `uv run python scripts/verify_codex_plugin.py` passed.
- `uv run ruff check .` passed.
- `uv run pytest` passed.
- `uv run python scripts/find_blender.py` found Blender 5.1.2.
- Blender smoke suite `register` passed.

## Agents And Review

- `iteration_3_contract_reviewer` confirmed required acceptance points: modular package, root entrypoint retention, draft manifest, register smoke, import safety, and no real data creation.
- `runtime_duplicate_risk_auditor` confirmed the safe path: keep `__init__.py` and `achievements_v01 (4).py` untouched, avoid package side effects, run `verify_frozen`, `verify_codex_plugin`, `ruff`, `pytest`, and register smoke.
- `/review` slash command is not callable in this environment; documented fallback review was performed.
- Final `/review` fallback status: PASS. Requirements match Iteration 3, diff is package skeleton/manifest/docs/tooling/tests only, add-on runtime files and real user data are untouched, fast gate and register smoke passed, and residual risks are listed below.

## Blockers

None.

## Residual Risks

- Draft `blender_manifest.toml` has not been validated or built as a release extension; release packaging remains Iteration 12 scope.
- The new `achievements/` package is not a functional extension entrypoint yet; runtime `register()`/`unregister()` still live in root `__init__.py`.
- Add-on source text still contains old user-facing "100 achievements" strings and `bl_info["blender"] == (4, 5, 0)`; these are intentionally left as known code-text drift because changing source requires synchronizing the permanent duplicate and belongs in a later add-on-source iteration.
- `smoke_rewards` previously logged known non-fatal complex-step errors for compositor/render-pass checks while returning PASS; Iteration 7 must make this an explicit test target.
- No production cloud/backend work has started; Cloud remains a future stub iteration.

## Next Start Prompt

Continue `codex/iteration-3-skeleton-extension-draft` from Iteration 4: Catalog Migration. Read `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`, `docs/handoff/current.md`, `docs/agent/frozen-application-contract.md`, and `docs/agent/frozen-decisions.md`. Do not touch real `~/BlenderAchievements` data. Before extracting catalog code, add tests that pin the current 105 achievements, 9 lessons, IDs, Russian texts, reward data, lesson links, stat keys, complex IDs, and complex steps. Keep `__init__.py` plus `achievements_v01 (4).py` byte-identical unless the user explicitly changes the duplicate policy.
