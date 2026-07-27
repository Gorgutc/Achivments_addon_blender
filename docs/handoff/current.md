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
- Installed extensions may lose root `bl_info` after Blender consumes it. Runtime navigation therefore reads `achievements.metadata.ADDON_NAME`; the frozen verifier forbids later `bl_info` reads, and Blender register smoke removes `bl_info` before exercising the full success branch.
- Prohibited add-on-owned `extensions.package_uninstall`, legacy `preferences.addon_remove`, and manual package deletion. Nested self-uninstall crashed isolated Blender 5.0.1/5.1.2/5.2.0 processes and is not part of normal verification.
- Kept `~/BlenderAchievements/` outside package removal. External Blender-owned removal acceptance uses only disposable profiles and must prove sentinel data unchanged.
- Fixed `subsurface_skin`: default-positive `Subsurface Scale`/`Subsurface IOR` no longer count; only exact active or linked `Subsurface Weight` (plus exact legacy `Subsurface`) matches.
- Fixed `denoiser_render`: only a completed Cycles render with `use_denoising` matches. Timer/depsgraph checks, Eevee, denoising-off, and passive default configuration remain false.
- `on_render_complete` evaluates the scene supplied by Blender rather than an unrelated ambient context scene.
- Preserved the exact 65-ID/85-pair catalog bijection, all 105 catalog IDs, 9 lessons, full GPL-3.0-or-later `LICENSE`, reward fallbacks, and offline-only sync.
- Historical duplicate evidence remains raw LF SHA-256 `9CB06CA4B4CECF48B2CA52E59F5F930B45FC537F5A945D262EBC086551090681` and Windows CRLF SHA-256 `62DDB0163B29C8C4A39347DEAF19D201F71C50A3D0F9A48F803387444DB24DAE`.

## Candidate Artifact

- Canonical path: `reports/extension/achievements-0.2.1.zip`
- Exact runtime source revision: `e179172705197da089ea04f709aaca3b38ad395b`.
- SHA-256: `568E1595249CA2816E461BE5AA5FAD5687C686BACD613B5B0A72A7E8D5337D42`.
- Size: `62,691` bytes; `22` regular allowlisted members; `237,719` uncompressed bytes.
- Every member is byte-identical to the corresponding Git blob at the exact source revision. There are no symlinks, duplicate entries, path traversal, or unexpected files.
- Blender 5.0.1/5.1.2/5.2.0 independently produced the same member digest map. The canonical byte stream is the Blender 5.2.0 build and remained unchanged through validation, repository generation, installation, probing, and removal checks on all three versions.
- Existing `reports/extension/achievements-0.2.0.zip` remains immutable. The invalidated pre-fix 0.2.1 candidate remains recoverably quarantined under `reports/extension-invalid/` and is not installable delivery evidence.

## Remaining

- Push the current 0.2.1 branch, including this refreshed handoff, to draft PR #14; observe its blocking checks and leave merge/tag/GitHub Release to a separate owner decision.
- Complete isolated Second Brain and append-only automatic-memory closeout without changing any `instance_matcher` surface.
- Owner-input epics stay open: 219 referenced PNG files, 11 placeholder tutorial URLs, 20 reward `.blend` names plus licenses, same-object/custom-origin/WIND behavior decisions, production cloud, and remaining UI/GPU decomposition.

## Verification

Committed-revision evidence:

- `verify_frozen.py`: `42/42 PASS`; `verify_codex_plugin.py`: `104/104 PASS`; exact predicate registry: 65 IDs / 85 catalog pairs with no `bpy` imports.
- `ruff check .`: PASS; full `pytest`: `455 passed`.
- All six Blender suites (`engine`, `lifecycle_stress`, `persistence`, `register`, `rewards`, `ui_visual`) passed on Blender 5.0.1, 5.1.2, and 5.2.0: `18/18 PASS` in disposable profiles.
- `extension validate`, `extension build`, and `server-generate` passed on all three versions from exact committed Git blobs. The exact canonical ZIP then passed a second `validate` and fresh one-package `server-generate` on all three versions.
- Fresh install/enable, installed-module identity, strict USER-repository resolution, installed Git-byte equality, native Extensions RNA, external Blender-owned removal, disabled/unimportable post-state, and data preservation passed on all three versions.
- The installed lifecycle runner failed closed on non-zero exit, missing PASS markers, Python traceback, `NameError`, access violation, `WinError`, warning/error markers, or changed archive bytes; the final three-version run emitted none of those forbidden conditions.
- Three sentinel files under each disposable `BlenderAchievements` directory retained exact size and SHA-256 across install, probe, removal, and post-removal probe. Real user progress was never addressed.
- The unchanged reset operator was separately exercised on all three versions: dialog cancellation preserved exact runtime state, persisted JSON, assets, and backup bytes; confirmation wrote a fresh current-schema profile while preserving `textures/`, `rewards/`, and the corrupt-backup sentinel.
- Headless Blender cannot open an interactive Preferences window (`screen.userpref_show.poll() == False`). The success branch is dynamically tested with loader-consumed `bl_info`, while real installed probes validate its target and native RNA; the final visible `Uninstall` click remains Blender-owned user interaction.

## Agents And Review

- Persistent `requirements_guardian` maintains the ignored session ledger and checks scope, done work, and remaining gates.
- Code/dead-code and component/instruction-drift/lookahead agents independently reproduced both false unlocks and the nested-uninstall crash on all supported versions.
- Independent component/instruction and code/dead-code reviews closed with `Critical 0 / Important 0` after the loader-consumed `bl_info` regression test. The final verification-review and explicit `/review` fallback use the exact artifact evidence above.

## Blockers

No current implementation blocker. Merge, tag, and GitHub Release remain intentionally unauthorized.

## Residual Risks

- The uninstall button intentionally opens Blender's filtered native card and requires the user to select `Uninstall`; one-click self-removal from add-on-owned Python is unsafe.
- Existing already-unlocked false-positive IDs are not revoked automatically. Use the existing confirmed reset for a clean retest.
- Real content remains absent: 219 referenced PNG files, 11 placeholder tutorial URLs, and 20 reward `.blend` names need owner-provided licensed content.
- Same-object predicate requirements, `custom_origin`, WIND/particle edge cases, production cloud, and remaining UI/GPU decomposition remain separate tasks.

## Next Start Prompt

Review Achievements 0.2.1 on `codex/backlog-technical-closeout` and draft PR #14. Read `AGENTS.md`, this handoff, ADR 0002, and ADR 0003. Confirm current CI/owner acceptance before any merge or version decision. Do not merge, tag, create a GitHub Release, touch real `~/BlenderAchievements`, overwrite the immutable 0.2.0 ZIP, or modify any `instance_matcher` information.
