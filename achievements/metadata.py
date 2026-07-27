"""Shared metadata for the modular Achievements runtime package."""

from __future__ import annotations

ADDON_NAME = "Achievements"
ADDON_VERSION = (0, 2, 1)
BLENDER_COMPATIBILITY_FLOOR = (5, 0, 0)
MINIMUM_VALIDATION_TARGET = "Blender 5.0.1"
PRIMARY_VALIDATION_TARGET = "Blender 5.1.2"
LATEST_VALIDATION_TARGET = "Blender 5.2.0"

# Deprecated compatibility alias for repo integrations that still import the
# previous name.  Blender 5.2 is now a blocking release target, not a canary.
CANARY_VALIDATION_TARGET = LATEST_VALIDATION_TARGET
