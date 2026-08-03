# Achievements 0.3 Atomic Roadmap Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement one explicitly owner-started card at a time. Each card uses the state machine and evidence rules below; checklist syntax is the task record, not proof that a task merged.

**Goal:** Establish a non-release, atomic delivery protocol and an owner-gated 0.3 queue for the GPL Blender add-on, Studio proposals, content, and future lesson assessment work.

**Architecture:** Every card declares one `target_repo` and changes at most that one implementation repository. The add-on repository remains canonical for runtime, catalog, approved assessment JSON, and the public-key registry; Studio cards merge in the private `Gorgutc/Achievements_studio` repository and may produce proposals/artifacts without replacing add-on truth or creating a second runtime. Only after the declared target repository synchronization/readback does the mandatory Second Brain synchronization run as the second sync. Here `synchronization/readback` means the normal PR merge/readback or, solely for `ACH-STU-000`, the audited repository-creation/readback exception below.

**Tech Stack:** Git/GitHub, Python and Blender 5.0+, `uv`, existing repository verifiers, Markdown, and the paired Second Brain vault.

## Global Constraints

- This Stage 0 task is governance/documentation only. It must not alter runtime code, tests, assets, ADRs, packaging, tags, releases, or real `~/BlenderAchievements` data.
- The current add-on source identity is `0.2.3`; it remains an unpublished source candidate. ADR 0008 keeps Stage A, Stage B, and Stage C separately owner-gated.
- The frozen baseline remains files-only, with XP cap `1550` and lesson runtime disabled. Network access, a one-time `+20` XP lesson reward, and cap `1730` are future proposals, not current behavior.
- The current GPL-covered add-on remains free. Commercial value is paid support, training, and separately licensed content; the product has no DRM, account or login requirement, telemetry, background entitlement, authentication, or network permission.
- Catalog data is canonical only in this add-on repository. Studio holds proposals/artifacts only. Approved assessment JSON and the public-key registry also belong in this repository.
- The executor does not choose a production domain, the exact production signing-key fingerprint, real tutorial URLs, or content assets. Each requires its own explicit owner approval before the dependent card may proceed.
- A card may change at most one implementation repository named by `target_repo`; its later Second Brain synchronization records the target-repository result and is never treated as a second implementation target.
- The planned registry contains exactly 76 cards: 1 Stage 0, 7 Studio, 11 owner-decision, 2 ADR, 3 pack-builder tooling, 10 pack, 24 content, 11 assessment, and 7 excluded-release cards. An ID is immutable once accepted; a changed result gets a new ID with an explicit `supersedes` relation.
- One task ID may be active at a time. An incomplete task keeps its ID and is recorded as WIP/Draft; it is never replaced by a stacked PR or silently renumbered.
- A Second Brain note may describe a proposal before the declared target repository synchronization/readback, but it cannot finalize the corresponding contract or evidence until the declared target repository synchronization/readback is complete.
- Every card must preserve the existing extension namespace, files-only permission, local-first persistence boundary, and the retired-duplicate rule for `achievements_v01 (4).py` unless a separate owner-approved task explicitly changes a governed contract.

---

## Stage 0 Scope And Completion Contract

`ACH-S0-001` creates this roadmap and refreshes the operational handoff. It establishes process and does not implement a Studio feature, content item, assessment evaluator, XP change, network feature, release candidate, or publication.

The following is the **target state only after an actual add-on repository merge/readback, the subsequent vault synchronization/readback, and the append-only memory note**, not evidence that this worktree has already merged or completed either later step:

```text
completed_task_id: ACH-S0-001
active_task_id: null
next_candidate_id: ACH-STU-000
next_candidate_status: awaiting_owner
done_count: 1
awaiting_owner_count: 1
queued_count: 67
excluded_count: 7
active_count: 0
```

Stage 0 is complete only when the roadmap/handoff diff has passed its required checks, received the required review, completed repository synchronization and readback, and then completed the required vault synchronization and readback. No stage is inferred from a green local command, a branch name, or a draft document.

## Artifact And Authority Map

| Surface | Authority | Required rule |
| --- | --- | --- |
| Add-on repository catalog | Canonical product/catalog data | Future catalog changes are reviewed here and never sourced from a Studio copy. |
| Add-on repository assessment JSON and public-key registry | Canonical approved assessment contract | Proposal drafts cannot become runtime inputs without the relevant owner decision, ADR, tests, merge, and readback. |
| Studio | Proposals, editorial assets, and production artifacts | Studio has no authority to create a second runtime, alter catalog truth, or grant entitlement. |
| Second Brain | Cross-repository traceability and handoff | It records completed facts only after the declared target repository synchronization/readback; before then its handoff status is `active` or `blocked`. |
| Release surfaces | ADR 0008 owner gates | They are not part of this roadmap queue and cannot be bundled with any card below. |

## One-Task Delivery Protocol

