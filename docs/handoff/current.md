# Achievements — ACH-S0-001 Atomic Roadmap

## Goal

Maintain the governance-only `ACH-S0-001` roadmap at `docs/superpowers/plans/2026-08-03-achievements-0.3-roadmap.md` without treating this repository file as self-certifying merge evidence. The roadmap defines the one-task protocol, exact state machine, one-`target_repo` rule, role/review model, 76-card queue, assessment/content contracts, and excluded release placeholders. Canonical final task state and merge evidence live in the paired Second Brain only after declared target repository synchronization/readback—normal PR merge/readback or, solely for `ACH-STU-000`, audited repository creation/readback—and the mandatory second synchronization.

Current source identity remains `0.2.3`, an unpublished source candidate. ADR 0008 continues to govern the current lineage: Stage A full validation produces only ephemeral outputs and authorizes no retention, canonical artifact, or publication; Stage B needs separate explicit owner candidate-retention acceptance for one exact audited local candidate SHA, which remains non-canonical and not publication; Stage C needs separate explicit owner publication acceptance for `v0.2.3` and GitHub Release from that exact retained candidate. This session grants none. Historical PR #17 reward-claim atomicity remains a preserved prerequisite from `codex/reward-claim-atomicity`: exact head `213babb6e29e023617a66600e4b9d8375ea466d9`, base `origin/main@9cd26bd616c861578bc026a627c1796dddcac655`, and merge `396dda957908b26c94d73387bcddf14712a4c23c` are historical evidence, not the current task goal.

## Changed Files

The exact Stage 0 repository path allowlist is:

- Create/maintain: `docs/superpowers/plans/2026-08-03-achievements-0.3-roadmap.md`.
- Modify/maintain: `docs/handoff/current.md`.

No other repository path is in scope. No runtime, tests, ADRs, assets, release tooling, catalog, persistence, packaging, tag, GitHub Release, or Blender Extensions/Superhive publication surface changes under this task. `__init__.py`, `achievements/rewards.py`, `achievements/persistence.py`, schema `1.0.0`, the sole runtime, current files-only permission, XP `5/10/20`, cap `1550`, and disabled lesson runtime remain unchanged.

## Done

- The roadmap defines `queued → ready → active → verify → review → repo_sync → vault_sync → done`, with supplemental `blocked`, `excluded`, and `awaiting_owner`, and permits at most one active ID.
- Each card names one `target_repo` and changes at most that implementation repository. Add-on catalog, approved assessment JSON, and public-key registry remain canonical in `Gorgutc/Achivments_addon_blender`; Studio proposals/artifacts target private `Gorgutc/Achievements_studio`. Second Brain is always the second synchronization.
- The exact queue has 76 IDs: `ACH-S0-001`; `ACH-STU-000..006`; `ACH-OD-000..010`; `ACH-ADR-009/010`; `ACH-PKB-001..003`; `ACH-PACK-001..010`; 24 `ACH-CNT-{THEME}-{STARTER|BONUS}-{RIGHTS|CONTENT|ASSEMBLY}` cards; `ACH-ASMT-001..011`; and seven `ACH-X-*` placeholders.
- The final registry state after actual `ACH-S0-001` repository and vault closeout is defined as: `ACH-S0-001` done, `ACH-STU-000` awaiting owner, 67 cards queued, 7 cards excluded, and no active card. This repository handoff does not claim that final state has already been reached.
- Current `0.2.3` runtime remains `threshold_basis_points: null`, lesson-assessment persistence disabled, and reward bridge disabled. The owner-approved roadmap rules are future work executed through `ACH-OD-000..010`, followed by the mandatory post-`ACH-OD-010` owner gate; planned threshold, `+20` once per lesson, and cap `1730` do not exist in runtime until their exact tasks merge.
- GPL-covered add-on behavior remains free. Paid support, training, and `Superhive Standard Royalty-Free` bonus content add no DRM, login, telemetry, background entitlement, XP, or reward-claim advantage.
- Historical PR #17 **Reward Claim Atomicity** evidence is preserved unchanged: PR #17 merged exact head `213babb6e29e023617a66600e4b9d8375ea466d9` as `396dda957908b26c94d73387bcddf14712a4c23c`; its prospective claim and idempotent retry contract remain frozen by ADR 0007. The current schema `1.0.0`, sole runtime, and reward/persistence behavior are unchanged.

## Remaining

- Before `repo_sync`, root/reviewer must rerun the exact allowlist audit, new-file-aware whitespace check, direct roadmap semantic audit, existing verifier, targeted infrastructure tests, and required full gate. This handoff intentionally does not self-certify those final results.
- After the add-on PR merge and exact merge-SHA readback, the current `ACH-S0-001` vault phase must update canonical `1-Projects/Achivments_addon_blender/Improvements.md` and create `1-Projects/Achivments_addon_blender/References/achievements-0.3-task-contracts.md` with all 15 fields for all 76 records.
- Vault evidence must record the exact add-on PR, exact add-on merge SHA, and exact vault PR. `merge_evidence.vault_merge_sha: self` is allowed only in the self-referential vault commit; Git history and vault `main` readback establish the actual SHA. `ACH-S0-001` becomes done only after that readback and append-only memory update.
- Execute the fixed assessment contract through `ACH-OD-000..010`; after the single atomic `ACH-OD-010` proposal, stop at its mandatory owner gate before ADR or implementation work.
- Owner-input content remains future work: 219 licensed PNG files, 11 approved tutorial URLs, and 20 licensed reward `.blend` files. Predicate semantics, deeper fixtures, UI/GPU/handler decomposition, and production cloud remain separate owner decisions.
- All `ACH-X-*` cards remain target-version-unassigned and excluded. Current `0.2.3` ADR 0008 Stage A/B/C is unchanged; any future 0.3 release identity or dependency graph needs a separate owner task and ADR.
- Tag, GitHub Release, and selection of an exact `0.2.3` artifact remain blocked pending explicit owner ship acceptance.

