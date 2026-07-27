# Achievements 0.2.2 — Blender Extension Policy Compliance

## Goal

Close Blender Extension policy warnings without changing add-on behavior: load every shipped support module below `bl_ext.<repository>.achievements`, keep the extension directory out of `sys.path`, declare only the file permission needed for local progress and reward assets, and prepare an audited `reports/extension/achievements-0.2.2.zip` for owner acceptance. Public operators, Scene properties, catalog IDs, persistence keys, `SCHEMA_VERSION = "1.0.0"`, UI behavior, reward fallbacks, and the offline-only product boundary remain unchanged.

This slice starts from clean `main@ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`, the merge commit of PR #14. The original technical-closeout baseline `04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3`, ADR 0002 duplicate-recovery evidence, and ADR 0003 behavior decisions remain historical truth. ADR 0004 records the new extension namespace and manifest-permission decision.

## Branch And Pull Request

- Branch: `codex/extension-policy-022`.
- Base: `main@ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`.
- PR #14 (`codex/backlog-technical-closeout`) is confirmed merged: `https://github.com/Gorgutc/Achivments_addon_blender/pull/14`; merge commit `ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`.
- The 0.2.2 draft integration PR is created only after committed release gates are green. The owner performs any later merge manually.
- Supported blocking matrix: Blender 5.0.1/5.1.2/5.2.0.
- Do not merge, tag, create a GitHub Release, or auto-merge from this handoff.

## Changed Files

- Root runtime and `achievements/predicates/time_state.py`: package-relative intra-extension imports; no runtime `import sys`, `_ADDON_DIR`, `sys.path` mutation, or absolute `achievements.*` fallback.
- Runtime, manifest, package metadata, `pyproject.toml`, and lockfile: active identity `0.2.2`, with Blender minimum 5.0 unchanged.
- `blender_manifest.toml`: exact `[permissions].files = "Store progress and load local reward assets"`; no `network` permission.
- Six source smoke loaders: package-aware root specs through `submodule_search_locations`.
- Static and installed-policy gates: import-policy AST checks, exact permission checks, empty Blender warning map, namespace identity, explicit unregister/register, external remove, post-remove state, archive hash, and disposable progress sentinels.
- Active README, architecture, frozen decisions/contract, packaging, verification, quality guidance, repo-local skills, CI, tests, ADR 0004, and this handoff.

## Done

- Removed the root `sys.path` bootstrap and converted root imports to `.achievements.*`; converted the time/state predicate import to `..engine`.
- Added a fail-closed static guard for shipped `import sys`, `from sys import`, `sys.path` access, and absolute intra-package `achievements.*` imports.
- Added an installed extension probe requiring all extension-directory modules to remain under `bl_ext.user_default.achievements...`, the extension directory to remain absent from `sys.path`, and Blender's entire extension warning map to be empty.
- Added manifest checks in both normal Python and installed Blender for the exact `files` permission and absence of `network`.
- Extended the installed lifecycle to build or select one exact archive, install/enable, probe namespace and permissions, explicitly unregister/register, externally remove through Blender CLI, prove disabled/unimportable post-state, and preserve three byte-exact sentinels under a disposable `BlenderAchievements` directory.
- Kept the exact 65-ID/85-pair catalog bijection, 105 achievements, 9 lessons, full GPL-3.0-or-later `LICENSE`, local integrity format, persistence schema, native extension-removal route, and all 0.2.1 predicate fixes unchanged.
- Preserved duplicate recovery evidence: raw LF SHA-256 `9CB06CA4B4CECF48B2CA52E59F5F930B45FC537F5A945D262EBC086551090681` and Windows CRLF SHA-256 `62DDB0163B29C8C4A39347DEAF19D201F71C50A3D0F9A48F803387444DB24DAE`.

## Owner Acceptance For 0.2.1

The owner confirmed the exact `reports/extension/achievements-0.2.1.zip` was installed, progress reset completed, corrected `subsurface_skin` and `denoiser_render` behavior was checked, the add-on routed to Blender's native Extensions card, and the final Blender-owned `Uninstall` completed successfully. This records the requested visible acceptance only; it does not separately claim that real user data was preserved after the owner's manual removal.

## Candidate Artifact

