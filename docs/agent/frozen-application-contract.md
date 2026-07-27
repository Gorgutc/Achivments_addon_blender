# Frozen Application Contract

This document freezes the current `main` behavior of the Achievements Blender add-on. Future edits must be narrow: change only the requested behavior and preserve every unrelated rule, UI decision, data shape, and lifecycle decision below unless the user explicitly asks to change it.

## Source Of Truth

- Canonical add-on runtime entrypoint: `__init__.py`.
- Catalog source of truth: `achievements/catalog.py`.
- Offline sync planning source: `achievements/sync.py`.
- Predicate source of truth: the exact registry under `achievements/predicates/`; root `_check_complex_step` is the Blender-facing adapter.
- Integrity source of truth: `achievements/integrity.py`; root hash functions remain compatibility wrappers.
- Retired duplicate: `achievements_v01 (4).py` is intentionally absent; ADR 0002 preserves exact Git recovery evidence.
- Stale reference file: `docs/archive/achievements_100_list.md` preserves an older 100-achievement design byte-for-byte and is not the current source of truth.
- README is useful orientation but the executable contract is the add-on code, `achievements/catalog.py`, and this frozen contract.
- Source strings are UTF-8 Russian user-facing text. Mojibake in terminal output is a display/encoding artifact, not permission to normalize or rewrite all text.

## Application Identity

- Add-on name: `Achievements`.
- Author: `axximus`.
- Version: `(0, 2, 0)`.
- Minimum `bl_info["blender"]`: `(5, 0, 0)`.
- Location: `3D Viewport > Header (trophy icon)`.
- Category: `Interface`.
- Product concept: Blender gamification with achievements, XP/levels, rewards, tutorials, popups, and pinning.

## Catalog Freeze

- Achievements: 105 total in `achievements/catalog.py`.
- Lessons: 9 total in `achievements/catalog.py`.
- Achievement check types: 40 `stat`, 65 `complex`.
- Complex steps: 85 total, with 1 to 4 steps per complex achievement.
- Achievement categories: `EDITING` 45, `MATERIALS` 17, `RENDERING` 17, `TIME` 12, `GEO_NODES` 14.
- Lesson categories: `EDITING` 5, `MATERIALS` 1, `TIME` 1, `GEO_NODES` 1, `RENDERING` 1.
- Difficulty counts: `easy` 10, `medium` 40, `hard` 55.
- Reward type counts: `none` 82, `tutorial` 2, `material` 11, `geo_nodes` 5, `mesh` 5.
- Reward category counts in achievements: `MESHES` 38, `SHADERS` 49, `GEO_NODES` 18.
- Reward categories declared by UI: `MESHES`, `GEO_NODES`, `SHADERS`, `COMPOSITOR`. `COMPOSITOR` currently has zero achievement entries and must not be removed casually.

Do not reorder, rename, or delete IDs, category keys, stat keys, complex IDs, reward categories, lesson IDs, or achievement IDs unless the task explicitly asks for a catalog behavior change.

## Achievement Schema

Every achievement entry keeps these fields:
- `id`
- `title`
- `description`
- `goal`
- `stat_key`
- `category`
- `check_type`
- `difficulty`
- `reward_type`
- `reward_data`
- `reward_category`
- `lesson_id`
- `icon_gray`
- `icon_color`

Complex achievements additionally keep:
- `complex_id`
- `steps`, with each step containing `label` and `check`.

Stat achievements must not define `complex_id` or `steps`. Complex achievements must use `stat_key == "_complex"`.

## Stats And Persistence

Runtime data path is resolved at import time but created lazily during registration/save:
- `~/BlenderAchievements/`
- `~/BlenderAchievements/achievements_data.json`
- `~/BlenderAchievements/textures/`
- `~/BlenderAchievements/rewards/`

JSON persistence keys:
- `schema_version`
- `stats`
- `unlocked`
- `unlock_hashes`
- `rewards_claimed`
- `pinned_ach_id`
- `daily_sessions`

Sync payloads intentionally exclude `pinned_ach_id` by default. Pinned overlay state is local UI state, not cloud state, unless a future task explicitly changes that contract.

Current persistence schema version: `1.0.0`.

Persisted stat fields:
- `vertices_created`
- `vertices_deleted`
- `edges_created`
- `faces_created`
- `meshes_1000plus`
- `materials_applied`
- `time_spent`
- `renders_completed`

Internal session fields track active time, idle gaps, mesh/material snapshots, daily streaks, and speed-modeler windows. Persistence writes are same-directory atomic JSON writes through a temp file, flush/fsync, and `os.replace`. Legacy JSON without current `schema_version` is migrated idempotently and may backfill a missing unlock marker. A current-schema payload never repairs a missing or forged marker. Corrupt JSON is quarantined beside the data file as `achievements_data.json.corrupt*` and a current-schema default file is recreated. Stat threshold evaluation, complex-step aggregation, proof/result DTOs, and progress interfaces live in pure `achievements/engine.py`; scene predicates live in pure `achievements/predicates/` and receive duck-typed Blender state from the root adapter. Do not change persistence shape, path, corrupt-file recovery, active-time semantics, or rule/progress contracts without an explicit migration task.