Every queued card follows this exact sequence. A later item cannot start merely because an earlier card has a branch, a WIP commit, a draft PR, or a locally green test.

1. **Explicit owner start.** The owner starts one exact ID, for example `ACH-STU-000`. The start message fixes the task ID, desired result, allowed paths, and any owner decisions being supplied. A coordinator must not infer authorization from a roadmap position.
2. **Live intake.** Revalidate the default branch/head, open PR list, worktree dirt, dependency/tool availability, active handoff, and canonical backlog. Record the observed baseline in the task evidence. If the requested work depends on a missing owner decision, place that same ID in `awaiting_owner` or `blocked` rather than substituting a different card.
3. **Isolation.** Except solely for the `ACH-STU-000` repository bootstrap exception below, create or reuse only `codex/<id>-<slug>` from the revalidated base. The worktree contains one task; no stacked PR and no unrelated cleanup is permitted. No other card may use the bootstrap exception.
4. **Task contract.** State the one deliverable, explicit out-of-scope areas, exact allowed file paths, required evidence, required reviewers, and completion predicate before editing. For code cards, also name the failing test and smoke coverage before implementation.
5. **Implementation or research.** A Terra writer owns the bounded work. Code cards use TDD: write the focused failing test, demonstrate the failure, make the smallest passing change, rerun the focused test, then run the relevant static and integration checks. Governance/research/content cards produce only their stated evidence artifact and do not smuggle runtime behavior into a documentation change.
6. **Verification.** Run the applicable repository verifiers and fast Python checks. A code/runtime/packaging card also runs the appropriate disposable-profile Blender smoke coverage when Blender is available. A missing tool is recorded as evidence gap, not silently converted into a pass.
7. **Review waves.** Sol orchestrates independent review after verification: requirements/scope, changed-file/diff and instruction drift, then component/dead-code/verification/lookahead review appropriate to the card. Confirmed Critical or Important findings are fixed and reverified before synchronization.
8. **Repository synchronization.** Only after the review gate, perform target commit, push, PR, merge, and readback for the one card. The readback records exact base/head/merge facts and the real CI result. `ACH-STU-000` alone replaces the pre-existing-repository branch/PR/merge sequence with the audited initial private-repository creation and readback defined below; all later Studio cards and every other card use the normal sequence. WIP/Draft is acceptable when unfinished, but it remains the same ID and does not permit another task to start.
9. **Vault synchronization.** Only after the declared target repository synchronization/readback, synchronize the required Second Brain living surfaces, session/handoff, canonical backlog, and evidence. Merge and read back the vault change separately. Before this point, the vault handoff is `active` or `blocked`, not a completed contract.
10. **Memory and stop.** Append the approved session memory note after both repository and vault readbacks, report residual risks and next candidate, clear `active_task_id` only for a completed task, then STOP. No follow-on card starts automatically.

### `ACH-STU-000` repository bootstrap exception

This exception applies only after the owner explicitly starts `ACH-STU-000`. Live intake must use authoritative account/connector readback to prove that `Gorgutc/Achievements_studio` does not already exist, verify authority to create it as a private repository, and record that no existing branch or PR exists; because the repository is absent, no pre-existing base or worktree is possible. If the repository already exists or any authority/existence fact is uncertain, STOP without creating or mutating it and return the discrepancy to the owner.

Create the private repository and seed its initial `main`, then read back exact privacy, default branch `main`, no added/outside collaborators or teams beyond the repository owner's implicit admin access, no secrets, no keys, and no releases. That initial repository creation, initial-`main` seed, and readback are this task's sole `repo_sync` exception because a PR cannot precede repository existence. Every later Studio card uses the normal `codex/<id>-<slug>` branch/worktree, PR, merge, and readback protocol. Second Brain synchronization, append-only memory, and STOP remain mandatory for `ACH-STU-000`.

## State Machine

The only normal delivery path is exactly:

```text
queued → ready → active → verify → review → repo_sync → vault_sync → done
```

`blocked`, `excluded`, and `awaiting_owner` are the only supplemental hold/terminal states.

