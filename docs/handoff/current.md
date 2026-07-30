# Achievements — 0.2.3 Release Identity And Lesson Assessment Research

## Goal

Make the current source identity `0.2.3` truthful, preserve its owner-gated release path, and record a closed lesson-result assessment research entry gate. ADR 0008 advances from the immutable pre-PR16 `0.2.2` ZIP because it cannot represent current `main`. Release stages: (A) a full validation gate produces only ephemeral outputs and authorizes no retention, canonical artifact, or publication; (B) only separate explicit owner candidate-retention acceptance may preserve one exact audited local candidate SHA, which remains non-canonical and not publication; (C) only separate explicit owner publication acceptance may create `v0.2.3` tag and GitHub Release from that exact retained candidate. This session grants none. PR #17 reward-claim atomicity is a preserved historical prerequisite from `codex/reward-claim-atomicity`: its exact head `213babb6e29e023617a66600e4b9d8375ea466d9`, base `origin/main@9cd26bd616c861578bc026a627c1796dddcac655`, and merge `396dda957908b26c94d73387bcddf14712a4c23c` remain historical evidence, not the current task goal.

## Changed Files

- Identity surfaces: `__init__.py`, `achievements/metadata.py`, `blender_manifest.toml`, `pyproject.toml`, `uv.lock`, and `tests/blender/smoke_extension_policy.py`.
- Release policy: `AGENTS.md`, `README.md`, ADR 0008, the active architecture/frozen/packaging/quality/verification docs, the four release-related plugin skills, and this handoff.
- Guard and build tooling: `scripts/build_extension.py`, `scripts/verify_frozen.py`, and `scripts/verify_codex_plugin.py`.
- Infra and release coverage: `tests/test_infra_scripts.py` and `tests/test_release_packaging.py`.
- Research-only assessment: `docs/research/lesson-result-verification.md` and its guard/mutant coverage.
- `achievements/rewards.py`, `achievements/persistence.py`, and their runtime behavior are unchanged in this current diff.

## Done

- All active identity surfaces, including the root `uv.lock` package and source-register smoke expectation, now agree on `0.2.3`.
- ADR 0008 defines Stage A ephemeral validation, separately owner-accepted Stage B retention of one exact audited local SHA, and separately owner-accepted Stage C tag/GitHub Release publication; no stage is granted here.
- The historical `achievements-0.2.2.zip` is immutable evidence only. The release builder rejects its use, enforces the required payload and `achievements/levels.py`, and performs its policy guard before source preparation, Blender discovery, or output.
- AST/TOML parity checks and clause-level additive guards cover all active release authorities, malformed `uv.lock` package shape, cache/digest boundaries, release actions, and owner-gated exceptions.
- `docs/research/lesson-result-verification.md` is a complete closed research specification: exact rubric and owner-decision fields, calibration/null threshold, disabled persistence/reward bridge, and no implementation authorization.
- Historical PR #17 **Reward Claim Atomicity** baseline is preserved unchanged: PR #17 merged exact head `213babb6e29e023617a66600e4b9d8375ea466d9` as `396dda957908b26c94d73387bcddf14712a4c23c`; its prospective claim and idempotent retry contract remain frozen by ADR 0007. The current schema `1.0.0`, the sole runtime, and `achievements/rewards.py`/`achievements/persistence.py` behavior are unchanged by this slice.

## Remaining

- Resolve the 16 owner decisions in `docs/research/lesson-result-verification.md`, including rubric semantics, fixtures/calibration, threshold, persistence/schema, and reward bridge, before proposing a separate ADR.
- Research anti-piracy/licensing separately; local unlock hashes and reward markers are not authentication. Any account or entitlement system requires an explicit privacy/network/revocation/offline-grace specification.
- Design an owner-only authoring UI separately for achievement cards, text, illustrations, tutorials, and reward assets, with validation and an export/review workflow rather than hidden production secrets in the add-on.
- Owner-input content epics remain: 219 licensed PNG files, 11 approved tutorial URLs, and 20 licensed reward `.blend` files.
- Predicate semantics, deeper fixtures, UI/GPU/handler decomposition, and production cloud remain separate decisions. Tag, GitHub Release, and selection of an exact 0.2.3 artifact remain blocked pending explicit owner ship acceptance.

## Verification