## Cloud Sync Stub

- Cloud sync is offline-first and disabled by default.
- `achievements/sync.py` stays pure Python with no `bpy` import, no user-home path assumptions, and no production network imports.
- `DisabledSyncBackend` exposes no transport hook and only returns disabled results.
- `SyncQueue` stores pending changes deterministically and deduplicates by `change_id`.
- Conflict decisions are deterministic: newer `updated_at` wins; equal timestamps prefer local source priority; full ties use stable lexical `change_id`.
- Normal add-on use must make no network calls. A production backend, identity model, auth flow, remote authority, and retry policy require a separate future task.

## XP And Levels

- Difficulty XP: `easy = 5`, `medium = 10`, `hard = 20`.
- Level thresholds double from 20 XP for level 1 to 2, through 10 levels.
- Level 10 is the cap and displays `MAX`.
- Level title keys are 1 through 10 and are part of the UI contract.

## Reward Rules

- Unlock integrity uses the legacy salt, the unchanged `os.getlogin()` value when available, SHA-256, and the first 16 hex characters through pure `make_unlock_hash`/`verify_unlock_hash` helpers. Headless sessions fall back to `getpass.getuser()` and finally the fixed `unknown-user` value only when username resolution raises `OSError`.
- The hash is a local integrity marker, not authentication or anti-cheat.
- Rewards can be applied only when the achievement is unlocked and the stored unlock hash verifies.
- `tutorial` rewards open URLs.
- `none` rewards do nothing and stay claim-free.
- `material`, `mesh`, and `geo_nodes` rewards load assets from `~/BlenderAchievements/rewards/` via `.blend` libraries when present.
- Missing asset fallbacks are intentional: generated material, ico sphere mesh, or node modifier placeholder.
- Material rewards overwrite all material slots on the active mesh.
- Mesh rewards link loaded objects into the active collection.
- Geo node rewards create a `NODES` modifier on the active object.
- Reward manifest, verifier, asset-existence cache, importer/action planning, and manager decisions live in pure `achievements/rewards.py`; Blender asset linking and placeholder creation remain runtime adapter behavior in the root operator.
- Bundled reward `.blend` assets remain release-blocked until asset licenses are explicitly approved; missing-asset fallback behavior is the intentional default before that decision.

## UI Design Freeze

Global layout:
- Main entry is a 3D Viewport header button: `Achievements (unlocked/total)`.
- Popup width is derived from `GRID_COLS * _CARD_W * _UNIT + 80`.
- Popup width, tab specs, pagination plans, Scene property specs, overlay frame geometry, storage filters, and reward labels are planned by pure `achievements/ui.py`; root `__init__.py` remains the Blender layout/GPU adapter.
- Grid is 2 columns by 5 rows, 10 cards per page.
- The stats box exposes a `Сбросить прогресс` button (`ach.reset_achievements`) that fully resets the profile after a confirmation dialog; this is an explicit testing/dev affordance.
- Cards are horizontal: icon on the left, text and actions on the right.
- Icons are 100x100 via `CARD_ICON_UNITS = 5.0`.
- Card width is `_CARD_W = 15.6`.
- Pagination uses left/right triangle icons and page text.

Tabs:
- `TASKS`: locked/uncompleted achievements.
- `DONE`: unlocked achievements.
- `LESSONS`: lesson cards.
- `STORAGE`: unlocked material/mesh/geo node rewards.

Accordions:
- Tasks default `EDITING` open; other task categories closed.
- Done, lessons, and storage accordions default closed.
- Accordion state is stored in `bpy.types.Scene` properties.

Achievement cards:
- Locked achievement title and description are disabled.
- Difficulty and XP appear inline in the title row.
- Stat achievements show a block-character progress bar with value/goal/percent.
- Complex achievements show step rows plus done-step count and percent.
- Pin button appears on task cards only.
- Reward label appears when reward type is not `none`.
- Reward action appears on unlocked cards only.

Lesson cards:
- Lesson cards use the same unified card layout.
- Linked achievement progress is shown as done/total when linked achievements exist.
- Lesson URL button opens via `ach.open_tutorial`.

Storage:
- Storage shows only unlocked achievements with reward type `material`, `mesh`, or `geo_nodes`.
- Storage is grouped by reward category.

## Overlay And Notification Design

Notifications:
- Steam-style bottom-left GPU overlay.
- Duration: 8 seconds.
- Slide-in: 0.4 seconds.
- Fade-out: last 2 seconds.
- Size: 500x132 px.
- Margin: 20 px.
- Icon placeholder: 100x100 px.
- Green left stripe.
- Three text lines: achievement received label, title, description.

