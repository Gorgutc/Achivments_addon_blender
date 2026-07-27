# Achievements 0.2.2 — Blender Extension Policy Compliance

## Goal

Close Blender Extension policy warnings without changing add-on behavior: load every shipped support module below `bl_ext.<repository>.achievements`, keep the extension directory out of `sys.path`, declare only the file permission needed for local progress and reward assets, and prepare an audited `reports/extension/achievements-0.2.2.zip` for owner acceptance. Public operators, Scene properties, catalog IDs, persistence keys, `SCHEMA_VERSION = "1.0.0"`, UI behavior, reward fallbacks, and the offline-only product boundary remain unchanged.

This slice starts from clean `main@ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`, the merge commit of PR #14. The original technical-closeout baseline `04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3`, ADR 0002 duplicate-recovery evidence, and ADR 0003 behavior decisions remain historical truth. ADR 0004 records the new extension namespace and manifest-permission decision.

## Branch And Pull Request

- Branch: `codex/extension-policy-022`.
- Base: `main@ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`.
- PR #14 (`codex/backlog-technical-closeout`) is confirmed merged: `https://github.com/Gorgutc/Achivments_addon_blender/pull/14`; merge commit `ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`.
- Draft PR #15: `https://github.com/Gorgutc/Achivments_addon_blender/pull/15`. It targets `main` from `codex/extension-policy-022`; the owner performs any later merge manually.
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

- Canonical path: `reports/extension/achievements-0.2.2.zip`.
- Exact runtime source revision: `14defe9794539c8ffe57c1b9d6675a8662564d32`.
- SHA-256: `7C564D30C10B650B0F004FC857424626F9B06E1C331609C619E39899D658617F`.
- Size: `62,724` bytes; `22` regular allowlisted members; `237,778` uncompressed bytes.
- Every member is byte-identical to its Git blob at the runtime source revision. The three Blender builds share one exact member-digest map and contain no symlink, duplicate, path traversal, or unexpected entry. Their ZIP container hashes may differ because Blender writes build metadata; the audited Blender 5.2.0 stream was copied byte-for-byte once to the canonical path and used unchanged for all final lifecycle gates.
- Immutable predecessor: `reports/extension/achievements-0.2.1.zip`, SHA-256 `568E1595249CA2816E461BE5AA5FAD5687C686BACD613B5B0A72A7E8D5337D42`, size `62,691` bytes. It must not be overwritten or relabeled.
- The immutable 0.2.0 candidate and quarantined invalid pre-fix artifact also remain untouched.

Canonical member SHA-256 map:

```text
LICENSE                                            8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903
__init__.py                                        08377208ba1be1d221b4408826b31e1c6abbce344be80f98e02bbc93abbb614e
achievements/__init__.py                           56f54ae3cdc1961c3da77601370bc690ca7c7700582e1a5fe53e8f62b2c301b6
achievements/catalog.py                            849ff560b71f8525bc1055ffeb954cee44775c3a57a5c5d2b0e6418c88916603
achievements/engine.py                             6755f489f8a277afeb043b2f87f24cae8e349a79287d4a95cb7f14a1912658eb
achievements/events.py                             964ce539e530bb48bf74eae437b6c27f8f5374dba73de61d53390421fd177368
achievements/integrity.py                          4d0702afbd48e5840026ec817cc7cbf39082bc719da7d3347b154e098870cdf2
achievements/lifecycle.py                          1870354727c0048878f93a207010969fc8c09b494f454802175e3e2b06d3a2c0
achievements/metadata.py                           b2a09c87cc5540f2b2f1b6b9f3900b007e5a7f88a9a882b270b4049592b456fe
achievements/persistence.py                        eb6ba2d0f7d9df4c6c93117c756e90527bbb1f5c362b39b352fbef8dae456db1
achievements/predicates/__init__.py                d3a34b25c5f67b730dbc30532a69617472e287a0d5c416c7c44c4302033c9113
achievements/predicates/geometry_nodes.py           24437b462900fe4228581b49d5512fd9ca5488dc7d89587f0e4f25f95e156960
achievements/predicates/material.py                 58a22a9b7fc44df1b8d27ec4e56304ee0829818c6c6dd2b947ab07d239e4ab44
achievements/predicates/object_modifier.py          5fe747f7e9d7914bc019a212720928e269c688b8bcbce2dfd81a567be14844d0
achievements/predicates/registry.py                 333a81c3f602d8974eb07b5925887fa1eb0a48d52225ae9e2e7315f25350ab18
achievements/predicates/render.py                   f17133298b8f5220ca572a7df85f9cadb434bbef6f1a48ee69d7877f4fdaf3e1
achievements/predicates/time_state.py               b1ef18512cf1139177fa462cd4341e1198052f6985845f9a1fc5f1ed7f61edfd
achievements/predicates/types.py                    9a02f7c9cf9979ee7251232995c4fea3bcf7a0d18276ba300bf5a4d085c815d8
achievements/rewards.py                             7bb43ca9a34c7b3a2a6c2205f148de35daf653af844b3fd340c1822bc65b7822
achievements/sync.py                                d0f9f430e471470ab7400cd63663c10e0d448bdf85fe828966dfcb3584393d92
achievements/ui.py                                  68a1393928e01ca8dbc8d5992449ffab655a9e4695f6df440490dcdbbb2870f6
blender_manifest.toml                               b553a81daa8e1aa91384f91819758c765e9723fee5e53f276d5d4adc9d68e2df
```

