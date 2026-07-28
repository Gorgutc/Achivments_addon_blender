"""Pure XP and level progression rules for the Achievements add-on.

The Blender entrypoint imports these values, while tests and verification can
exercise the progression contract without importing :mod:`bpy`.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable, Mapping
from typing import Any

DIFFICULTY_XP = {
    "easy": 5,
    "medium": 10,
    "hard": 20,
}

LEVEL_BANDS = (20, 40, 80, 120, 140, 170, 200, 230, 260, 290)
MAX_LEVEL = 10
MAX_XP = 1550

LEVEL_TITLES = {
    1: "Новичок",
    2: "Начинающий",
    3: "Ньюблинг",
    4: "Ученик",
    5: "Умелец",
    6: "Мастеровой",
    7: "Эксперт",
    8: "Виртуоз",
    9: "Гуру",
    10: "Легенда",
}


if len(LEVEL_BANDS) != MAX_LEVEL or sum(LEVEL_BANDS) != MAX_XP:
    raise RuntimeError("level bands must define exactly ten levels ending at 1550 XP")


XP_LEVELS: list[dict[str, int]] = []
_xp_start = 0
for _level, _band_size in enumerate(LEVEL_BANDS, start=1):
    _xp_end = _xp_start + _band_size
    XP_LEVELS.append({"level": _level, "xp_start": _xp_start, "xp_end": _xp_end})
    _xp_start = _xp_end


def calculate_xp(
    achievements: Iterable[Mapping[str, Any]], unlocked: Collection[str]
) -> int:
    """Calculate derived XP from unlocked catalog IDs."""

    return sum(
        DIFFICULTY_XP.get(achievement.get("difficulty", "medium"), 10)
        for achievement in achievements
        if achievement.get("id") in unlocked
    )


def calculate_level(xp: int) -> tuple[int, float, int, int]:
    """Return the legacy ``(level, progress, range, current)`` tuple."""

    for entry in XP_LEVELS:
        if xp < entry["xp_end"]:
            band_size = entry["xp_end"] - entry["xp_start"]
            band_current = xp - entry["xp_start"]
            return (
                entry["level"],
                band_current / band_size,
                band_size,
                band_current,
            )
    return MAX_LEVEL, 1.0, 0, 0


def format_level_progress(
    progress: float,
    level_range: int,
    level_current: int,
    *,
    bar_length: int = 12,
) -> str:
    """Format a level band, reserving ``MAX`` for the completed cap tuple."""

    if level_range == 0:
        return "MAX"
    filled = int(progress * bar_length)
    bar = "█" * filled + "░" * (bar_length - filled)
    return f"{bar} {level_current}/{level_range}"