## Verification

Required Stage 0 evidence, to be rerun by root/reviewer before `repo_sync`:

1. Confirm `git status --short` contains only the exact two-path allowlist.
2. Stage only those exact paths, then run the new-file-aware `git diff --cached --check`; do not rely on an unstaged `git diff --check` to inspect the new roadmap.
3. Run a direct static roadmap audit proving 76 unique IDs, 24 `ACH-CNT-*`, 7 `ACH-X-*`, no duplicate IDs, required markers/results, one `target_repo` per non-excluded card, required dependency edges, and an acyclic DAG.
4. Run `uv run python scripts/verify_codex_plugin.py` and targeted `uv run pytest tests/test_infra_scripts.py -q`.
5. Run the applicable full fast gate: `uv run python scripts/verify_frozen.py`, `uv run python scripts/verify_codex_plugin.py`, `uv run python scripts/verify_predicates.py`, `uv run ruff check .`, and `uv run pytest`.

The latest reported `verify_codex_plugin.py` result was **126/126 PASS**, but that verifier guards historical handoff/release facts and existing infrastructure invariants; it does **not** validate new roadmap IDs, semantics, results, dependencies, or DAG. Cached results and this prose are not final direct-roadmap evidence. Root/reviewer must rerun and record final outputs after exact staging before `repo_sync`.

Historical pre-ADR-0008 evidence remains unchanged: PR #17 ran the exact reviewed head through GitHub Fast Gate and the blocking Blender 5.0.1, Blender 5.1.2, and Blender 5.2.0 source-smoke matrix; all checks completed successfully before merge. CI created and removed disposable per-job ZIP/install state; no canonical, retained, or published extension artifact was produced. That historical evidence is not Stage 0 verification and is not 0.2.3 Blender-smoke evidence.

## Agents And Review

- Terra owns the bounded two-path documentation diff; future code cards require a TDD Terra writer with a focused failing test before implementation.
- Sol enforces one task/one target repository, coordinates independent requirements, diff/instruction, component/content, verification, and lookahead review waves, and requires fixes plus reruns for confirmed Critical/Important findings.
- The explicit `/review` fallback covers requirements, exact diff, checks, blockers, and residual risks because no callable slash command is available. A review conclusion is not merge or release evidence.
- Historical PR #17 review and Blender-matrix evidence remains historical only; it does not satisfy Stage 0 roadmap validation or a future assessment/release gate.

## Blockers

No technical blocker prevents source-candidate work. The documentation task remains gated by root/reviewer direct roadmap audit, exact staged allowlist verification, repository merge/readback, and the current `ACH-S0-001` vault phase. `ACH-STU-000` is not active; it becomes `awaiting_owner` only in the finalized vault registry. Current lesson assessment remains disabled. ADR 0008 still requires separate explicit owner candidate-retention acceptance for Stage B and separate explicit owner publication acceptance for Stage C. No production asset addition or real `~/BlenderAchievements` access is authorized. The historical `achievements-0.2.2.zip` is immutable pre-PR16 evidence only and is not a current artifact.

## Residual Risks

- Existing verification does not directly parse the new roadmap, so a dedicated static audit and independent review are mandatory before synchronization.
- Repository prose can drift from canonical task state; only the post-merge Second Brain registry/readback may finalize `done` evidence.
- Future pack network permission, assessment persistence, XP, and reward bridge work can conflict with current frozen behavior if started before their exact owner gates and ADRs.
- Rights evidence, static content production, signed assembly, and runtime consumption remain separate cards; collapsing them can hide license, integrity, or entitlement mistakes.
- Existing reward atomicity limitations remain: process-crash recovery depends on marked scene state; concurrent Blender processes share one JSON file last-writer-wins; Blender Undo does not reverse the external JSON claim; and `bpy.data.user_map()` cleanup assumes synchronous execution.

## Next Start Prompt

First read canonical final status/evidence from the paired Second Brain and verify the corresponding repository/vault merge facts. If `ACH-S0-001` is not done, continue the same ID through its missing review, repository, or vault step. If it is done, keep `active_task_id` null and wait for explicit owner authorization to start exact `ACH-STU-000`; do not infer a start from queue order. Revalidate target `main`, PRs, dirt, dependencies, handoff, and canonical backlog before any edit. The lesson-assessment specification remains a separate research-only slice, and current implementation remains disabled until the planned owner gate and ADR path complete. Keep real `~/BlenderAchievements` untouched; any retained candidate, canonical artifact, tag, GitHub Release, Blender Extensions publication, Superhive publication, production asset publication, or cloud/auth change requires explicit owner authorization.
