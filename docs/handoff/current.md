# Current Handoff

## Goal

Iteration 8: Rewards Layer.

Extract pure reward manifest, verifier, asset-existence cache, importer/action planning, and manager decisions while preserving Blender material, mesh, and geo node fallback behavior and reward claim persistence.

## Changed Files

- `README.md`
- `__init__.py`
- `achievements/rewards.py`
- `achievements_v01 (4).py`
- `docs/agent/architecture.md`
- `docs/agent/frozen-application-contract.md`
- `docs/agent/packaging-release.md`
- `docs/agent/verification.md`
- `docs/handoff/current.md`
- `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`
- `scripts/verify_codex_plugin.py`
- `tests/blender/smoke_rewards.py`
- `tests/test_rewards.py`
- `tests/test_infra_scripts.py`

## Done

- Added `achievements/rewards.py` as a pure helper module with no `bpy`, no user-data path access, and no import-time Blender side effects.
- Added `RewardSpec`, `RewardAction`, `RewardResult`, `RewardManifest`, `RewardVerifier`, `AssetCache`, and `RewardManager`.
- Moved reward manifest, verifier, cache, importer/action planner, and manager decisions into the rewards module.
- Root `ACH_OT_ApplyReward` now delegates access checks, unlock-hash verification, asset path resolution, cache-backed asset existence, tutorial/no-reward handling, and fallback planning to `achievements/rewards.py`.
- Root `ACH_OT_ApplyReward` remains the Blender adapter for actual `.blend` linking, placeholder material creation, placeholder mesh creation, placeholder geo node modifier creation, reporting, saving, and `stats.rewards_claimed`.
- Preserved material, mesh, and geo node fallback behavior for missing `.blend` assets.
- Preserved legacy late-asset behavior by caching only existing asset paths; missing assets are rechecked on later claims.
- Strengthened `tests/blender/smoke_rewards.py` to verify reward claim persistence in runtime stats, JSON, and `load_data()`.
- Recorded asset licensing policy: bundled reward `.blend` assets remain release-blocked until licenses are explicitly approved.
- The asset licensing policy remains release-blocked until reward `.blend` asset licenses are explicitly approved.
- README, architecture, frozen contract, verification docs, packaging/release docs, verifier registry, roadmap, and handoff were updated for Iteration 8.
- Kept `__init__.py` and `achievements_v01 (4).py` byte-identical after root runtime edits.

## Remaining

- Start Iteration 9: UI Split And Visual QA.
- Split Scene properties, operators, popup tabs/cards, notifications, and pinned overlay into UI modules.
- Preserve tabs `Задания / Выполнено / Уроки / Хранилище`, card layout contracts, pinned overlay, notifications, pagination, storage grouping, and long text behavior.
- Run screenshot-based visual QA for header button, popup layout, pinned overlay, notifications, and long text.
- Keep `__init__.py` and `achievements_v01 (4).py` byte-identical for root runtime edits.

## Verification

- Baseline before Iteration 8 changes:
  - `uv run python scripts/verify_frozen.py` passed: `35/35 PASS`.
  - `uv run python scripts/verify_codex_plugin.py` passed: `88/88 PASS`.
  - `uv run ruff check .` passed.
  - `uv run pytest` passed: `25 passed`.
- RED checks:
  - `uv run pytest tests/test_rewards.py` failed before implementation because `achievements/rewards.py` did not exist.
  - `uv run pytest tests/test_rewards.py::test_asset_cache_rechecks_missing_assets_so_late_files_can_link` failed before cache refinement because missing asset paths were cached as misses.
- Targeted GREEN checks:
  - `uv run pytest tests/test_rewards.py` passed: `5 passed`.
  - `uv run python scripts/run_blender_smoke.py --suite rewards` passed with material, mesh, geo fallback, and claim persistence checks.
- Final gate:
  - `uv run python scripts/verify_frozen.py` passed: `35/35 PASS`.
  - `uv run python scripts/verify_codex_plugin.py` passed: `89/89 PASS`.
  - `uv run ruff check .` passed.
  - `uv run pytest` passed.
  - `uv run python scripts/run_blender_smoke.py --suite register` passed.
  - `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress` passed.
  - `uv run python scripts/run_blender_smoke.py --suite persistence` passed.
  - `uv run python scripts/run_blender_smoke.py --suite engine` passed.
  - `uv run python scripts/run_blender_smoke.py --suite rewards` passed.
- Blender smoke suite `rewards` passed with fallback and claim persistence checks.

## Agents And Review

- `reward_layer_mapper`/Einstein audited the current reward flow and provided extraction risks and test recommendations.
- `verification_reviewer`/Galileo reviewed the staged Iteration 8 diff, found no reward-layer code blocker, and flagged the stale pending review line that was corrected before final gates.
- Final `/review` fallback status: PASS. Requirements match Iteration 8, duplicate contract is restored, the rewards module is pure, late-added assets are rechecked after missing-asset fallbacks, rewards smoke preserves fallback and claim persistence behavior, and residual risks are listed below.

## Blockers

None.

## Residual Risks

- Actual Blender `.blend` library loading and placeholder creation still live in root `ACH_OT_ApplyReward` adapter; the pure rewards module plans actions but does not import `bpy`.
- Existing asset paths are cached per process; missing assets are rechecked on later claims, but deleted assets after a positive cache hit may need a future explicit invalidation hook.
- Bundled reward assets remain release-blocked until asset licenses are approved; missing-asset fallbacks are still the intentional default.
- Current root source still contains old user-facing "100 achievements" runtime strings and `bl_info["blender"] == (4, 5, 0)`; these remain known frozen drift.
- No production cloud/backend work has started; Cloud remains a future stub iteration.

## Next Start Prompt

Continue from Iteration 9: UI Split And Visual QA. Read `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`, `docs/handoff/current.md`, `docs/agent/frozen-application-contract.md`, and `docs/agent/frozen-decisions.md`. Do not touch real `~/BlenderAchievements` data. Start with UI split tests and screenshot-based visual QA planning for header button, popup tabs/cards, pinned overlay, notifications, and long text. Preserve the existing tabs `Задания / Выполнено / Уроки / Хранилище`, layout contracts, reward storage grouping, and byte-identical duplicate contract.