Pinned achievement overlay:
- Same size and bottom-left origin as notifications.
- Yellow left stripe.
- Sits above active notifications.
- Shows current progress.
- Auto-unpins when the achievement unlocks.

Do not replace GPU overlay behavior with panel-only UI unless explicitly requested.

## Runtime Lifecycle

Registration registers:
- Eight operator classes.
- `bpy.types.Scene` tab/page/accordion properties.
- `depsgraph_update_post`, `load_post`, `save_pre`, and `render_complete` handlers.
- `_timer_tick` and `_notification_redraw_tick` timers.
- `VIEW3D_HT_header` draw callback.
- Two `SpaceView3D` GPU draw handlers.

Unregistration must clean all of the above symmetrically and clear preview collections. Repeated register/unregister must be safe in background Blender smoke. The root entrypoint delegates idempotent class, Scene property, handler, timer, header, and draw-handler wiring to `achievements/lifecycle.py`; stat/complex rule orchestration and proof/progress helpers delegate to `achievements/engine.py`; reward decision planning delegates to `achievements/rewards.py`; activity/session tracking and cached scene snapshot resets delegate to `achievements/events.py`.

## Function Map

Security and XP:
- `_make_unlock_hash`
- `_verify_unlock`
- `_calc_xp`
- `_calc_level`
- `_difficulty_label`

Persistence and activity:
- `_on_user_activity`
- `_flush_session_time`
- `_ensure_data_dirs`
- `save_data`
- `load_data`

GPU overlays:
- `_add_notification`
- `_tag_redraw_all`
- `_draw_rect`
- `_reward_type_label`
- `_draw_notifications`
- `_draw_pinned_achievement`

Achievement checking:
- `check_achievements`
- `_unlock_achievement`
- `_check_complex_step`
- `_check_complex`
- `check_complex_achievements`
- `_get_mesh_counts`

Blender handlers and timers:
- `on_depsgraph_update`
- `on_load_post`
- `on_save_pre`
- `on_render_complete`
- `_timer_tick`
- `_notification_redraw_tick`

Icons and previews:
- `_ensure_icons`
- `_get_icon_id`

Operators:
- `ACH_OT_OpenWindow`
- `ACH_OT_OpenTutorial`
- `ACH_OT_ApplyReward`
- `ACH_OT_PinAchievement`
- `ACH_OT_PagePrev`
- `ACH_OT_PageNext`
- `ACH_OT_ResetAchievements`
- `ACH_OT_AchievementsDialog`

UI helpers:
- `achievements/ui.py`
- `achievements.ui.ease_out_cubic`
- `_tab_prop`
- `_draw_unified_card`
- `_draw_grid_page`
- `_draw_header_button`

Lifecycle:
- `_base_scene_properties`
- `_category_scene_properties`
- `_scene_property_names`
- `_register_scene_properties`
- `_unregister_scene_properties`
- `_handler_pairs`
- `_register_handlers`
- `_unregister_handlers`
- `_register_timers`
- `_unregister_timers`
- `_register_draw_handlers`
- `_unregister_draw_handlers`
- `register`
- `unregister`

## Future Change Rule

Before editing add-on behavior:
1. Identify the exact frozen section affected.
2. Confirm whether the user explicitly requested a behavior/design/data change.
3. Keep unrelated sections unchanged.
4. Update this contract and verifiers only when the accepted behavior changes.
5. Run static verification and Blender smoke appropriate to the touched surface.

## Required Verification Coverage

- `verify_frozen.py` freezes catalog digest/counts/schema keys, UI/runtime constants, top-level function map, class map, registered classes, strict predicate-registry bijection, duplicate absence/recovery evidence, archived-list Git blob, tracked-data safety, and this contract.
- `verify_codex_plugin.py` freezes Codex docs, skills, hooks, agents, and required tracked infra files.
- Blender `register` smoke freezes registration cleanup.
- Blender `lifecycle_stress` smoke freezes repeated register/unregister cleanup, handler counts, timer cleanup, draw handler identity, and hot-reload idempotency.
- Blender `persistence` smoke freezes temp-home JSON schema, save/load, legacy unlock-hash migration, current-schema missing/forged marker preservation, current `schema_version`, atomic current-schema save, and corrupt JSON quarantine/recovery.
- Blender `engine` smoke freezes compositor/render-pass complex checks so they do not emit `[Achievements] complex step check error` markers.
- Blender `rewards` smoke freezes material, mesh, and geo node fallback behavior plus reward claim persistence.
- Blender `ui_visual` smoke freezes UI geometry planning, tab state acceptance, non-overlap overlay stacking, and a generated visual contract artifact for header/popup/cards/notifications/pinned overlay.
