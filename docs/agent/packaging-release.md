# Packaging And Release

Current package state is documentation-only for this preparation task.

Future release work should decide:
- Whether `__init__.py` remains the package entry point.
- Whether the duplicate `achievements_v01 (4).py` is removed or archived.
- Whether a Blender extension manifest is introduced.
- How `.blend` reward assets are packaged and validated.
- Whether `bl_info` is updated to Blender 5.0+.
- Which smoke suites are required before release.

Until that task is started, release packaging checks are non-blocking. Do not create release archives from this preparation layer alone.
