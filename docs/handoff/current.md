# Achievements — Reward Claim Atomicity

## Goal

Make asset reward claims truthful and retryable: confirm the Blender-side action first, persist a prospective claim atomically second, and mutate the runtime claim set only after the write succeeds. The work is isolated on `codex/reward-claim-atomicity` from exact `origin/main@9cd26bd616c861578bc026a627c1796dddcac655`; PR #16 is already merged in that base and is not a continuation target.

## Changed Files

- Runtime/pure logic: sole runtime `__init__.py`, `achievements/rewards.py`, and `achievements/persistence.py`.
- Regression coverage: `tests/test_rewards.py`, `tests/test_persistence.py`, `tests/blender/smoke_rewards.py`, `tests/test_infra_scripts.py`, `scripts/run_blender_smoke.py`, `scripts/verify_frozen.py`, and `scripts/verify_codex_plugin.py`.
- Decision/instruction surfaces: ADR 0007, architecture, frozen decisions, frozen application contract, verification guide, frozen-decisions skill, the superseded roadmap's live policy pointer, and this handoff.

## Done

- `material`, `mesh`, and `geo_nodes` now use `claim_after_apply`; the read-only `RewardResult.mark_claimed` compatibility alias is preserved, and tutorial/`none` behavior is unchanged.
- Each asset action returns a confirmed postcondition. Missing expected datablocks, incompatible targets, wrong subtypes, false postconditions, and Blender exceptions return `CANCELLED` without persistence or a claim.
- The first claim is a prospective claim: `payload_from_stats(..., reward_claim=id)` leaves runtime state unchanged, the existing same-directory atomic JSON write runs, and only a successful write adds the in-memory claim.
- Save failure after confirmed action returns `FINISHED` with a retry warning. Material/Object/GeometryNodeTree markers let the next unclaimed attempt recover the existing witness and retry persistence idempotently without duplicating Blender state.
- Invalid and partial actions restore material data/object links, empty slots, and active indices for all objects sharing a mesh, remove partial modifiers, and remove the complete newly loaded/created Blender ID delta, including nested dependencies and Library IDs. Geo-node actions preserve Blender-supported non-mesh targets and require an actual `NODES` modifier with the assigned GeometryNodeTree.
- Already-persisted rewards retain explicit reapply and skip redundant claim persistence.
- ADR 0007 freezes this behavior. Recovery markers are idempotency metadata, not authentication. Version `0.2.2`, schema `1.0.0`, exact JSON keys, 105 achievements, 9 lessons, XP policy, catalog/assets, files-only permission, and disabled production networking are unchanged.

## Remaining

- Research a separate tutorial-proof design: compare the learner's Blender result with an approved lesson result and award only after a defensible threshold such as 90%; define normalized scene features, weights, tolerances, anti-gaming rules, explainable differences, and author-owned reference fixtures before implementation.
- Research anti-piracy/licensing separately; local unlock hashes and reward markers are not authentication. Any account or entitlement system requires an explicit privacy/network/revocation/offline-grace specification.
- Design an owner-only authoring UI separately for achievement cards, text, illustrations, tutorials, and reward assets, with validation and an export/review workflow rather than hidden production secrets in the add-on.
- Owner-input content epics remain: 219 licensed PNG files, 11 approved tutorial URLs, and 20 licensed reward `.blend` files.
- Predicate semantics, deeper fixtures, UI/GPU/handler decomposition, production cloud, release versioning, tag, and GitHub Release remain separate decisions.

## Verification

Required fast gate:

1. `uv run python scripts/verify_frozen.py`
2. `uv run python scripts/verify_codex_plugin.py`
3. `uv run python scripts/verify_predicates.py`
4. `uv run ruff check .`
5. `uv run pytest`

Current-tree evidence: `verify_frozen.py` **59/59 PASS**; `verify_codex_plugin.py` **120/120 PASS**; predicate registry **65 IDs / 85 catalog pairs PASS**; Ruff PASS; pytest **482 passed**. All six source smoke suites pass on local Blender 5.1.2 with disposable profiles. The expanded reward suite also passes on Blender 5.2.0 LTS and covers six linked/fallback save-failure retries, exact runtime/JSON state, nested dependency cleanup, exact shared-mesh/object-linked material-slot and active-index rollback, supported CURVE targets, incompatible LIGHT denial, partial-action rollback, and persisted reapply. `git diff --check` passes.

No local Blender 5.0 executable is installed; the existing GitHub matrix is historical base evidence, not a run of this unpublished branch. No install/ZIP/release gate is authorized for this slice.

## Agents And Review

- A persistent component guardian holds the task contract, frozen invariants, no-real-data boundary, and session record.
- Independent reward test and Blender API reviewers have confirmed the expanded current-tree behavior with 0 Critical / 0 Important / 0 Low after nested-ID, rollback, and cross-version geo fixes.
- Explorer, code, dead-code, instruction-drift, verification, and lookahead reviews completed in waves. They found and closed exact shared-owner active-index rollback, compatibility-guard, handoff-guard, and live ADR-pointer gaps; final re-review is 0 Critical / 0 Important / 0 Low.
- The explicit `/review` fallback covered requirements, diff, checks, blockers, and residual risks because no callable slash command was available.

## Blockers

None for local implementation and verification. No push, PR, tag, GitHub Release, version bump, production asset addition, or real `~/BlenderAchievements` access is authorized.

## Residual Risks

- Witness recovery is scene/session local. A process crash can recover only when the marked `.blend` state survives; there is no cross-process reward journal.
- Concurrent Blender processes still share one JSON file and can overwrite each other last-writer-wins; multi-process coordination is a separate persistence task.
- Blender Undo does not reverse the external JSON claim; the claim proves a successful application event, while explicit reapply restores a removed scene result.
- `bpy.data.user_map()` delta cleanup assumes synchronous operator execution so unrelated IDs are not created inside the same action window.
- Production reward assets still require license approval and exact expected-datablock validation.
- Blender 5.0 behavior will rely on the blocking CI matrix when this branch is eventually published; it is not locally installed in this session.

## Next Start Prompt

Verify the exact local branch/commit and current `origin/main` before continuing. Do not redo reward claim atomicity. Take one separate task at a time; the recommended next task is a research-only specification for tutorial result verification and a defensible 90% threshold. Keep real `~/BlenderAchievements` untouched and do not publish or release without explicit owner authorization.
