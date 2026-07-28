# Achievements — Active-Time and XP Integration

## Goal

Integrate the owner-approved active-time correctness commit `787857d1ca6ef32be5fa81b708ef9b1e833f226e` and XP level-reachability commit `966ba6abc016454680d22179d93319686b8bbd6d` from their shared exact base `main@64076a6f7e6dde494ac9435627bdcebe2e7f9a46`. Close the related instruction drift without expanding product behavior.

PR #15 is already merged in `main@64076a6`; it is not a draft or an active continuation target. The delivery branch is `codex/active-time-level-integration`. Resolve its actual local and remote SHA with Git rather than treating this moving handoff as a commit-identity source.

## Changed Files

- Runtime and pure behavior: `__init__.py`, `achievements/events.py`, and new `achievements/levels.py`.
- Behavior regressions: `tests/test_events.py`, new `tests/test_levels.py`, and Blender smoke updates in `smoke_lifecycle_stress.py`, `smoke_persistence.py`, and `smoke_ui_visual.py`.
- Frozen decisions and architecture: ADR 0005, ADR 0006, `architecture.md`, `frozen-application-contract.md`, `frozen-decisions.md`, `verification.md`, and the frozen-decisions skill.
- Fail-closed verification: `scripts/verify_frozen.py`, `scripts/verify_codex_plugin.py`, and `tests/test_infra_scripts.py`.
- P1 instruction/CI repair: `README.md`, `.github/workflows/fast-gate.yml`, `.codex/hooks/session-start.py`, `quality-tooling.md`, `packaging-release.md`, the context-keeper skill, the historical roadmap banner, and this handoff.

## Done

- Active time uses the ADR 0005 non-refreshing 120-second monotonic window. Only qualifying Blender events open or extend a window; timer, persistence, popup/draw, register/load, and flush do not manufacture activity.
- Runtime activity anchors remain absent from JSON. Existing `time_spent`, `daily_sessions`, unlocks, integrity markers, rewards, persistence path, and `SCHEMA_VERSION = "1.0.0"` remain compatible.
- XP awards stay `5/10/20`; ADR 0006 freezes the ten reachable level bands and exact `1550 XP` cap. Level 10 progresses through `1549`, and only `105/105` displays `MAX`.
- Root compatibility aliases and wrappers remain while pure `achievements/levels.py` owns XP aggregation, level calculation, and display formatting.
- The retired duplicate stays absent. Context guidance now names `__init__.py` as the sole runtime and points to ADR 0002 recovery evidence.
- The old iterative roadmap is explicitly `SUPERSEDED — HISTORICAL PLAN ONLY`; its body remains historical evidence rather than current instructions.
- `scripts/verify_predicates.py` is now an explicit local and GitHub Actions fast-gate step, mirrored by active quality/release guidance and guarded by the Codex verifier and infra tests.

## Remaining

- Owner-input content epics remain separate: 219 licensed PNG files, 11 approved tutorial URLs, and 20 licensed reward `.blend` files with expected-datablock and claimed-only-after-apply acceptance.
- Predicate semantics, deeper Blender fixtures, further UI/GPU/handler decomposition, and a production cloud backend remain separate specifications.
- A tag or GitHub Release requires a later explicit release-policy decision. This integration does not authorize either.

## Verification

The combined branch must pass, as one result:

1. `uv run python scripts/verify_frozen.py`
2. `uv run python scripts/verify_codex_plugin.py`
3. `uv run python scripts/verify_predicates.py`
4. `uv run ruff check .`
5. `uv run pytest`
6. All six Blender source smoke suites in disposable profiles.
7. Committed-revision installed lifecycle/policy and the blocking Blender 5.0.1/5.1.2/5.2.0 matrix.
8. Requirements, code/dead-code, component/instruction-drift, verification, and lookahead review.

Individual source-branch results do not substitute for this combined gate. Never run Blender smoke against real `~/BlenderAchievements` data, and never overwrite the immutable 0.2.1/0.2.2 canonical ZIP evidence.

Combined-tree evidence recorded on 2026-07-28:

- `verify_frozen.py`: **58/58 PASS**; `verify_codex_plugin.py`: **119/119 PASS**; predicate registry: **65 IDs / 85 catalog pairs PASS**.
- Ruff: PASS; pytest: **478 passed**.
- All six source smoke suites passed on each blocking target Blender 5.0.1, 5.1.2, and 5.2.0: **18/18 PASS**, using disposable profiles.
- Independent conflict/component/dead-code and instruction-drift/verification reviews found two Important documentation guards, both fixed and re-reviewed at **0 Critical / 0 Important / 0 Low**.

Committed integration-tree installed lifecycle/policy passed on Blender 5.0.1, 5.1.2, and 5.2.0: install, namespace/`sys.path`/warning/permission checks, explicit unregister/register, Blender-owned removal, post-remove state, and disposable progress preservation all passed. Per-run ZIP hashes are verification artifacts rather than byte-reproducible commit identities. The exact final commit and remote state belong in the paired session closeout; this file intentionally does not self-reference its containing SHA.

## Agents And Review

- A persistent requirements guardian held the owner-approved behavior, no-real-data, one-commit, push-only, and no-release boundaries.
- Independent conflict/component/dead-code and instruction-drift/verification/lookahead reviewers inspected the combined tree in waves.
- Review fixed the missing ADR 0005 frozen-skill contract and weak P1 false-green checks, then confirmed **0 Critical / 0 Important / 0 Low**.
- If the `/review` command is unavailable, the final reviewer performs the explicit requirements/diff/checks/blockers/residual-risks fallback.

## Blockers

None for the scoped P0/P1 integration. PR creation, tag creation, and GitHub Release creation are intentionally outside this handoff.

## Residual Risks

- Future catalog or difficulty changes must recompute the XP cap, reachability, and no-downlevel bounds.
- Future activity sources must preserve the non-refreshing monotonic-window contract and keep flush paths passive.
- Real content, disputed predicate semantics, deeper Blender fixtures, root-runtime decomposition, and production cloud remain unfinished product work.

## Next Start Prompt

Verify the exact remote state of `codex/active-time-level-integration` or its eventual `main` merge before continuing. Do not redo P0/P1. Select one owner-input epic from the canonical backlog, keep real `~/BlenderAchievements` untouched, and do not create a tag or GitHub Release without a separate owner decision.
