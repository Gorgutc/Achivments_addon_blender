from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def test_catalog_module_is_safe_to_import_and_validates_current_content():
    catalog_path = ROOT / "achievements" / "catalog.py"
    assert catalog_path.is_file(), "missing catalog module"

    text = catalog_path.read_text(encoding="utf-8")
    assert "import bpy" not in text
    assert "BlenderAchievements" not in text
    assert "Path.home()" not in text

    from achievements import catalog

    assert catalog.validate_catalog() == []
    assert catalog.catalog_digest() == catalog.FROZEN_CATALOG_DIGEST


def test_catalog_counts_match_iteration_contract():
    from achievements import catalog

    counts = catalog.catalog_counts()

    assert counts["achievement_count"] == 105
    assert counts["lesson_count"] == 9
    assert counts["check_types"] == {"complex": 65, "stat": 40}
    assert counts["complex_step_total"] == 85
    assert counts["complex_step_range"] == [1, 4]
    assert counts["first_achievement_id"] == "first_vertex"
    assert counts["last_achievement_id"] == "geonode_domain_switch"
    assert counts["first_lesson_id"] == "lesson_vertices_basics"
    assert counts["last_lesson_id"] == "lesson_render_basics"


def test_lesson_links_and_reward_payloads_are_referentially_valid():
    from achievements import catalog

    lessons = {lesson["id"] for lesson in catalog.LESSONS_DEF}
    achievements = {item["id"] for item in catalog.ACHIEVEMENTS_DEF}

    assert len(achievements) == len(catalog.ACHIEVEMENTS_DEF)
    assert len(lessons) == len(catalog.LESSONS_DEF)
    assert all(
        item["lesson_id"] is None or item["lesson_id"] in lessons
        for item in catalog.ACHIEVEMENTS_DEF
    )

    for item in catalog.ACHIEVEMENTS_DEF:
        reward_type = item["reward_type"]
        reward_data = item["reward_data"]
        if reward_type == "none":
            assert reward_data == {}
        elif reward_type == "tutorial":
            assert reward_data["url"].startswith("http")
        elif reward_type in catalog.ASSET_REWARD_TYPES:
            assert reward_data["name"].startswith("ACH_")
            assert reward_data["description"]
            assert reward_data["blend_file"].startswith("rewards/")


def test_complex_achievements_have_unique_steps_and_runtime_checks():
    from achievements import catalog

    complex_achievements = [
        item for item in catalog.ACHIEVEMENTS_DEF if item["check_type"] == "complex"
    ]
    complex_ids = {item["complex_id"] for item in complex_achievements}
    step_total = sum(len(item["steps"]) for item in complex_achievements)

    assert len(complex_ids) == len(complex_achievements)
    assert step_total == catalog.catalog_counts()["complex_step_total"]
    for item in complex_achievements:
        step_checks = [step["check"] for step in item["steps"]]
        step_labels = [step["label"] for step in item["steps"]]
        assert item["stat_key"] == "_complex"
        assert 1 <= len(step_checks) <= 4
        assert len(step_checks) == len(set(step_checks))
        assert all(step_check for step_check in step_checks)
        assert all(label for label in step_labels)