| State | Entry condition | Required exit evidence |
| --- | --- | --- |
| `queued` | The roadmap names a card but the owner has not started it. | Exact owner start moves it to `ready`. |
| `ready` | Owner supplied the exact card and scope is intelligible. | Normal live intake plus one isolated branch/worktree move the card to `active`; solely for `ACH-STU-000`, authoritative absent-repository live intake plus the bootstrap task contract under the named exception do so. |
| `active` | At most one active card exists and owns either one isolated worktree or, solely for `ACH-STU-000`, the single audited repository-creation operation. | Its stated result and evidence exist; then enter `verify`. |
| `verify` | Editing/research is complete enough to check. | Required commands, tests, and applicable smoke evidence pass or record a real gap. |
| `review` | Verification evidence is available. | Required review waves resolve confirmed findings. |
| `repo_sync` | Review is accepted for this card. | Normal cards use commit, push, PR, merge, and declared target repository readback to identify actual SHA/CI facts; solely `ACH-STU-000` satisfies `repo_sync` through audited private-repository creation plus readback of the exact initial-`main` SHA, privacy, default branch, no added/outside collaborators or teams beyond the repository owner's implicit admin access, no secrets, no keys, and no releases under the named repository bootstrap exception. |
| `vault_sync` | The declared target repository synchronization/readback proves repository synchronization. | Required Second Brain merge/readback records only the verified facts. |
| `done` | Both synchronization readbacks and memory append are complete. | Set `active_task_id: null`; name one `awaiting_owner` next candidate; STOP. |
| `blocked` | The same ID cannot progress because a concrete external fact or decision is missing. | The owner supplies the missing condition; resume the same ID. |
| `excluded` | A requested activity is explicitly outside this roadmap or current owner authorization. | It needs a separately owner-started task, not a workaround. |
| `awaiting_owner` | A specific owner decision/start is required before any safe work begins. | Explicit owner input moves the same ID to `ready`. |

## Roles, Tests, And Review Expectations

