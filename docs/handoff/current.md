# Current Handoff

## Goal

Iteration 11: QA And CI.

Add repository CI gates that mirror the local QA contract, expand fast unit coverage for catalog, persistence, engine, rewards, and sync stub, and document the Python 3.13 CI alignment while keeping Blender runtime behavior unchanged.

## Changed Files

- `.github/workflows/fast-gate.yml`
- `.github/workflows/blender-smoke.yml`
- `README.md`
- `docs/agent/quality-tooling.md`
- `docs/agent/verification.md`
- `docs/handoff/current.md`
- `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`
- `scripts/verify_codex_plugin.py`
- `tests/test_catalog.py`
- `tests/test_engine.py`
- `tests/test_infra_scripts.py`
- `tests/test_persistence.py`
- `tests/test_rewards.py`
- `tests/test_sync.py`

## Done

- Added `.github/workflows/fast-gate.yml` for the blocking fast gate on pull requests, pushes to `main`, and manual dispatch.
- The fast gate runs `verify_frozen`, `verify_codex_plugin`, `ruff`, and `pytest` on Python 3.13.
- Added `.github/workflows/blender-smoke.yml` for Blender smoke CI on pull requests, pushes to `main`, and manual dispatch.
- The Blender smoke workflow runs Blender 5.1 stable as the blocking target and Blender 5.2 alpha canary as a non-blocking target through `continue-on-error`.
- The canary download URL is intentionally read from repository variable `BLENDER_5_2_ALPHA_URL`.
- Both Blender smoke matrix targets run `register`, `lifecycle_stress`, `persistence`, `engine`, `rewards`, and `ui_visual`.
- Expanded catalog unit coverage in `tests/test_catalog.py` for safe import, frozen digest/counts, lesson links, reward payloads, and complex step structure.
- Expanded persistence coverage for invalid payload sanitization, stat coercion, duplicate cleanup, pinned-state type safety, and missing unlock hash generation.
- Expanded engine coverage for ratio/progress-bar clamping and empty complex achievements.
- Expanded rewards coverage for tutorial URL validation and ignored unsupported reward types.
- Expanded sync stub coverage for recursive immutable payload snapshots and deterministic set ordering.
- Updated `scripts/verify_codex_plugin.py` so the workflows and catalog unit test stay tracked infrastructure.
- Updated README, verification docs, quality-tooling docs, roadmap, infra tests, and handoff for Iteration 11.
- Left `__init__.py` and `achievements_v01 (4).py` untouched, so the duplicate contract remains unchanged.
- Kept normal unit tests free of `bpy`; Blender-only coverage remains in smoke suites routed through `scripts/run_blender_smoke.py`.

## Remaining

- Start Iteration 12: Release.
- Finalize extension manifest metadata and release documentation.
- Add Blender extension validate/build commands and decide the release asset/license policy before bundling any reward assets.
- Configure repository variable `BLENDER_5_2_ALPHA_URL` if the non-blocking canary job should actually download and smoke Blender 5.2 alpha in GitHub Actions.
- Do not add the Blender 5.2 alpha canary job to required branch protection unless the user explicitly promotes Blender 5.2 to a blocking release target.

## Verification

- Baseline before Iteration 11 changes:
  - `uv run python scripts/verify_frozen.py` passed: `35/35 PASS`.
  - `uv run python scripts/verify_codex_plugin.py` passed: `91/91 PASS`.
  - `uv run ruff check .` passed.
  - `uv run pytest` passed: `44 passed`.
- RED checks:
  - `uv run pytest tests/test_infra_scripts.py::test_iteration_11_github_actions_workflows_are_present_and_match_contract` failed before workflows existed because `.github/workflows/fast-gate.yml` was missing.
  - `uv run pytest tests/test_infra_scripts.py::test_verify_codex_plugin_passes_current_infra_contract` failed before verifier coverage was updated because workflow records were missing from verifier output.
  - `uv run pytest tests/test_catalog.py` initially failed because the new catalog test expected non-existent `catalog.COMPLEX_STEP_CHECKS`; the test was corrected to assert real catalog contracts instead.
- Targeted GREEN checks:
  - `uv run pytest tests/test_infra_scripts.py::test_iteration_11_github_actions_workflows_are_present_and_match_contract` passed.
  - `uv run pytest tests/test_infra_scripts.py::test_verify_codex_plugin_passes_current_infra_contract` passed after staging verifier-covered files.
  - `uv run pytest tests/test_catalog.py` passed: `4 passed`.
  - `uv run pytest tests/test_persistence.py` passed: `7 passed`.
  - `uv run pytest tests/test_engine.py` passed: `7 passed`.
  - `uv run pytest tests/test_rewards.py` passed: `6 passed`.
  - `uv run pytest tests/test_sync.py` passed: `9 passed`.
- Final gate:
  - `uv run python scripts/verify_frozen.py` passed.
  - `uv run python scripts/verify_codex_plugin.py` passed.
  - `uv run ruff check .` passed.
  - `uv run pytest` passed: `54 passed`.
  - `uv run python scripts/find_blender.py` found Blender 5.1.2.
  - `uv run python scripts/run_blender_smoke.py --suite register` passed on Blender 5.1.2 with temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
  - `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress` passed on Blender 5.1.2.
  - `uv run python scripts/run_blender_smoke.py --suite persistence` passed on Blender 5.1.2.
  - `uv run python scripts/run_blender_smoke.py --suite engine` passed on Blender 5.1.2.
  - `uv run python scripts/run_blender_smoke.py --suite rewards` passed on Blender 5.1.2.
  - `uv run python scripts/run_blender_smoke.py --suite ui_visual` passed on Blender 5.1.2 and saved `ui_visual_contract.png` under the temporary visual QA artifact directory.

## Agents And Review

- `quality_tooling_architect` audited the CI/tooling direction and recommended blocking fast gate plus blocking Blender 5.1 stable smoke with a non-blocking Blender 5.2 canary.
- `blender_api_compat_guardian` audited the Blender smoke CI shape, confirmed `scripts/run_blender_smoke.py` keeps temp profile isolation, and flagged two in-progress blockers: the stale `COMPLEX_STEP_CHECKS` test assumption and untracked `tests/test_catalog.py`. Both were resolved before final verification.
- Final review agents checked the staged Iteration 11 diff for CI correctness, instruction drift, and verification coverage.
- Final `/review` fallback status: PASS. Requirements match Iteration 11, CI command names mirror local gates, Blender 5.1 stable is blocking, Blender 5.2 alpha is canary-only, root Blender runtime is unchanged, duplicate contract is unchanged, and residual risks are listed below.

## Blockers

None.

## Residual Risks

- GitHub Actions canary smoke requires repository variable `BLENDER_5_2_ALPHA_URL`; without it the canary job intentionally fails non-blocking and does not provide real Blender 5.2 coverage.
- CI uses Python 3.13 while `pyproject.toml` still allows local Python 3.11+; this is intentional tooling alignment, not a local compatibility-floor change.
- Blender 5.2 alpha remains a canary and should not be made branch-protection required until a future explicit release decision.
- Release packaging, extension validation/build commands, static extension repository output, and bundled reward asset licensing are still Iteration 12 work.

## Next Start Prompt

Continue from Iteration 12: Release. Read `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`, `docs/handoff/current.md`, `docs/agent/packaging-release.md`, `docs/agent/frozen-application-contract.md`, and `docs/agent/verification.md`. Do not touch real `~/BlenderAchievements` data. Finalize extension packaging metadata and release docs, add Blender extension validate/build commands, preserve the byte-identical duplicate contract, keep README updated, and decide bundled asset/license policy before packaging any reward assets.
