"""Pure UI planning helpers for the Achievements add-on.

This module owns UI contracts and geometry calculations. Blender-specific
layout, ``bpy`` operators, GPU drawing, and icon loading stay in the root
runtime adapter.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

GRID_COLS = 2
GRID_ROWS = 5
PAGE_SIZE = GRID_COLS * GRID_ROWS

CARD_WIDTH_UNITS = 15.6
CARD_ICON_UNITS = 5.0
UNIT = 20.0
CARD_HEIGHT_UNITS = 5.0
ICON_UNITS = 5.0
GAP_UNITS = 0.8

NOTIFY_DURATION = 8.0
NOTIFY_SLIDE_IN = 0.4
NOTIFY_ICON_SIZE = 100
NOTIFY_PADDING = 16
NOTIFY_TEXT_GAP = 8
NOTIFY_HEIGHT = NOTIFY_ICON_SIZE + NOTIFY_PADDING * 2
NOTIFY_WIDTH = 500
NOTIFY_MARGIN = 20
OVERLAY_STACK_GAP = 10
PIN_MARGIN_X = NOTIFY_MARGIN
PIN_MARGIN_Y = NOTIFY_MARGIN

ASSET_REWARD_TYPES = {"material", "mesh", "geo_nodes"}
CARD_TITLE_MAX_CHARS = 48
CARD_DESCRIPTION_MAX_CHARS = 64
OVERLAY_TITLE_MAX_CHARS = 34
OVERLAY_DESCRIPTION_MAX_CHARS = 42


@dataclass(frozen=True)
class TabSpec:
    key: str
    label: str


@dataclass(frozen=True)
class ScenePropertySpec:
    name: str
    kind: str
    default: Any
    items: tuple[tuple[str, str, str], ...] = ()
    min_value: int | None = None


@dataclass(frozen=True)
class GridPagePlan:
    page: int
    total_pages: int
    start: int
    end: int
    page_size: int
    empty_slots: int


@dataclass(frozen=True)
class OverlayFrame:
    x: float
    y: float
    width: int
    height: int
    alpha: float
    icon_rect: tuple[float, float, int, int]
    text_x: float
    progress_bar_width: float


TABS = (
    TabSpec("TASKS", "Задания"),
    TabSpec("DONE", "Выполнено"),
    TabSpec("LESSONS", "Уроки"),
    TabSpec("STORAGE", "Хранилище"),
)

TAB_PAGE_PROPERTIES = {
    "TASKS": "ach_page_tasks",
    "DONE": "ach_page_done",
    "LESSONS": "ach_page_lessons",
    "STORAGE": "ach_page_storage",
}

REWARD_TYPE_LABELS = {
    "tutorial": "Награда: урок",
    "material": "Награда: материал",
    "mesh": "Награда: меш",
    "geo_nodes": "Награда: Geometry Nodes",
    "none": "",
}


def base_scene_property_specs() -> tuple[ScenePropertySpec, ...]:
    return (
        ScenePropertySpec(
            name="ach_tab",
            kind="enum",
            default="TASKS",
            items=tuple((tab.key, tab.label, "") for tab in TABS),
        ),
        ScenePropertySpec("ach_page_tasks", "int", 0, min_value=0),
        ScenePropertySpec("ach_page_done", "int", 0, min_value=0),
        ScenePropertySpec("ach_page_lessons", "int", 0, min_value=0),
        ScenePropertySpec("ach_page_storage", "int", 0, min_value=0),
    )


def category_scene_property_specs(
    achievement_categories: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    reward_categories: list[tuple[str, str]] | tuple[tuple[str, str], ...],
) -> tuple[ScenePropertySpec, ...]:
    specs: list[ScenePropertySpec] = []
    for category_id, _label in achievement_categories:
        specs.extend(
            (
                ScenePropertySpec(
                    f"ach_acc_tasks_{category_id}", "bool", category_id == "EDITING"
                ),
                ScenePropertySpec(f"ach_acc_done_{category_id}", "bool", False),
                ScenePropertySpec(f"ach_acc_lessons_{category_id}", "bool", False),
                ScenePropertySpec(
                    f"ach_page_tasks_{category_id.lower()}", "int", 0, min_value=0
                ),
                ScenePropertySpec(
                    f"ach_page_done_{category_id.lower()}", "int", 0, min_value=0
                ),
                ScenePropertySpec(
                    f"ach_page_lessons_{category_id.lower()}", "int", 0, min_value=0
                ),
            )
        )
    for category_id, _label in reward_categories:
        specs.extend(
            (
                ScenePropertySpec(f"ach_acc_storage_{category_id}", "bool", False),
                ScenePropertySpec(
                    f"ach_page_storage_{category_id.lower()}", "int", 0, min_value=0
                ),
            )
        )
    return tuple(specs)


def scene_property_names(
    achievement_categories: list[tuple[str, str]] | tuple[tuple[str, str], ...],
    reward_categories: list[tuple[str, str]] | tuple[tuple[str, str], ...],
) -> list[str]:
    return [
        *(spec.name for spec in base_scene_property_specs()),
        *(spec.name for spec in category_scene_property_specs(achievement_categories, reward_categories)),
    ]


def tab_page_property(tab_key: str) -> str:
    if tab_key in TAB_PAGE_PROPERTIES:
        return TAB_PAGE_PROPERTIES[tab_key]
    return f"ach_page_{tab_key.lower()}"


def grid_page_plan(total_items: int, current_page: int) -> GridPagePlan:
    total_pages = max(1, math.ceil(total_items / PAGE_SIZE))
    page = min(max(0, current_page), total_pages - 1)
    start = page * PAGE_SIZE
    end = start + PAGE_SIZE
    item_count = max(0, min(PAGE_SIZE, total_items - start))
    empty_slots = (GRID_COLS - item_count % GRID_COLS) % GRID_COLS
    return GridPagePlan(
        page=page,
        total_pages=total_pages,
        start=start,
        end=end,
        page_size=PAGE_SIZE,
        empty_slots=empty_slots,
    )


def popup_dialog_width() -> int:
    return int(GRID_COLS * CARD_WIDTH_UNITS * UNIT + 80)


def ease_out_cubic(t: float) -> float:
    t = max(0.0, min(1.0, t))
    return 1.0 - (1.0 - t) ** 3


def _overlay_frame(x: float, y: float, alpha: float) -> OverlayFrame:
    icon_x = x + NOTIFY_PADDING
    icon_y = y + (NOTIFY_HEIGHT - NOTIFY_ICON_SIZE) / 2
    text_x = icon_x + NOTIFY_ICON_SIZE + NOTIFY_PADDING
    progress_bar_width = NOTIFY_WIDTH - (text_x - x) - NOTIFY_PADDING - 50
    return OverlayFrame(
        x=x,
        y=y,
        width=NOTIFY_WIDTH,
        height=NOTIFY_HEIGHT,
        alpha=alpha,
        icon_rect=(icon_x, icon_y, NOTIFY_ICON_SIZE, NOTIFY_ICON_SIZE),
        text_x=text_x,
        progress_bar_width=progress_bar_width,
    )


def notification_frame(index: int, elapsed: float) -> OverlayFrame:
    alpha = 1.0
    if elapsed < NOTIFY_SLIDE_IN:
        alpha = ease_out_cubic(elapsed / NOTIFY_SLIDE_IN)
    elif elapsed > (NOTIFY_DURATION - 2.0):
        alpha = max(0.0, (NOTIFY_DURATION - elapsed) / 2.0)

    slide_t = ease_out_cubic(min(elapsed / NOTIFY_SLIDE_IN, 1.0))
    target_y = NOTIFY_MARGIN + index * (NOTIFY_HEIGHT + OVERLAY_STACK_GAP)
    y = target_y * slide_t - (NOTIFY_HEIGHT * (1.0 - slide_t))
    return _overlay_frame(NOTIFY_MARGIN, y, alpha)


def pinned_frame(notification_count: int) -> OverlayFrame:
    notification_offset = 0
    if notification_count:
        notification_offset = notification_count * (NOTIFY_HEIGHT + OVERLAY_STACK_GAP) + 10
    return _overlay_frame(PIN_MARGIN_X, PIN_MARGIN_Y + notification_offset, 1.0)


def reward_type_label(reward_type: str) -> str:
    return REWARD_TYPE_LABELS.get(reward_type, "")


def fit_text(text: str, *, max_chars: int) -> str:
    if max_chars <= 3:
        return text[:max_chars]
    if len(text) <= max_chars:
        return text
    return f"{text[: max_chars - 3].rstrip()}..."


def card_title_text(text: str) -> str:
    return fit_text(text, max_chars=CARD_TITLE_MAX_CHARS)


def card_description_text(text: str) -> str:
    return fit_text(text, max_chars=CARD_DESCRIPTION_MAX_CHARS)


def overlay_title_text(text: str) -> str:
    return fit_text(text, max_chars=OVERLAY_TITLE_MAX_CHARS)


def overlay_description_text(text: str) -> str:
    return fit_text(text, max_chars=OVERLAY_DESCRIPTION_MAX_CHARS)


def task_items(achievements: list[dict[str, Any]], unlocked_ids: set[str]) -> list[dict[str, Any]]:
    return [achievement for achievement in achievements if achievement["id"] not in unlocked_ids]


def done_items(achievements: list[dict[str, Any]], unlocked_ids: set[str]) -> list[dict[str, Any]]:
    return [achievement for achievement in achievements if achievement["id"] in unlocked_ids]


def storage_items(achievements: list[dict[str, Any]], unlocked_ids: set[str]) -> list[dict[str, Any]]:
    return [
        achievement
        for achievement in achievements
        if achievement["id"] in unlocked_ids and achievement.get("reward_type") in ASSET_REWARD_TYPES
    ]


def items_for_category(
    items: list[dict[str, Any]],
    category_id: str,
    *,
    key: str,
) -> list[dict[str, Any]]:
    return [item for item in items if item.get(key) == category_id]
