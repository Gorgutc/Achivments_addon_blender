from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def sample_achievements():
    return [
        {
            "id": "todo_edit",
            "category": "EDITING",
            "reward_type": "none",
            "reward_category": "MESHES",
        },
        {
            "id": "done_material",
            "category": "MATERIALS",
            "reward_type": "material",
            "reward_category": "SHADERS",
        },
        {
            "id": "done_mesh",
            "category": "EDITING",
            "reward_type": "mesh",
            "reward_category": "MESHES",
        },
        {
            "id": "done_tutorial",
            "category": "TIME",
            "reward_type": "tutorial",
            "reward_category": "GEO_NODES",
        },
    ]


def test_ui_module_is_safe_to_import_and_exposes_contract_types():
    ui_path = ROOT / "achievements" / "ui.py"
    assert ui_path.is_file(), "missing Iteration 9 UI module"

    text = ui_path.read_text(encoding="utf-8")
    assert "import bpy" not in text
    assert "BlenderAchievements" not in text
    assert "Path.home()" not in text

    from achievements import ui

    assert ui.TabSpec
    assert ui.ScenePropertySpec
    assert ui.GridPagePlan
    assert ui.OverlayFrame
    assert ui.TABS[0].key == "TASKS"
    assert [tab.key for tab in ui.TABS] == ["TASKS", "DONE", "LESSONS", "STORAGE"]
    assert [tab.label for tab in ui.TABS] == ["Задания", "Выполнено", "Уроки", "Хранилище"]


def test_scene_property_specs_preserve_tabs_categories_and_defaults():
    from achievements import ui
    from achievements.catalog import ACH_CATEGORIES, REWARD_CATEGORIES

    base = ui.base_scene_property_specs()
    category = ui.category_scene_property_specs(ACH_CATEGORIES, REWARD_CATEGORIES)
    names = ui.scene_property_names(ACH_CATEGORIES, REWARD_CATEGORIES)

    assert base[0] == ui.ScenePropertySpec(
        name="ach_tab",
        kind="enum",
        default="TASKS",
        items=tuple((tab.key, tab.label, "") for tab in ui.TABS),
    )
    assert "ach_page_tasks" in names
    assert "ach_page_storage" in names
    assert ui.ScenePropertySpec(
        name="ach_acc_tasks_EDITING",
        kind="bool",
        default=True,
    ) in category
    assert ui.ScenePropertySpec(
        name="ach_acc_done_EDITING",
        kind="bool",
        default=False,
    ) in category
    assert ui.ScenePropertySpec(
        name="ach_acc_storage_SHADERS",
        kind="bool",
        default=False,
    ) in category
    assert ui.tab_page_property("TASKS") == "ach_page_tasks"
    assert ui.tab_page_property("DONE_EDITING") == "ach_page_done_editing"
    assert ui.tab_page_property("STORAGE_GEO_NODES") == "ach_page_storage_geo_nodes"


def test_grid_pagination_popup_width_and_overlay_geometry_are_stable():
    from achievements import ui

    page = ui.grid_page_plan(total_items=23, current_page=4)
    assert page == ui.GridPagePlan(
        page=2,
        total_pages=3,
        start=20,
        end=30,
        page_size=10,
        empty_slots=1,
    )
    assert ui.popup_dialog_width() == 704

    entering = ui.notification_frame(index=0, elapsed=0.0)
    settled = ui.notification_frame(index=1, elapsed=ui.NOTIFY_SLIDE_IN)
    fading = ui.notification_frame(index=0, elapsed=ui.NOTIFY_DURATION - 1.0)
    pinned = ui.pinned_frame(notification_count=2)

    assert entering.x == 20
    assert entering.y == -132
    assert entering.alpha == 0.0
    assert settled.x == 20
    assert settled.y == 162
    assert settled.alpha == 1.0
    assert fading.alpha == 0.5
    assert pinned.y == 314
    assert pinned.icon_rect == (36, 330.0, 100, 100)
    assert pinned.text_x == 152
    assert pinned.progress_bar_width == 302


def test_tab_item_filters_and_category_grouping_preserve_storage_contract():
    from achievements import ui

    achievements = sample_achievements()
    unlocked = {"done_material", "done_mesh", "done_tutorial"}

    assert [item["id"] for item in ui.task_items(achievements, unlocked)] == ["todo_edit"]
    assert [item["id"] for item in ui.done_items(achievements, unlocked)] == [
        "done_material",
        "done_mesh",
        "done_tutorial",
    ]
    assert [item["id"] for item in ui.storage_items(achievements, unlocked)] == [
        "done_material",
        "done_mesh",
    ]
    assert [item["id"] for item in ui.items_for_category(
        achievements,
        "EDITING",
        key="category",
    )] == ["todo_edit", "done_mesh"]
    assert ui.reward_type_label("material") == "Награда: материал"


def test_long_ru_and_en_text_is_budgeted_for_cards_and_overlays():
    from achievements import ui

    short_ru = "Короткое имя"
    long_ru = "Очень длинное русское описание достижения для проверки компактной карточки"
    long_en = "A very long English achievement description for compact overlay rendering"

    assert ui.fit_text(short_ru, max_chars=20) == short_ru
    assert ui.fit_text(long_ru, max_chars=24).endswith("...")
    assert len(ui.fit_text(long_ru, max_chars=24)) <= 24
    assert len(ui.card_title_text(long_ru)) <= ui.CARD_TITLE_MAX_CHARS
    assert len(ui.card_description_text(long_en)) <= ui.CARD_DESCRIPTION_MAX_CHARS
    assert len(ui.overlay_title_text(long_ru)) <= ui.OVERLAY_TITLE_MAX_CHARS
    assert len(ui.overlay_description_text(long_en)) <= ui.OVERLAY_DESCRIPTION_MAX_CHARS