- **Terra writer:** owns the one-card contract, bounded edits, TDD for code cards, relevant checks, and truthful evidence. Terra does not claim a merge, release, or owner acceptance without readback.
- **Sol orchestrator/reviewer:** keeps the one-task boundary, schedules review waves, checks live status, and rejects additive release or entitlement authority.
- **Requirements guardian:** remains active through a broad card; it checks allowed paths, frozen facts, baseline values, owner gates, and completion evidence.
- **Independent reviewers:** review the actual diff and evidence, not a description of it. Their waves cover requirements, code/component or content correctness, dead-code/instruction drift when applicable, verification, and lookahead/residual risk.
- **Code-card test sequence:** focused failing test → focused passing test → relevant static verifier → relevant `uv run pytest` scope → Blender smoke in temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES` when the card touches Blender/runtime/packaging behavior.
- **Documentation/content-card test sequence:** path allowlist → link/schema/provenance checks relevant to the card → `git diff --check` → applicable repository verifier → review. Documentation cannot declare an unperformed runtime or publication result.

## Product And Assessment Boundaries

### Fixed assessment rules for every future lesson card

The nine lesson cards below use this exact planned contract until a separately owner-approved ADR changes it:

1. The assessed root is `Assessment Collection`; evaluation accepts an otherwise arbitrary scene and follows the recursive dependency closure from that collection.
2. Extra scene content is allowed unless an explicit rule forbids it.
3. Selectors use structural relationships; datablock names and collection/order position are insignificant by default.
4. Exactly one current attempt is evaluated, and any cross-scope operation blocks a pass.
5. Event evidence contains only the minimum semantic event; it contains no filesystem paths and no scene dump.
6. The planned threshold is `min_positive_score * 10` basis points only when calibration proves a nonzero positive/negative gap. Current `0.2.3` runtime remains `threshold_basis_points: null`, lesson persistence disabled, and reward bridge disabled until the separately authorized tasks actually merge.
7. Every assessment version has 20 independent holdouts split `7/7/6` across Blender 5.0.1, 5.1.2, and 5.2.0.
8. Acceptance requires 0 adversarial false positives, 0 canonical false negatives, and at most 1 equivalence false negative after explicit owner disposition.
9. The learner receives a Russian, rule-by-rule result with score, mandatory-gate failures, accepted equivalences, and actionable differences.

### Content taxonomy and commercial boundary

- Themes: `modeling_foundations`, `lookdev_render`, `geometry_nodes`, and `workflow`.
- Tiers: **free starter** and **paid bonus**.
- Every content package has three separately owner-started, separately reviewable atomic cards: `RIGHTS` (license/provenance evidence), `CONTENT` (editorial/tutorial/asset result), and `ASSEMBLY` (repository/package-ready integration and validation). A `CONTENT` result never substitutes for rights evidence; an `ASSEMBLY` result never supplies missing rights.
- The paid tier sells support/training/content value compatible with GPL redistribution of the add-on. It does not gate use of the add-on or add DRM, login, telemetry, or a hosted entitlement service.

### Future lesson-runtime boundary

If and only if later owner decisions and ADRs authorize implementation, the proposed lesson policy is `+20` XP exactly once per completed lesson, with a resulting cap of `1730`. That future contract requires its own TDD, migration/persistence decision, compatibility review, and Blender smoke coverage. It is not implemented by this roadmap and it does not modify the current cap `1550` or disabled lesson runtime.

### Registry handoff boundary

This Markdown queue is the compact Stage 0 proposal, not the canonical 15-field registry. After the add-on PR is merged and its exact merge SHA is read back, the **current `ACH-S0-001` vault phase** must update canonical `1-Projects/Achivments_addon_blender/Improvements.md` and create `1-Projects/Achivments_addon_blender/References/achievements-0.3-task-contracts.md` with all 15 required fields for all 76 records: `id`, `status`, `phase`, `target_repo`, `depends_on`, `allowed_paths`, `deliverable`, `out_of_scope`, `acceptance`, `verification`, `required_reviews`, `owner_gate_before`, `owner_gate_after`, `stop_conditions`, and `merge_evidence`. This work belongs to `ACH-S0-001`, not `ACH-PKB-003`.

The vault record must carry the exact add-on PR, exact add-on merge SHA, and exact vault PR. Because the vault commit cannot contain its own eventual SHA, `merge_evidence.vault_merge_sha: self` is allowed only inside that self-referential vault commit; the actual SHA is established by Git history and vault `main` readback. `ACH-S0-001` reaches `done` only after that vault-main readback and the append-only memory note are complete.

## Task Queue

Each row below is a planned result, not an implementation claim. The 76 IDs are the expected registry set. Every normal card begins at `queued` and needs an explicit owner start; excluded cards remain `excluded`. Dependencies describe ordering, not implicit permission.

### Stage 0 governance

| ID | `target_repo` | Planned result | Dependency |
| --- | --- | --- | --- |
| `ACH-S0-001` | `Gorgutc/Achivments_addon_blender` | This atomic roadmap, a truthful current handoff, the one-task protocol, ownership boundaries, state machine, future queue, and explicit exclusions. | Owner start for Stage 0; no runtime or vault write in the worktree phase. |

### Studio queue — `ACH-STU-000` through `ACH-STU-006`

| ID | `target_repo` | Planned result | Dependency / non-authorization |
| --- | --- | --- | --- |
| `ACH-STU-000` | `Gorgutc/Achievements_studio` | Create the private repository and its initial `main`; permit no added/outside collaborators or teams beyond the repository owner's implicit admin access, and add no secrets, keys, or releases. | `ACH-S0-001` merge/readback; then `awaiting_owner` plus `OG-STUDIO-START`. |
| `ACH-STU-001` | `Gorgutc/Achievements_studio` | Add the Blender 5.2 extension foundation, pure domain schema, and fast CI. | `ACH-STU-000` repository synchronization/readback. |
| `ACH-STU-002` | `Gorgutc/Achievements_studio` | Add a read-only AST adapter for canonical add-on `catalog.py`, without importing it or writing to the add-on repository. | `ACH-STU-001` merge/readback. |
| `ACH-STU-003` | `Gorgutc/Achievements_studio` | Add the deterministic atomic proposal/draft engine, JSON schema, and stale-base rejection. | `ACH-STU-002` merge/readback. |
| `ACH-STU-004` | `Gorgutc/Achievements_studio` | Add standard Blender UI for source selection, safe editable fields, validation, and save/export. | `ACH-STU-003` merge/readback. |
| `ACH-STU-005` | `Gorgutc/Achievements_studio` | Add the advanced editor, session unlock, and exhaustive impact classification. | `ACH-STU-004` merge/readback; no production key is introduced. |
| `ACH-STU-006` | `Gorgutc/Achievements_studio` | Add the assessment-draft editor and end-to-end catalog-plus-assessment proposal flow. | `ACH-STU-005` merge/readback; downstream work still needs its exact owner start. |

### Owner-decision and lesson-card queue — `ACH-OD-000` through `ACH-OD-010`

| ID | `target_repo` | Planned result | Dependency / non-authorization |
| --- | --- | --- | --- |
| `ACH-OD-000` | `Gorgutc/Achievements_studio` | Freeze the common nine-lesson assessment contract above and add a research-only calibration harness. | `ACH-STU-006` merge/readback; no runtime implementation authority. |
| `ACH-OD-001` | `Gorgutc/Achievements_studio` | Exact `lesson_vertices_basics` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-002` | `Gorgutc/Achievements_studio` | Exact `lesson_edit_basics` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-003` | `Gorgutc/Achievements_studio` | Exact `lesson_edges` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-004` | `Gorgutc/Achievements_studio` | Exact `lesson_faces` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-005` | `Gorgutc/Achievements_studio` | Exact `lesson_modeling` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-006` | `Gorgutc/Achievements_studio` | Exact `lesson_materials` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-007` | `Gorgutc/Achievements_studio` | Exact `lesson_time_management` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-008` | `Gorgutc/Achievements_studio` | Exact `lesson_geo_nodes_intro` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-009` | `Gorgutc/Achievements_studio` | Exact `lesson_render_basics` card, fixtures, holdouts, and calibration evidence. | `ACH-OD-000` merge/readback. |
| `ACH-OD-010` | `Gorgutc/Achievements_studio` | Produce one atomic assessment proposal from the common contract and all nine exact cards. | All `ACH-OD-001..009` merge/readbacks; mandatory `OG-OD-FINAL` owner gate before `ACH-ADR-009`. |

### ADR queue — `ACH-ADR-009` and `ACH-ADR-010`

| ID | `target_repo` | Planned result | Dependency / non-authorization |
| --- | --- | --- | --- |
| `ACH-ADR-009` | `Gorgutc/Achivments_addon_blender` | Accept the signed-pack and GPL-compatible commercial boundary, exact permissions, signing-key lifecycle, and pack-delivery contract. | `ACH-OD-010` merge/readback plus mandatory `OG-OD-FINAL`; no implementation or release action. |
| `ACH-ADR-010` | `Gorgutc/Achivments_addon_blender` | Accept the assessment persistence, XP, reward bridge, privacy, and implementation contract. | `ACH-ADR-009` merge/readback plus `OG-ADR-ACCEPT`; current `0.2.3` behavior remains unchanged until later tasks merge. |

### Product knowledge base queue — `ACH-PKB-001` through `ACH-PKB-003`

| ID | `target_repo` | Planned result | Dependency / non-authorization |
| --- | --- | --- | --- |
| `ACH-PKB-001` | `Gorgutc/Achievements_studio` | Strict pack manifest and deterministic `.achpack` builder. | `ACH-ADR-010` merge/readback plus `OG-PKB-START`. |
| `ACH-PKB-002` | `Gorgutc/Achievements_studio` | Static `.blend`, MP4, catalog, and license audit pipeline. | `ACH-PKB-001` merge/readback. |
| `ACH-PKB-003` | `Gorgutc/Achievements_studio` | Ed25519 signer, encrypted PKCS#8 workflow, and signing provenance. | `ACH-PKB-002` merge/readback. Production-key use needs separate approval of one exact fingerprint; the key is never stored in a repository, `.blend`, Blender Preferences, or CI. |

### Pack tooling queue — `ACH-PACK-001` through `ACH-PACK-010`

All local-file and HTTPS inputs enter the same signature, approved-key, manifest, hash, archive-safety, and transactional-store trust pipeline. Future HTTPS access is conditioned on exact `bpy.app.online_access`. Starter packs use an approved public URL. Paid packs arrive through a local file or an expiring URL held in memory only; the URL is never persisted and never becomes entitlement state. Blender 5.2 Remote Asset Library is a public storefront, never an entitlement service or a trusted claim source. Any bundled Python dependency is shipped as an audited wheel; runtime `pip` installation and package download are forbidden.

The future manifest permission descriptions are exact: `files = "Store progress and install signed reward packs"` and `network = "Download signed reward packs selected by the user"`. `network` and `bpy.app.online_access` remain absent from current `0.2.3` and can appear only through the explicit `ACH-PACK-008` contract.

| ID | `target_repo` | Planned result | Dependency / frozen boundary |
| --- | --- | --- | --- |
| `ACH-PACK-001` | `Gorgutc/Achivments_addon_blender` | Strict pack-manifest parser and signed positive/negative fixtures. | `ACH-PKB-003`, `ACH-ADR-009`, and `OG-PACK-START`. |
| `ACH-PACK-002` | `Gorgutc/Achivments_addon_blender` | Ed25519 verifier and canonical approved public-key registry. | `ACH-PACK-001` merge/readback; add-on repository owns the registry. |
| `ACH-PACK-003` | `Gorgutc/Achivments_addon_blender` | Archive-safety preflight with limits, containment/path/collision/zip-bomb defenses, and complete streamed hash verification. | `ACH-PACK-002` merge/readback. |
| `ACH-PACK-004` | `Gorgutc/Achivments_addon_blender` | Transactional immutable pack store with staging, idempotent install/update, equivocation rejection, rollback, and crash recovery. | `ACH-PACK-003` merge/readback. |
| `ACH-PACK-005` | `Gorgutc/Achivments_addon_blender` | Explicit local-file installer over the common verified-store pipeline. | `ACH-PACK-004` merge/readback; no background downloader. |
| `ACH-PACK-006` | `Gorgutc/Achivments_addon_blender` | Exact free-starter reward resolver preserving ADR 0007 claim-after-apply and retryable-unclaimed semantics. | `ACH-PACK-005` merge/readback. |
| `ACH-PACK-007` | `Gorgutc/Achivments_addon_blender` | Verified Local Asset Library connection, browser-only logical active pointer, and guarded safe removal without progress/claim deletion. | `ACH-PACK-006` merge/readback. |
| `ACH-PACK-008` | `Gorgutc/Achivments_addon_blender` | Explicit HTTPS transport conditioned on exact `bpy.app.online_access`, with exact new permissions, approved host policy, stream cap, and the common trust pipeline. | `ACH-PACK-007` merge/readback plus separate network/permission and production-domain owner approval. |
| `ACH-PACK-009` | `Gorgutc/Achivments_addon_blender` | Disabled Remote Library seam pending a separately approved endpoint contract. | `ACH-PACK-008` merge/readback; no endpoint, polling, login, or background entitlement. |
| `ACH-PACK-010` | `Gorgutc/Achivments_addon_blender` | Adversarial integration and `0.3.0` source-readiness evidence. | `ACH-PACK-009` merge/readback; source-readiness is not a retained candidate, release identity, tag, or publication. |

### Content queue — 24 exact `ACH-CNT-*` cards

`STARTER` and `BONUS` are stable identifier tiers, not price claims: `access` is respectively `free` and `paid`. Every `RIGHTS` card freezes exact manifest IDs, asset IDs, and provenance; every `CONTENT` card produces static `.blend`, MP4, previews, and license files; every `ASSEMBLY` card produces a deterministic signed artifact plus verification evidence. All starter artifacts use `CC0-1.0`. All bonus artifacts use `Superhive Standard Royalty-Free` and never affect XP or reward claims.

| ID | `target_repo` | Access | Planned result | Dependency |
| --- | --- | --- | --- | --- |
| `ACH-CNT-MODELING-FOUNDATIONS-STARTER-RIGHTS` | `Gorgutc/Achievements_studio` | `free` | Freeze exact manifest IDs, asset IDs, and provenance under `CC0-1.0`. | `ACH-ADR-009` and `OG-RIGHTS-MODELING-FOUNDATIONS-STARTER`. |
| `ACH-CNT-MODELING-FOUNDATIONS-STARTER-CONTENT` | `Gorgutc/Achievements_studio` | `free` | Produce static `.blend`, MP4, previews, and licenses under `CC0-1.0`. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-MODELING-FOUNDATIONS-STARTER-ASSEMBLY` | `Gorgutc/Achievements_studio` | `free` | Produce the deterministic signed artifact and verification evidence under `CC0-1.0`. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |
| `ACH-CNT-MODELING-FOUNDATIONS-BONUS-RIGHTS` | `Gorgutc/Achievements_studio` | `paid` | Freeze exact manifest IDs, asset IDs, and provenance under `Superhive Standard Royalty-Free`; no XP/claim effect. | `ACH-ADR-009` and `OG-RIGHTS-MODELING-FOUNDATIONS-BONUS`. |
| `ACH-CNT-MODELING-FOUNDATIONS-BONUS-CONTENT` | `Gorgutc/Achievements_studio` | `paid` | Produce static `.blend`, MP4, previews, and licenses under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-MODELING-FOUNDATIONS-BONUS-ASSEMBLY` | `Gorgutc/Achievements_studio` | `paid` | Produce the deterministic signed artifact and verification evidence under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |
| `ACH-CNT-LOOKDEV-RENDER-STARTER-RIGHTS` | `Gorgutc/Achievements_studio` | `free` | Freeze exact manifest IDs, asset IDs, and provenance under `CC0-1.0`. | `ACH-ADR-009` and `OG-RIGHTS-LOOKDEV-RENDER-STARTER`. |
| `ACH-CNT-LOOKDEV-RENDER-STARTER-CONTENT` | `Gorgutc/Achievements_studio` | `free` | Produce static `.blend`, MP4, previews, and licenses under `CC0-1.0`. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-LOOKDEV-RENDER-STARTER-ASSEMBLY` | `Gorgutc/Achievements_studio` | `free` | Produce the deterministic signed artifact and verification evidence under `CC0-1.0`. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |
| `ACH-CNT-LOOKDEV-RENDER-BONUS-RIGHTS` | `Gorgutc/Achievements_studio` | `paid` | Freeze exact manifest IDs, asset IDs, and provenance under `Superhive Standard Royalty-Free`; no XP/claim effect. | `ACH-ADR-009` and `OG-RIGHTS-LOOKDEV-RENDER-BONUS`. |
| `ACH-CNT-LOOKDEV-RENDER-BONUS-CONTENT` | `Gorgutc/Achievements_studio` | `paid` | Produce static `.blend`, MP4, previews, and licenses under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-LOOKDEV-RENDER-BONUS-ASSEMBLY` | `Gorgutc/Achievements_studio` | `paid` | Produce the deterministic signed artifact and verification evidence under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |
| `ACH-CNT-GEOMETRY-NODES-STARTER-RIGHTS` | `Gorgutc/Achievements_studio` | `free` | Freeze exact manifest IDs, asset IDs, and provenance under `CC0-1.0`. | `ACH-ADR-009` and `OG-RIGHTS-GEOMETRY-NODES-STARTER`. |
| `ACH-CNT-GEOMETRY-NODES-STARTER-CONTENT` | `Gorgutc/Achievements_studio` | `free` | Produce static `.blend`, MP4, previews, and licenses under `CC0-1.0`. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-GEOMETRY-NODES-STARTER-ASSEMBLY` | `Gorgutc/Achievements_studio` | `free` | Produce the deterministic signed artifact and verification evidence under `CC0-1.0`. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |
| `ACH-CNT-GEOMETRY-NODES-BONUS-RIGHTS` | `Gorgutc/Achievements_studio` | `paid` | Freeze exact manifest IDs, asset IDs, and provenance under `Superhive Standard Royalty-Free`; no XP/claim effect. | `ACH-ADR-009` and `OG-RIGHTS-GEOMETRY-NODES-BONUS`. |
| `ACH-CNT-GEOMETRY-NODES-BONUS-CONTENT` | `Gorgutc/Achievements_studio` | `paid` | Produce static `.blend`, MP4, previews, and licenses under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-GEOMETRY-NODES-BONUS-ASSEMBLY` | `Gorgutc/Achievements_studio` | `paid` | Produce the deterministic signed artifact and verification evidence under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |
| `ACH-CNT-WORKFLOW-STARTER-RIGHTS` | `Gorgutc/Achievements_studio` | `free` | Freeze exact manifest IDs, asset IDs, and provenance under `CC0-1.0`. | `ACH-ADR-009` and `OG-RIGHTS-WORKFLOW-STARTER`. |
| `ACH-CNT-WORKFLOW-STARTER-CONTENT` | `Gorgutc/Achievements_studio` | `free` | Produce static `.blend`, MP4, previews, and licenses under `CC0-1.0`. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-WORKFLOW-STARTER-ASSEMBLY` | `Gorgutc/Achievements_studio` | `free` | Produce the deterministic signed artifact and verification evidence under `CC0-1.0`. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |
| `ACH-CNT-WORKFLOW-BONUS-RIGHTS` | `Gorgutc/Achievements_studio` | `paid` | Freeze exact manifest IDs, asset IDs, and provenance under `Superhive Standard Royalty-Free`; no XP/claim effect. | `ACH-ADR-009` and `OG-RIGHTS-WORKFLOW-BONUS`. |
| `ACH-CNT-WORKFLOW-BONUS-CONTENT` | `Gorgutc/Achievements_studio` | `paid` | Produce static `.blend`, MP4, previews, and licenses under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `RIGHTS` merge/readback. |
| `ACH-CNT-WORKFLOW-BONUS-ASSEMBLY` | `Gorgutc/Achievements_studio` | `paid` | Produce the deterministic signed artifact and verification evidence under `Superhive Standard Royalty-Free`; no XP/claim effect. | Matching `CONTENT` and `ACH-PKB-003` merge/readback. |

