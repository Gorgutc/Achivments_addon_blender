# Achievements — Reward Claim Atomicity

## Goal

Make asset reward claims truthful and retryable: confirm the Blender-side action first, persist a prospective claim atomically second, and mutate the runtime claim set only after the write succeeds. PR #17 delivered exact branch head `213babb6e29e023617a66600e4b9d8375ea466d9` from `codex/reward-claim-atomicity`, based on `origin/main@9cd26bd616c861578bc026a627c1796dddcac655`, and merged it into `main` as `396dda957908b26c94d73387bcddf14712a4c23c`. This living handoff is refreshed by a scoped docs/guard follow-up whose containing merge must be resolved from Git history rather than self-referenced.

## Changed Files

- Runtime/pure logic: sole runtime `__init__.py`, `achievements/rewards.py`, and `achievements/persistence.py`.
- Regression coverage: `tests/test_rewards.py`, `tests/test_persistence.py`, `tests/blender/smoke_rewards.py`, `tests/test_infra_scripts.py`, `scripts/run_blender_smoke.py`, `scripts/verify_frozen.py`, and `scripts/verify_codex_plugin.py`.
- Decision/instruction surfaces: ADR 0007, architecture, frozen decisions, frozen application contract, verification guide, frozen-decisions skill, the superseded roadmap's live policy pointer, and this handoff.
- Post-merge closeout: only this handoff, its fail-closed verifier, and focused mutant coverage change after PR #17.

## Done

- `material`, `mesh`, and `geo_nodes` now use `claim_after_apply`; the read-only `RewardResult.mark_claimed` compatibility alias is preserved, and tutorial/`none` behavior is unchanged.
- Each asset action returns a confirmed postcondition. Missing expected datablocks, incompatible targets, wrong subtypes, false postconditions, and Blender exceptions return `CANCELLED` without persistence or a claim.
- The first claim is a prospective claim: `payload_from_stats(..., reward_claim=id)` leaves runtime state unchanged, the existing same-directory atomic JSON write runs, and only a successful write adds the in-memory claim.
- Save failure after confirmed action returns `FINISHED` with a retry warning. Material/Object/GeometryNodeTree markers let the next unclaimed attempt recover the existing witness and retry persistence idempotently without duplicating Blender state.
- Invalid and partial actions restore material data/object links, empty slots, and active indices for all objects sharing a mesh, remove partial modifiers, and remove the complete newly loaded/created Blender ID delta, including nested dependencies and Library IDs. Geo-node actions preserve Blender-supported non-mesh targets and require an actual `NODES` modifier with the assigned GeometryNodeTree.
- Already-persisted rewards retain explicit reapply and skip redundant claim persistence.
- ADR 0007 freezes this behavior. Recovery markers are idempotency metadata, not authentication. Version `0.2.2`, schema `1.0.0`, exact JSON keys, 105 achievements, 9 lessons, XP policy, catalog/assets, files-only permission, and disabled production networking are unchanged.
- PR #17 merged exact head `213babb6e29e023617a66600e4b9d8375ea466d9` as `396dda957908b26c94d73387bcddf14712a4c23c` after the Fast Gate and all Blender 5.0.1 / 5.1.2 / 5.2.0 source-smoke jobs succeeded.

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

PR #17 ran the exact reviewed head through GitHub Fast Gate and the blocking Blender 5.0.1, 5.1.2, and 5.2.0 source-smoke matrix; all checks completed successfully before merge. CI created and removed disposable per-job ZIP/install state; no canonical, retained, or published extension artifact was produced. The local machine still has no Blender 5.0 executable.

## Agents And Review

- A persistent component guardian holds the task contract, frozen invariants, no-real-data boundary, and session record.
- Independent reward test and Blender API reviewers have confirmed the expanded current-tree behavior with 0 Critical / 0 Important / 0 Low after nested-ID, rollback, and cross-version geo fixes.
- Explorer, code, dead-code, instruction-drift, verification, and lookahead reviews completed in waves. They found and closed exact shared-owner active-index rollback, compatibility-guard, handoff-guard, and live ADR-pointer gaps; final re-review is 0 Critical / 0 Important / 0 Low.
- Delivery verification independently checked the exact PR #17 base/head, four successful blocking jobs, merge method, and resulting `main` SHA before this closeout.
- The explicit `/review` fallback covered requirements, diff, checks, blockers, and residual risks because no callable slash command was available.

## Blockers

None for the merged source slice. PR #17 merged exact head `213babb6e29e023617a66600e4b9d8375ea466d9` into `main` as `396dda957908b26c94d73387bcddf14712a4c23c` after Fast Gate and Blender 5.0.1 / 5.1.2 / 5.2.0 succeeded. CI created and removed disposable per-job ZIP/install state; no tag, GitHub Release, version bump, production asset addition, canonical/retained/published extension artifact, or real `~/BlenderAchievements` access was performed.

## Residual Risks

- Witness recovery is scene/session local. A process crash can recover only when the marked `.blend` state survives; there is no cross-process reward journal.
- Concurrent Blender processes still share one JSON file and can overwrite each other last-writer-wins; multi-process coordination is a separate persistence task.
- Blender Undo does not reverse the external JSON claim; the claim proves a successful application event, while explicit reapply restores a removed scene result.
- `bpy.data.user_map()` delta cleanup assumes synchronous operator execution so unrelated IDs are not created inside the same action window.
- Production reward assets still require license approval and exact expected-datablock validation.
- Blender 5.0.1 behavior passed the blocking PR #17 matrix; Blender 5.0 is still unavailable locally, and future changes must retain that CI row.

## Next Start Prompt

Verify current `main` contains PR #17 head `213babb6e29e023617a66600e4b9d8375ea466d9`, merge `396dda957908b26c94d73387bcddf14712a4c23c`, and this containing handoff closeout before continuing. Do not redo reward claim atomicity. Take one separate task at a time; the recommended next task is a research-only specification for tutorial result verification and a defensible 90% threshold. Keep real `~/BlenderAchievements` untouched; any tag, GitHub Release, version bump, production asset publication, or cloud/auth change requires separate owner authorization.
