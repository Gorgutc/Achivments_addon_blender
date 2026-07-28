from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

catalog = importlib.import_module("achievements.catalog")
levels = importlib.import_module("achievements.levels")
persistence = importlib.import_module("achievements.persistence")


EXPECTED_DIFFICULTY_XP = {"easy": 5, "medium": 10, "hard": 20}
EXPECTED_BANDS = (20, 40, 80, 120, 140, 170, 200, 230, 260, 290)
EXPECTED_STARTS = (0, 20, 60, 140, 260, 400, 570, 770, 1000, 1260)
EXPECTED_ENDS = (20, 60, 140, 260, 400, 570, 770, 1000, 1260, 1550)
LEGACY_STARTS = (0, 20, 60, 140, 300, 620, 1260, 2540, 5100, 10220)
EXPECTED_TITLES = {
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


def _achievement_xp(achievement: dict) -> int:
    return levels.DIFFICULTY_XP.get(achievement.get("difficulty", "medium"), 10)


def _reachable_xp() -> set[int]:
    reachable = {0}
    for achievement in catalog.ACHIEVEMENTS_DEF:
        award = _achievement_xp(achievement)
        reachable |= {xp + award for xp in tuple(reachable)}
    return reachable


def _level_from_starts(xp: int, starts: tuple[int, ...]) -> int:
    return max(level for level, start in enumerate(starts, start=1) if xp >= start)


def test_level_module_is_pure_and_contract_values_are_exact():
    source = (ROOT / "achievements" / "levels.py").read_text(encoding="utf-8")

    assert "import bpy" not in source
    assert levels.DIFFICULTY_XP == EXPECTED_DIFFICULTY_XP
    assert levels.LEVEL_BANDS == EXPECTED_BANDS
    assert levels.MAX_LEVEL == 10
    assert levels.MAX_XP == 1550
    assert levels.LEVEL_TITLES == EXPECTED_TITLES
    assert [
        {"level": level, "xp_start": start, "xp_end": end}
        for level, (start, end) in enumerate(
            zip(EXPECTED_STARTS, EXPECTED_ENDS, strict=True), start=1
        )
    ] == levels.XP_LEVELS


@pytest.mark.parametrize(
    ("level", "start", "end"),
    [
        (level, start, end)
        for level, (start, end) in enumerate(
            zip(EXPECTED_STARTS, EXPECTED_ENDS, strict=True), start=1
        )
    ],
)
def test_calculate_level_boundaries(level: int, start: int, end: int):
    band_size = end - start

    assert levels.calculate_level(start) == (level, 0.0, band_size, 0)
    assert levels.calculate_level(end - 1) == (
        level,
        pytest.approx((band_size - 1) / band_size),
        band_size,
        band_size - 1,
    )

    if end < levels.MAX_XP:
        next_band = EXPECTED_BANDS[level]
        assert levels.calculate_level(end) == (level + 1, 0.0, next_band, 0)
    else:
        assert levels.calculate_level(end) == (levels.MAX_LEVEL, 1.0, 0, 0)


def test_level_ten_progress_is_not_formatted_as_max_before_cap():
    _level, progress, level_range, level_current = levels.calculate_level(1260)
    assert levels.format_level_progress(progress, level_range, level_current) == (
        "░" * 12 + " 0/290"
    )

    _level, progress, level_range, level_current = levels.calculate_level(1549)
    assert levels.format_level_progress(progress, level_range, level_current) == (
        "█" * 11 + "░ 289/290"
    )

    _level, progress, level_range, level_current = levels.calculate_level(levels.MAX_XP)
    assert levels.format_level_progress(progress, level_range, level_current) == "MAX"


def test_calculate_xp_preserves_legacy_medium_fallback_and_ignores_locked_ids():
    achievements = [
        {"id": "easy", "difficulty": "easy"},
        {"id": "missing_difficulty"},
        {"id": "unknown_difficulty", "difficulty": "legendary"},
        {"id": "locked_hard", "difficulty": "hard"},
    ]

    assert levels.calculate_xp(
        achievements,
        {"easy", "missing_difficulty", "unknown_difficulty", "stale_id"},
    ) == 25


def test_catalog_subset_sums_cover_exact_reachable_state_space():
    reachable = _reachable_xp()

    assert reachable == set(range(0, levels.MAX_XP + 1, 5))
    assert set(EXPECTED_STARTS) <= reachable


def test_catalog_max_xp_matches_cap_and_only_full_catalog_is_max():
    all_ids = {achievement["id"] for achievement in catalog.ACHIEVEMENTS_DEF}
    all_xp = levels.calculate_xp(catalog.ACHIEVEMENTS_DEF, all_ids)

    assert len(all_ids) == len(catalog.ACHIEVEMENTS_DEF) == 105
    assert all_xp == levels.MAX_XP
    assert levels.calculate_level(all_xp) == (levels.MAX_LEVEL, 1.0, 0, 0)

    easy_id = next(
        achievement["id"]
        for achievement in catalog.ACHIEVEMENTS_DEF
        if achievement["difficulty"] == "easy"
    )
    proper_subset = all_ids - {easy_id}
    proper_subset_xp = levels.calculate_xp(catalog.ACHIEVEMENTS_DEF, proper_subset)

    assert len(proper_subset) == 104
    assert proper_subset_xp == levels.MAX_XP - levels.DIFFICULTY_XP["easy"]
    assert levels.calculate_level(proper_subset_xp) == (
        levels.MAX_LEVEL,
        pytest.approx(285 / 290),
        290,
        285,
    )
    assert levels.calculate_xp(catalog.ACHIEVEMENTS_DEF, {"unknown_stale_id"}) == 0


def test_rebalance_never_lowers_legacy_level_or_promotes_by_more_than_three():
    deltas = []

    for xp in sorted(_reachable_xp()):
        legacy_level = _level_from_starts(xp, LEGACY_STARTS)
        new_level = levels.calculate_level(xp)[0]
        delta = new_level - legacy_level
        assert delta >= 0
        assert delta <= 3
        deltas.append(delta)

    assert max(deltas) == 3


def test_default_persistence_payload_does_not_store_derived_progression():
    payload = persistence.default_payload()

    assert "xp" not in payload
    assert "level" not in payload
    assert "xp" not in payload["stats"]
    assert "level" not in payload["stats"]