### Future assessment implementation queue — `ACH-ASMT-001` through `ACH-ASMT-011`

All `ACH-ASMT-*` cards target `Gorgutc/Achivments_addon_blender` and remain `queued` until their dependencies complete and the owner explicitly starts the exact next card; `OG-ASMT-START` is an entry condition, not permission to activate the whole family. Pack implementation requires Blender 5.2; assessment/XP work preserves Blender 5.0.1 and 5.1.2 support, with final cross-version coverage also including Blender 5.2.0.

The separate assessment store paths are exact and tests/smoke must redirect them through disposable profiles:

```text
~/BlenderAchievements/lesson_assessment/state.json
~/BlenderAchievements/lesson_assessment/attempts/<attempt_id>.json
~/BlenderAchievements/lesson_assessment/events/<attempt_id>.jsonl
~/BlenderAchievements/lesson_assessment/.writer.lock
```

| ID | `target_repo` | Planned result after authorization | Dependency / frozen boundary |
| --- | --- | --- | --- |
| `ACH-ASMT-001` | `Gorgutc/Achivments_addon_blender` | Canonical assessment JSON schema, strict loader, and deterministic digest. | `ACH-ADR-010` and `OG-ASMT-START`; add-on repository owns approved JSON. |
| `ACH-ASMT-002` | `Gorgutc/Achivments_addon_blender` | Normalized feature graph and deterministic comparison primitives. | `ACH-ASMT-001` merge/readback. |
| `ACH-ASMT-003` | `Gorgutc/Achivments_addon_blender` | Basis-points score, Russian rule-by-rule explanation, and calibration logic. | `ACH-ASMT-002` merge/readback; a null threshold cannot pass. |
| `ACH-ASMT-004` | `Gorgutc/Achivments_addon_blender` | Blender-facing read-only evidence adapter while the pure comparison engine remains `bpy`-free. | `ACH-ASMT-003` merge/readback. |
| `ACH-ASMT-005` | `Gorgutc/Achivments_addon_blender` | Read-only Submit Result UI with score, rule explanations, and errors. | `ACH-ASMT-004` merge/readback; no persistence/XP/reward mutation yet. |
| `ACH-ASMT-006` | `Gorgutc/Achivments_addon_blender` | Separate assessment store at the exact paths above with atomic writes and a single-writer `.writer.lock` lease. | `ACH-ASMT-005` merge/readback. |
| `ACH-ASMT-007` | `Gorgutc/Achivments_addon_blender` | Attempts/events plus latest, best, and stale lifecycle semantics. | `ACH-ASMT-006` merge/readback. |
| `ACH-ASMT-008` | `Gorgutc/Achivments_addon_blender` | Grant `+20` XP exactly once per passed lesson and raise the reachable cap to `1730`. | `ACH-ASMT-007` merge/readback; current `1550` remains until this task merges. |
| `ACH-ASMT-009` | `Gorgutc/Achivments_addon_blender` | Pending/free-starter reward bridge preserving ADR 0007 claim-after-apply and retryable-unclaimed behavior. | `ACH-ASMT-008` and `ACH-PACK-006` merge/readbacks. |
| `ACH-ASMT-010` | `Gorgutc/Achivments_addon_blender` | Local MP4 playback, URL fallback, pack controls, and explicit Reset Lessons. | `ACH-ASMT-009` plus `ACH-PACK-007`; `ACH-PACK-008`/`ACH-PACK-009` only when the approved URL/remote scope requires them. |
| `ACH-ASMT-011` | `Gorgutc/Achivments_addon_blender` | Nine-lesson adversarial integration and Blender 5.0.1/5.1.2/5.2.0 matrix. | `ACH-ASMT-010` merge/readback only; `ACH-PACK-010` remains an independent pack source-readiness task and is not a dependency; no release/publication action. |

