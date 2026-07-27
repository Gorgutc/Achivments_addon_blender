# Achievements 0.2.1 — Developer Reset And Predicate Fixes

## Goal

Finish the developer-test slice on `codex/backlog-technical-closeout` and draft PR #14: preserve the existing confirmed progress reset, add a crash-safe route to real Blender extension removal, prevent factory-default false unlocks for `subsurface_skin` and `denoiser_render`, and publish a separately verified `reports/extension/achievements-0.2.1.zip`. Catalog IDs, persistence keys, and `SCHEMA_VERSION = "1.0.0"` remain unchanged.

This slice starts from completed 0.2.0 handoff head `98c84b5961e6b9957788ecc42c3044816af551c6`. The original technical-backlog and duplicate-retirement baseline remains `04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3`; ADR 0002 and its recovery evidence remain historical truth. ADR 0003 records the new runtime decisions. The immutable 0.2.0 ZIP is not overwritten.

## Branch And Pull Request

- Branch: `codex/backlog-technical-closeout`
- Draft PR: `https://github.com/Gorgutc/Achivments_addon_blender/pull/14`
- Supported blocking matrix: Blender 5.0.1/5.1.2/5.2.0
- Merge, tag, and GitHub Release are not authorized.

## Changed Files

- Root runtime: version 0.2.1, render-event propagation, handler-supplied scene, strict installed-extension resolution, and native `Extensions` navigation.
- Pure helpers: optional predicate event, exact Principled Subsurface Weight, event-gated Cycles denoising, and fail-closed extension target planning.
- Tests and verifiers: factory-default characterization, real exception sentinels for all 85 predicate pairs, handler-level render semantics, Blender Extensions API checks, and an AST prohibition on self-uninstall.
- Active README, architecture, frozen contract/decisions, verification, packaging guidance, plugin skills, ADR 0003, and this handoff.

## Done

- Kept `Сбросить прогресс` behavior and confirmation unchanged. It resets achievement/progress state but does not remove the extension or delete `textures/`/`rewards/` assets.
- Added `Удалить аддон…`. It is enabled only when `bl_ext.<repo>.achievements` resolves to exactly one enabled USER repository and the executing package directory matches that repository.
- The navigation operator checks Preferences availability, opens `section='EXTENSIONS'`, selects add-ons and installed packages, clears stale filters/tags, and searches for `Achievements`. Blender owns the final `Uninstall` action after add-on code returns.
- Prohibited add-on-owned `extensions.package_uninstall`, legacy `preferences.addon_remove`, and manual package deletion. Nested self-uninstall crashed isolated Blender 5.0.1/5.1.2/5.2.0 processes and is not part of normal verification.
- Kept `~/BlenderAchievements/` outside package removal. External Blender-owned removal acceptance uses only disposable profiles and must prove sentinel data unchanged.
- Fixed `subsurface_skin`: default-positive `Subsurface Scale`/`Subsurface IOR` no longer count; only exact active or linked `Subsurface Weight` (plus exact legacy `Subsurface`) matches.
- Fixed `denoiser_render`: only a completed Cycles render with `use_denoising` matches. Timer/depsgraph checks, Eevee, denoising-off, and passive default configuration remain false.
- `on_render_complete` evaluates the scene supplied by Blender rather than an unrelated ambient context scene.
- Preserved the exact 65-ID/85-pair catalog bijection, all 105 catalog IDs, 9 lessons, full GPL-3.0-or-later `LICENSE`, reward fallbacks, and offline-only sync.
- Historical duplicate evidence remains raw LF SHA-256 `9CB06CA4B4CECF48B2CA52E59F5F930B45FC537F5A945D262EBC086551090681` and Windows CRLF SHA-256 `62DDB0163B29C8C4A39347DEAF19D201F71C50A3D0F9A48F803387444DB24DAE`.

## Candidate Artifact

- Planned canonical path: `reports/extension/achievements-0.2.1.zip`
- Runtime source revision, SHA-256, size, member digests, and three-version install/removal evidence are pending the committed-revision release gate.
- Existing `reports/extension/achievements-0.2.0.zip` remains immutable.

## Remaining

- Commit the implementation revision, run the full committed-revision fast/deep/release gates, and publish the new canonical ZIP without overwriting prior candidates.
- Validate installed extension-management state and external Blender-owned removal on all three versions while preserving disposable-profile data sentinels.
- Complete independent review, update this handoff with final SHA/evidence, push draft PR #14, then perform isolated Second Brain and append-only automatic-memory closeout.
- Owner-input epics stay open: 219 referenced PNG files, 11 placeholder tutorial URLs, 20 reward `.blend` names plus licenses, same-object/custom-origin/WIND behavior decisions, production cloud, and remaining UI/GPU decomposition.

## Verification

Current pre-commit evidence:

- `verify_frozen.py`: `41/41 PASS`.
- `verify_predicates.py`: exact 65 IDs / 85 catalog pairs; no `bpy` imports.
- Focused Ruff: PASS.
- Focused pure tests after new exception coverage: `405 passed`.
- Blender 5.1.2 `engine` and `register` smoke: PASS in disposable profiles, including handler-level denoiser propagation and the `EXTENSIONS` operator/property contract.
- Full pytest, all six suites on all three versions, packaging, installed-navigation, external removal, ZIP hashes, and CI remain pending until the runtime revision is committed.

## Agents And Review

- Persistent `requirements_guardian` maintains the ignored session ledger and checks scope, done work, and remaining gates.
- Code/dead-code and component/instruction-drift/lookahead agents independently reproduced both false unlocks and the nested-uninstall crash on all supported versions.
- Final verification-review and explicit `/review` fallback are pending release evidence.

## Blockers

No current implementation blocker. The release artifact cannot be built in `--revision HEAD` mode until this complete runtime payload is committed. Any confirmed Critical/Important review finding must be fixed before that commit.

## Residual Risks

- The uninstall button intentionally opens Blender's filtered native card and requires the user to select `Uninstall`; one-click self-removal from add-on-owned Python is unsafe.
- Existing already-unlocked false-positive IDs are not revoked automatically. Use the existing confirmed reset for a clean retest.
- Real content remains absent: 219 referenced PNG files, 11 placeholder tutorial URLs, and 20 reward `.blend` names need owner-provided licensed content.
- Same-object predicate requirements, `custom_origin`, WIND/particle edge cases, production cloud, and remaining UI/GPU decomposition remain separate tasks.

## Next Start Prompt

Continue Achievements 0.2.1 on `codex/backlog-technical-closeout` and draft PR #14. Read `AGENTS.md`, this handoff, ADR 0002, and ADR 0003. Finish every pending release gate, then replace pending artifact fields with exact committed revision/SHA/size evidence. Do not merge, tag, create a GitHub Release, touch real `~/BlenderAchievements`, overwrite the immutable 0.2.0 ZIP, or modify any `instance_matcher` information.
