"""Safe Python package shell for the Achievements Blender add-on.

This package intentionally stays free of ``bpy`` imports and filesystem side
effects while the current Blender entrypoint remains the repository root
``__init__.py``.
"""

from __future__ import annotations

from .metadata import (
    ADDON_NAME,
    ADDON_VERSION,
    BLENDER_COMPATIBILITY_FLOOR,
    CANARY_VALIDATION_TARGET,
    PRIMARY_VALIDATION_TARGET,
)

__all__ = [
    "ADDON_NAME",
    "ADDON_VERSION",
    "BLENDER_COMPATIBILITY_FLOOR",
    "CANARY_VALIDATION_TARGET",
    "PRIMARY_VALIDATION_TARGET",
]
