# ADR 0003: Safe Extension Removal And Render Events

Status: accepted for Achievements 0.2.1.

## Context

The add-on needs an accessible removal path during development. Calling Blender's extension-uninstall operator from an executing add-on-owned operator was reproduced as an access-violation crash on Blender 5.0.1, 5.1.2, and 5.2.0. Progress lives outside the installed package under `~/BlenderAchievements/` and must not be coupled to package removal.

Two complex predicates also treated passive Blender defaults as completed work. Principled BSDF has nonzero `Subsurface Scale` and `Subsurface IOR` even when `Subsurface Weight` is zero. Cycles denoising can be enabled while Eevee is active and before any render occurs.

## Decision

- `ach.open_extension_manager` is navigation only. It resolves the exact installed `bl_ext.<repo>.achievements` package against one enabled `USER` repository and a matching package directory, then opens Blender's `Extensions` section filtered to the installed `Achievements` card.
- Runtime navigation reads the stable `achievements.metadata.ADDON_NAME`; it does not read root `bl_info` after import because Blender's extension loader may consume and remove that mapping.
- Blender owns the final `Uninstall` action after add-on code returns. Add-on-owned operators never call `extensions.package_uninstall`, never use legacy `preferences.addon_remove`, and never delete package files manually.
- Package removal preserves `~/BlenderAchievements/`. The existing confirmed `Сбросить прогресс` action remains separate and unchanged.
- `subsurface_skin` accepts only an active or linked exact `Subsurface Weight` input, with the exact legacy `Subsurface` socket retained as a compatibility fallback.
- `denoiser_render` requires a transient `render_complete` event, `scene.render.engine == "CYCLES"`, and `scene.cycles.use_denoising`. Generic timer and dependency-graph checks have no event and therefore cannot unlock it.
- The render handler evaluates the scene supplied by Blender, not an unrelated ambient context scene.

## Consequences

The removal flow requires a final user action in Blender's own extension card but avoids unloading Python code while its operator is still executing. Existing unlocked IDs are not revoked automatically; developers can use the existing reset command for a clean retest. The persistence schema remains `1.0.0`, and catalog IDs and external data paths do not change.
