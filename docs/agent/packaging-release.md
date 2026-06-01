# Packaging And Release

Current package state: draft `blender_manifest.toml` exists, and a safe `achievements/` Python package skeleton exists. This is not a release-ready extension package yet.

The new `achievements/` package is not a functional extension entrypoint. Current Blender registration still lives in the repository root `__init__.py`, and no runtime delegation has been enabled.

Future release work should decide:
- Whether `__init__.py` remains the package entry point.
- How to validate that `achievements_v01 (4).py` remains a permanent byte-identical duplicate unless the user explicitly changes that policy.
- Whether the draft manifest metadata needs changes before validation/build.
- How `.blend` reward assets are packaged and validated.
- Whether `bl_info` is updated to Blender 5.0+.
- Which smoke suites are required before release.

Until the release task is started, release packaging checks are non-blocking. Do not create release archives from this draft layer alone.