## Remaining

- Commit and push this handoff closeout, then observe every blocking check for the final draft PR #15 head and provide the exact canonical ZIP to the owner for visible acceptance. Leave merge, tag, and GitHub Release to the owner.
- After the owner manually merges 0.2.2, update only the six approved Achievements files in Second Brain, preserving every protected `instance_matcher` surface byte-for-byte; then add one append-only automatic-memory note.
- Owner-input epics remain open: 219 referenced PNG files, 11 placeholder tutorial URLs, 20 reward `.blend` names and licenses, predicate-semantics decisions, production cloud, and remaining UI/GPU decomposition.

## Verification

- Committed `uv run` fast gate: `verify_frozen.py` 43/43 PASS; `verify_codex_plugin.py` 107/107 PASS; exact 65-ID/85-pair predicate verifier PASS without `bpy`; Ruff PASS; full pytest `458 passed`.
- All six source Blender suites pass on committed HEAD for Blender 5.0.1, 5.1.2, and 5.2.0: 18/18 PASS in disposable profiles.
- Git-backed `extension validate`, `extension build`, and `server-generate` passed independently on all three Blender versions. All three builds contain the same exact Git-byte member map.
- The canonical ZIP itself passed a second `extension validate` and fresh one-package `server-generate` on all three versions; each generated repository recorded the exact sole `files` permission, no `network`, and the matching archive hash.
- One exact canonical SHA passed install/enable, full empty warning map, namespace and `sys.path` checks, installed manifest permissions, explicit unregister/register, external Blender-owned CLI removal, disabled/unimportable post-state, and three byte-identical disposable sentinels on Blender 5.0.1, 5.1.2, and 5.2.0. No `Policy violation with top level module:` or `Policy violation with sys.path:` line was emitted.
- Draft PR #15 blocking checks for implementation commit `14defe9794539c8ffe57c1b9d6675a8662564d32` were all green: Fast gate plus Blender 5.0.1, 5.1.2, and 5.2.0.

## Agents And Review

- A persistent `requirements_guardian` tracks scope, completed evidence, remaining gates, protected artifacts, and owner-only actions.
- Code/dead-code, component/instruction-drift, lookahead, and independent verification reviewers run in waves.
- The first independent review found and closed three Important gaps: incomplete removal lifecycle, partial warning-map inspection, and missing ADR 0004 verifier coverage.
- Final component/lookahead and code/dead-code reviews report `Critical 0 / Important 0`. The explicit `/review` fallback covers requirements, complete diff, checks, blockers, and residual risks.

## Blockers

No known implementation or packaging blocker. Merge remains intentionally blocked on green final-PR-head CI plus the owner's visible 0.2.2 acceptance and manual merge. Tag, GitHub Release, Second Brain publication, and automatic-memory closeout remain unauthorized before the owner's manual merge.

## Residual Risks

- The visible Extensions card and permission display still need the owner's short manual 0.2.2 acceptance before merge: no Warning section, `files` permission visible, add-on opens, and final Blender-owned `Uninstall` succeeds.
- Headless probes exercise the loader/policy/lifecycle contract but do not replace that visible UI acceptance.
- Real content remains absent: 219 referenced PNG files, 11 placeholder tutorial URLs, and 20 reward `.blend` names need owner-provided licensed content.
- Predicate semantics, production cloud, and remaining UI/GPU decomposition remain separate tasks.

## Next Start Prompt

Continue Achievements 0.2.2 on draft PR #15 from `codex/extension-policy-022`. Read `AGENTS.md`, this handoff, ADR 0002, ADR 0003, and ADR 0004. Confirm final-PR-head blocking CI remains green and record owner acceptance of exact ZIP SHA-256 `7C564D30C10B650B0F004FC857424626F9B06E1C331609C619E39899D658617F`; the owner then merges manually. After merge, perform only the approved six-file Achievements Second Brain closeout and append-only memory note. Do not auto-merge, tag, create a GitHub Release, touch real `~/BlenderAchievements`, overwrite immutable ZIPs, or modify any `instance_matcher` information.