## Explicitly Excluded Release Cards

These seven cards are target-version-unassigned placeholders and remain `excluded`. They do not alter or extend the current `0.2.3` ADR 0008 lineage: its Stage A/B/C gates remain unchanged and none is granted here. Any future 0.3 release identity, dependency graph, retained candidate, or publication contract needs a separate explicit owner task and ADR before an `ACH-X-*` placeholder can be reconsidered.

| ID | `target_repo` | `target_version` | State | Exclusion reason and future-only dependency |
| --- | --- | --- | --- | --- |
| `ACH-X-STAGE-A` | `Gorgutc/Achivments_addon_blender` | `unassigned` | `excluded` | No implementation dependency. Requires a separate exact target-identity/release-contract task, `OG-STAGE-A`, and a separate owner start. |
| `ACH-X-STAGE-B` | `Gorgutc/Achivments_addon_blender` | `unassigned` | `excluded` | Future-only dependency `ACH-X-STAGE-A`, plus `OG-STAGE-B` and a separate owner start. |
| `ACH-X-STAGE-C` | `Gorgutc/Achivments_addon_blender` | `unassigned` | `excluded` | Future-only dependency `ACH-X-STAGE-B`, plus `OG-STAGE-C` and a separate owner start. |
| `ACH-X-TAG` | `Gorgutc/Achivments_addon_blender` | `unassigned` | `excluded` | Future-only dependency `ACH-X-STAGE-C`, plus `OG-TAG` and a separate owner start. |
| `ACH-X-GITHUB-RELEASE` | `Gorgutc/Achivments_addon_blender` | `unassigned` | `excluded` | Future-only dependency `ACH-X-TAG`, plus `OG-GITHUB-RELEASE` and a separate owner start. |
| `ACH-X-BLENDER-EXTENSIONS` | `Gorgutc/Achivments_addon_blender` | `unassigned` | `excluded` | Future-only dependency `ACH-X-GITHUB-RELEASE`, plus `OG-BLENDER-EXTENSIONS` and a separate owner start. |
| `ACH-X-SUPERHIVE` | `Gorgutc/Achivments_addon_blender` | `unassigned` | `excluded` | Future-only dependency `ACH-X-GITHUB-RELEASE`, plus `OG-SUPERHIVE` and a separate owner start. |

