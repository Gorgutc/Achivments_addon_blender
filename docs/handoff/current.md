# Achievements 0.2.0 — Technical Backlog Closeout

## Goal

Prepare one integration PR, `codex/backlog-technical-closeout`, from
`main@04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3`. Deliver a verified
`reports/extension/achievements-0.2.0.zip` candidate while preserving catalog
IDs, operators, Scene properties, handlers, UI layout, persistence keys, and
`SCHEMA_VERSION = "1.0.0"`.

This handoff supersedes the active status of the historical Iteration 12
handoff and roadmap. Historical files remain unchanged as history.

## Branch And Pull Request

- Branch: `codex/backlog-technical-closeout`
- Draft PR: `https://github.com/Gorgutc/Achivments_addon_blender/pull/14`
- Baseline: `04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3`
- First CI commit: `d40a809` — fixed blocking Blender 5.0.1/5.1.2/5.2.0 matrix
- Packaging commit: `5f96f49` — deterministic Git-backed builder and GPL license
- Merge, tag, and GitHub Release are not authorized in this session.

## Changed Files

- Root runtime metadata, integrity wrappers, predicate adapter, and dead-code cleanup
- `achievements/integrity.py`, `achievements/predicates/`, and persistence policy
- `scripts/verify_frozen.py`, `scripts/verify_predicates.py`, and packaging tooling
- CI, Ruff configuration, unit/Blender smoke coverage, README, active contracts, and skills
- `LICENSE`, ADR 0002, and the byte-exact archived 100-achievement document

## Done

- Promoted add-on identity to 0.2.0 and minimum Blender metadata to 5.0.
- Replaced all active runtime 100-achievement text with 105.
- Retired `achievements_v01 (4).py` with separate raw-LF Git-blob and Windows-CRLF evidence, exact blob ID, source revision, and recovery procedure in ADR 0002.
- Moved `achievements_100_list.md` byte-for-byte to `docs/archive/`.
- Removed root `_ease_out_cubic`, `_check_streak`, `math`, `REWARDS_DIR`, predicate-local helpers, and the 712-line predicate branch tree; retained `achievements.ui.ease_out_cubic`.
- Added pure deterministic unlock-integrity helpers. Legacy payloads may backfill missing markers; current-schema missing or forged markers remain invalid and deny rewards.
- Added a pure predicate registry split by object/modifier, render, material, Geometry Nodes, and time/state. Root `_check_complex_step` is a thin Blender adapter; speed-model reset remains adapter-owned.
- Replaced source-text predicate coverage with an exact 65-ID/85-pair catalog bijection.
- Added full GPL-3.0-or-later `LICENSE` and a revision-mode builder that reads committed Git blobs, rejects dirty/untracked runtime payload, and validates ZIP members.
- Replaced the optional alpha canary with fixed blocking CI targets Blender 5.0.1, 5.1.2, and 5.2.0.
- Preserved missing-asset fallbacks and offline-only sync behavior.

## Remaining

- Complete full fast/deep/release gates on the final committed revision.
- Build and audit `reports/extension/achievements-0.2.0.zip`; record SHA-256, size, and member digests.
- Complete independent code/dead-code/component/instruction-drift/lookahead/verification reviews and explicit `/review` fallback.
- Push the final commits and require all PR checks green. Do not merge.
- After PR verification, update only `1-Projects/Achivments_addon_blender` from an isolated clean Second Brain worktree, proving every `instance_matcher` surface byte-identical; then append one automatic-memory note.

## Verification

Completed focused evidence:

- CI workflow contract: passed; baseline PR run started all three fixed Blender rows.
- Integrity and persistence: `12 passed`; focused Ruff passed.
- Predicate registry: exact 65 IDs / 85 pairs, no `bpy`; `264 passed`; focused Ruff passed.
- Five predicate-category Blender fixtures: false→true and no-error marker passed on Blender 5.1.2 and 5.2.0 in isolated profiles.
- Packaging: `20 passed`; focused Ruff passed; GPL normalized SHA-256 `8CEB4B9EE5ADEDDE47B31E975C1D90C73AD27B6B165A1DCD80C7C545EB65B903`.
- Frozen verifier after integration: `40/40 PASS`.
- Duplicate recovery evidence independently reproduced Git blob `21d5023697370800ced934959463da1e4be7cd5f`, raw LF SHA-256 `9CB06CA4B4CECF48B2CA52E59F5F930B45FC537F5A945D262EBC086551090681`, and Windows CRLF SHA-256 `62DDB0163B29C8C4A39347DEAF19D201F71C50A3D0F9A48F803387444DB24DAE`.

Final gate evidence will replace this in-progress list before closeout.

## Agents And Review

- Persistent `requirements_guardian` maintains the ignored session ledger under `reports/session/`.
- Predicate and packaging implementers completed focused verification.
- Independent code/dead-code and component/instruction-drift audits are in progress.
- Lookahead and final verification review remain required after the complete diff is stable.

## Blockers

No confirmed code blocker. Blender 5.0.1 final-revision evidence, candidate ZIP verification, PR checks, and isolated durable closeout are pending.

## Residual Risks

- Real content remains intentionally absent: 219 referenced PNG files, 11 placeholder tutorial URLs, and 20 reward `.blend` names require owner-supplied licensed assets/content.
- Same-object predicate requirements, `custom_origin`, WIND/particle edge cases, and other known legacy approximations remain separate behavior tasks.
- Production cloud backend and remaining UI/GPU decomposition are separate epics.
- Windows ACL cleanup can fail for some system temp directories; verification must use controlled isolated profile paths and report any runner-level limitation.

## Next Start Prompt

Continue Achievements 0.2.0 on `codex/backlog-technical-closeout` and draft PR #14. Read `AGENTS.md`, this handoff, ADR 0002, the requirements ledger, and the current PR checks. Do not merge, tag, create a GitHub Release, touch real `~/BlenderAchievements`, or modify any `instance_matcher` information. Finish the remaining release gates, reviews, isolated Second Brain update, and append-only automatic-memory closeout.
