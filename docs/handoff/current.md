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
- Integration commit: `59e100b` — metadata, duplicate retirement, integrity,
  predicates, tests, docs, and dead-code closeout
- Release-gate fix: `a7d4a3ab8966431a330cac9c2b1c225a2be57622` — headless
  username compatibility and isolated fail-closed Blender extension CLI
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
- Preserved `os.getlogin()` as the authoritative legacy username whenever it
  works; headless Blender falls back deterministically to `getpass.getuser()`
  and finally `unknown-user` without deriving identity from temporary HOME.
- Added a pure predicate registry split by object/modifier, render, material, Geometry Nodes, and time/state. Root `_check_complex_step` is a thin Blender adapter; speed-model reset remains adapter-owned.
- Replaced source-text predicate coverage with an exact 65-ID/85-pair catalog bijection.
- Added full GPL-3.0-or-later `LICENSE` and a revision-mode builder that reads committed Git blobs, rejects dirty/untracked runtime payload, and validates ZIP members.
- Replaced the optional alpha canary with fixed blocking CI targets Blender 5.0.1, 5.1.2, and 5.2.0.
- Added an isolated extension CLI runner using `--factory-startup` and temporary
  `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`; it rejects stale server
  output and fails closed on command errors, failure markers, or missing
  success markers. Any cleanup `[extension-cli:WARN]` invalidates release
  acceptance even if the helper itself exits zero.
- Preserved missing-asset fallbacks and offline-only sync behavior.

## Candidate Artifact

- Canonical path: `reports/extension/achievements-0.2.0.zip`
- Runtime source revision: `a7d4a3ab8966431a330cac9c2b1c225a2be57622`
- Selected source build: Blender 5.2.0 LTS under
  `reports/extension-validation/a7d4a3a/blender-5.2.0/`
- SHA-256: `99752FD28A8F894BDB8F26F61FA49C049C56CB4808286BA97A8AB39C085E36DA`
- Size: `61152` bytes
- Payload: exactly 22 regular files — manifest, `LICENSE`, root `__init__.py`,
  and the recursive `achievements/` runtime package
- Every member is byte-equal to its Git blob at the runtime source revision;
  no symlink, path traversal, duplicate/case-collision, legacy duplicate,
  test, documentation, workflow, report, or reward asset is present.
- The verified Blender 5.2 artifact was byte-copied once to the canonical path;
  source and destination SHA-256 matched. It was not rebuilt or overwritten.

## Remaining

- Commit and push this final handoff update, require the docs-only PR checks to
  remain green, and keep draft PR #14 unmerged.
- Update only `1-Projects/Achivments_addon_blender` from an isolated clean
  Second Brain worktree, proving every `instance_matcher` surface byte-identical.
- Append one automatic-memory note after the successful vault push.
- Owner-input epics remain open: 219 PNG assets, 11 real tutorial URLs, 20
  reward `.blend` assets plus licenses, predicate behavior decisions,
  production cloud, and remaining UI/GPU decomposition.

## Verification

Final committed-revision evidence:

- `verify_frozen.py`: `40/40 PASS`.
- `verify_predicates.py`: exact 65 IDs / 85 catalog pairs and no `bpy` import.
- `verify_codex_plugin.py`: `103/103 PASS`.
- `ruff check .`: PASS.
- Full `pytest`: `360 passed`.
- Draft PR #14 at `a7d4a3a`: Fast Gate run `30252504757` SUCCESS;
  Blender Smoke run `30252504744` SUCCESS on blocking 5.0.1, 5.1.2, and
  5.2.0 rows, each running all six suites.
- Official portable Blender 5.0.1 archive SHA-256
  `921D77F6C505A35B2C2F6E67D4AD1C10B72418338BA0E0D3EA7F582A5E5FE46E`
  matched Blender Foundation's published checksum; its local six-suite smoke
  passed in isolated profiles.
- Release-mode source `validate`, `build`, and one-package `server-generate`
  passed without WARN on Blender 5.0.1, 5.1.2, and 5.2.0.
- The exact canonical ZIP SHA above passed archive-member/Git-byte audit,
  archive `extension validate`, one-package `server-generate`, install/enable,
  manifest `0.2.0`, register, and unregister on all three Blender versions.
- All achievement data paths used disposable validation profiles; no real
  `~/BlenderAchievements` path was accessed by acceptance runs.
- GPL normalized SHA-256 remains
  `8CEB4B9EE5ADEDDE47B31E975C1D90C73AD27B6B165A1DCD80C7C545EB65B903`.
- Duplicate recovery evidence independently reproduced Git blob `21d5023697370800ced934959463da1e4be7cd5f`, raw LF SHA-256 `9CB06CA4B4CECF48B2CA52E59F5F930B45FC537F5A945D262EBC086551090681`, and Windows CRLF SHA-256 `62DDB0163B29C8C4A39347DEAF19D201F71C50A3D0F9A48F803387444DB24DAE`.

## Agents And Review

- Persistent `requirements_guardian` maintained the ignored session ledger
  under `reports/session/` and checked every requirement/gate transition.
- Explorer/component/instruction-drift, code/dead-code, lookahead, and final
  verification-review waves completed.
- Final independent result: Critical `0`, Important `0` after fixes.
- Explicit `/review` fallback covered requirements, full diff, checks,
  blockers, and residual risks; no merge, tag, or GitHub Release is authorized.

## Blockers

No confirmed code or release-artifact blocker. Only isolated durable closeout
in Second Brain and automatic memory remains; PR #14 must stay draft/unmerged.

## Residual Risks

- Real content remains intentionally absent: 219 referenced PNG files, 11 placeholder tutorial URLs, and 20 reward `.blend` names require owner-supplied licensed assets/content.
- Same-object predicate requirements, `custom_origin`, WIND/particle edge cases, and other known legacy approximations remain separate behavior tasks.
- Production cloud backend and remaining UI/GPU decomposition are separate epics.
- Blender's archive timestamp metadata means separate builds can have different
  outer ZIP SHA values despite identical member bytes. The frozen canonical
  SHA above is therefore the only candidate identity; do not rebuild it.
- Temporary-profile cleanup residue is non-product telemetry, but any emitted
  `[extension-cli:WARN]` invalidates acceptance and requires a fresh run.

## Next Start Prompt

Continue Achievements 0.2.0 on `codex/backlog-technical-closeout` and draft PR #14. Read `AGENTS.md`, this handoff, ADR 0002, and current PR checks. The canonical candidate is the exact SHA documented above. Do not rebuild or overwrite it. Do not merge, tag, create a GitHub Release, touch real `~/BlenderAchievements`, or modify any `instance_matcher` information. Only isolated Second Brain and append-only automatic-memory closeout should remain.