## Execution Handoff

No card starts automatically from this document. After actual completion of `ACH-S0-001` repository and vault synchronization, the next candidate is `ACH-STU-000` with status `awaiting_owner`. The owner must explicitly start that exact ID; the first worker then reruns live intake instead of trusting this roadmap as live merge evidence.

## Self-Review Checklist

- [x] The normal state sequence is exactly `queued → ready → active → verify → review → repo_sync → vault_sync → done`.
- [x] `blocked`, `excluded`, and `awaiting_owner` are named without adding another state.
- [x] The exact 76-card queue covers `ACH-S0-001`, `ACH-STU-000..006`, `ACH-OD-000..010`, `ACH-ADR-009/010`, `ACH-PKB-001..003`, `ACH-PACK-001..010`, all 24 `ACH-CNT-*` cards, `ACH-ASMT-001..011`, and the seven `ACH-X-*` exclusions.
- [x] The nine existing lesson IDs, fixed assessment rules, content themes, tiers, and separate `RIGHTS → CONTENT → ASSEMBLY` cards are explicit.
- [x] The current files-only / `1550` / disabled-lesson baseline and future no-network `+20` / `1730` proposal are distinct.
- [x] `ACH-X-STAGE-A/B/C`, `ACH-X-TAG`, `ACH-X-GITHUB-RELEASE`, `ACH-X-BLENDER-EXTENSIONS`, and `ACH-X-SUPERHIVE` explicitly exclude the release/publication path.
- [x] No wording treats this Stage 0 repository document as proof of a merge, a retained candidate, a release, or an implemented runtime feature.