- Reserved canonical path: `reports/extension/achievements-0.2.2.zip`.
- The canonical 0.2.2 candidate, runtime commit, SHA-256, size, member digests, and three-version exact-archive evidence are pending the committed-revision release gate and must be filled in before delivery.
- Immutable predecessor: `reports/extension/achievements-0.2.1.zip`, SHA-256 `568E1595249CA2816E461BE5AA5FAD5687C686BACD613B5B0A72A7E8D5337D42`, size `62,691` bytes. It must not be overwritten or relabeled.
- The immutable 0.2.0 candidate and quarantined invalid pre-fix artifact also remain untouched.

## Remaining

- Commit the reviewed implementation, then build 0.2.2 from exact Git blobs with `scripts/build_extension.py --revision HEAD`.
- Run `extension validate`, `extension build`, `server-generate`, ZIP allowlist/Git-byte/member audit, and the exact canonical archive lifecycle on Blender 5.0.1, 5.1.2, and 5.2.0.
- Record the final runtime commit, SHA-256, byte size, member digests, and `Critical 0 / Important 0` review evidence here.
- Push `codex/extension-policy-022`, create the draft integration PR, and observe all blocking CI checks. Leave merge, tag, and GitHub Release to the owner.
- After the owner manually merges 0.2.2, update only the six approved Achievements files in Second Brain, preserving every protected `instance_matcher` surface byte-for-byte; then add one append-only automatic-memory note.
- Owner-input epics remain open: 219 referenced PNG files, 11 placeholder tutorial URLs, 20 reward `.blend` names and licenses, predicate-semantics decisions, production cloud, and remaining UI/GPU decomposition.

## Verification

- Static pre-commit evidence: `verify_frozen.py` 43/43 PASS; `verify_codex_plugin.py` 107/107 PASS after required policy files entered the index; exact predicate verifier PASS; Ruff PASS.
- All six source Blender suites pass on Blender 5.0.1, 5.1.2, and 5.2.0: 18/18 PASS in disposable profiles.
- Preliminary working-tree install/policy probes passed on all three supported Blender versions with no `Policy violation with top level module:` and no `Policy violation with sys.path:` output.
- The strengthened full install/policy/register/unregister/remove lifecycle passed on Blender 5.0.1, 5.1.2, and 5.2.0 against one exact preliminary working-tree archive, SHA-256 `C76B98B483B37DB08E327592453B4A6ABF4D6C24B6170CE02C73AEA1E9E162EC`, including empty warning map, post-remove state, unchanged archive hash, and unchanged disposable sentinels.
- These preliminary runs do not replace the pending committed-Git canonical ZIP matrix.

## Agents And Review

- A persistent `requirements_guardian` tracks scope, completed evidence, remaining gates, protected artifacts, and owner-only actions.
- Code/dead-code, component/instruction-drift, lookahead, and independent verification reviewers run in waves.
- The first independent review found and closed three Important gaps: incomplete removal lifecycle, partial warning-map inspection, and missing ADR 0004 verifier coverage. Final review is repeated after committed artifact evidence.
- `/review` fallback covers requirements, complete diff, test evidence, blockers, and residual risks before delivery.

## Blockers

No known implementation blocker. Delivery is intentionally blocked until the committed 0.2.2 ZIP and full three-version exact-archive gates are complete. Merge, tag, GitHub Release, Second Brain publication, and automatic-memory closeout remain unauthorized before the owner's manual merge.

## Residual Risks

- The visible Extensions card and permission display still need the owner's short manual 0.2.2 acceptance before merge: no Warning section, `files` permission visible, add-on opens, and final Blender-owned `Uninstall` succeeds.
- Headless probes exercise the loader/policy/lifecycle contract but do not replace that visible UI acceptance.
- Real content remains absent: 219 referenced PNG files, 11 placeholder tutorial URLs, and 20 reward `.blend` names need owner-provided licensed content.
- Predicate semantics, production cloud, and remaining UI/GPU decomposition remain separate tasks.

## Next Start Prompt

Continue Achievements 0.2.2 on `codex/extension-policy-022` from `main@ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`. Read `AGENTS.md`, this handoff, ADR 0002, ADR 0003, and ADR 0004. Complete only the pending committed-artifact, CI, owner-acceptance, and post-merge closeout gates. Do not merge, tag, create a GitHub Release, touch real `~/BlenderAchievements`, overwrite immutable ZIPs, or modify any `instance_matcher` information.