Required fast gate:

1. `uv run python scripts/verify_frozen.py`
2. `uv run python scripts/verify_codex_plugin.py`
3. `uv run python scripts/verify_predicates.py`
4. `uv run ruff check .`
5. `uv run pytest`

Current-session evidence: `verify_frozen.py` **59/59 PASS**; `verify_codex_plugin.py` **126/126 PASS**; targeted `tests/test_infra_scripts.py tests/test_release_packaging.py` **59 passed**; full pytest in an isolated basetemp **490 passed**; and Ruff PASS. One source-register smoke ran PASS on local Blender 5.1.2 with a disposable profile. `git diff HEAD --check` passes after the current remediation. This session did not run the full six-suite smoke set, cross-version smoke, installed-extension policy smoke, extension build, candidate retention, tag, or GitHub Release for 0.2.3. Commit, PR, and merge identity are resolved from Git history and the canonical Second Brain session record rather than self-referenced here.

Historical pre-ADR-0008 evidence: PR #17 ran the exact reviewed head through GitHub Fast Gate and the blocking Blender 5.0.1, Blender 5.1.2, and Blender 5.2.0 source-smoke matrix; all checks completed successfully before merge. CI created and removed disposable per-job ZIP/install state; no canonical, retained, or published extension artifact was produced. That is historical evidence only, not 0.2.3 Blender-smoke evidence. The local machine still has no Blender 5.0 executable.

## Agents And Review

- Terra guardian/implementer owns the task contract, frozen invariants, no-real-data boundary, implementation, and requirements ledger for this source-candidate/research slice.
- Sol orchestration coordinates the bounded review waves and preserves the owner-gated release boundary.
- The latest independent audit found stale handoff framing and clause-corpus gaps; this slice remediated those alongside release-policy, candidate-digest/cache-key, additive false-green, and malformed-`uv.lock` handling.
- Final independent code and backlog/instruction-drift re-review after remediation reports **0 Critical / 0 Important / 0 Low: GO** for the source-policy and research-draft merge. This is not Stage B candidate-retention or Stage C publication acceptance.
- The explicit `/review` fallback covers requirements, diff, checks, blockers, and residual risks because no callable slash command is available. PR #17 reviewer and Blender-matrix evidence above is historical only.

## Blockers

No technical blocker prevents source-candidate work. Research-draft work is likewise unblocked, while implementation remains closed. PR #17 historical evidence records Fast Gate and Blender 5.0.1 / 5.1.2 / 5.2.0 for its pre-ADR-0008 source, not this 0.2.3 session. ADR 0008 sets version `0.2.3`: Stage A full validation remains ephemeral, Stage B separate explicit owner candidate-retention acceptance is required for one exact audited local candidate SHA, and Stage C separate explicit owner publication acceptance is required for `v0.2.3` and GitHub Release. No stage is granted in this session. No production asset addition or real `~/BlenderAchievements` access is authorized.

## Residual Risks

- Witness recovery is scene/session local. A process crash can recover only when the marked `.blend` state survives; there is no cross-process reward journal.
- Concurrent Blender processes still share one JSON file and can overwrite each other last-writer-wins; multi-process coordination is a separate persistence task.
- Blender Undo does not reverse the external JSON claim; the claim proves a successful application event, while explicit reapply restores a removed scene result.
- `bpy.data.user_map()` delta cleanup assumes synchronous operator execution so unrelated IDs are not created inside the same action window.
- Production reward assets still require license approval and exact expected-datablock validation.
- Blender 5.0.1 behavior passed the blocking PR #17 matrix; Blender 5.0 is still unavailable locally, and future changes must retain that CI row.

## Next Start Prompt

Verify current `main` contains PR #17 head `213babb6e29e023617a66600e4b9d8375ea466d9`, merge `396dda957908b26c94d73387bcddf14712a4c23c`, ADR 0008, and the canonical lesson-assessment research draft before continuing. Do not redo reward claim atomicity or alter the release policy without a new owner decision. Take one separate task at a time: the lesson-assessment specification remains a separate research-only slice, and implementation remains prohibited until a separate ADR follows the closed entry gate. Keep real `~/BlenderAchievements` untouched; any tag, GitHub Release, canonical artifact, production asset publication, or cloud/auth change requires explicit owner authorization.
