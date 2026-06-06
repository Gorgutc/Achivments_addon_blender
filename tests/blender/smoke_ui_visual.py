from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(os.environ["ACHIEVEMENTS_ADDON_ROOT"])
ADDON_PATH = ROOT / "__init__.py"
MODULE_NAME = "achievements_blender_smoke_ui_visual_addon"
VIEWPORT_SIZE = (1280, 720)


def fail(message: str) -> None:
    print(f"[smoke_ui_visual:FAIL] {message}")
    raise SystemExit(1)


def load_addon():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, ADDON_PATH)
    if spec is None or spec.loader is None:
        fail("cannot create module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def assert_inside_viewport(frame, label: str) -> None:
    width, height = VIEWPORT_SIZE
    if frame.x < 0 or frame.y < 0:
        fail(f"{label} starts outside viewport: {(frame.x, frame.y)}")
    if frame.x + frame.width > width or frame.y + frame.height > height:
        fail(f"{label} exceeds viewport: {(frame.x, frame.y, frame.width, frame.height)}")


def draw_rect(pixels: list[float], width: int, height: int, rect, color) -> None:
    x, y, w, h = rect
    x0 = max(0, int(x))
    y0 = max(0, int(y))
    x1 = min(width, int(x + w))
    y1 = min(height, int(y + h))
    for yy in range(y0, y1):
        for xx in range(x0, x1):
            offset = (yy * width + xx) * 4
            pixels[offset : offset + 4] = color


def save_visual_contract(module, path: Path) -> None:
    width = module.ach_ui.popup_dialog_width()
    height = 620
    bg = [0.06, 0.07, 0.09, 1.0]
    pixels = bg * width * height

    # Header button strip.
    draw_rect(pixels, width, height, (20, 580, 220, 28), [0.18, 0.20, 0.24, 1.0])
    draw_rect(pixels, width, height, (28, 586, 16, 16), [0.35, 0.70, 0.95, 1.0])

    # Popup body, tabs, and representative two-column card grid.
    draw_rect(pixels, width, height, (20, 320, width - 40, 240), [0.10, 0.11, 0.14, 1.0])
    tab_width = (width - 64) // len(module.ach_ui.TABS)
    for index, _tab in enumerate(module.ach_ui.TABS):
        draw_rect(
            pixels,
            width,
            height,
            (32 + index * tab_width, 530, tab_width - 8, 24),
            [0.20, 0.23, 0.28, 1.0],
        )
    for col in range(module.GRID_COLS):
        for row in range(2):
            x = 32 + col * 332
            y = 370 + row * 62
            draw_rect(pixels, width, height, (x, y, 312, 50), [0.16, 0.17, 0.20, 1.0])
            draw_rect(pixels, width, height, (x + 8, y + 8, 34, 34), [0.30, 0.32, 0.36, 1.0])
            draw_rect(pixels, width, height, (x + 52, y + 32, 190, 6), [0.76, 0.78, 0.82, 1.0])
            draw_rect(pixels, width, height, (x + 52, y + 18, 250, 5), [0.45, 0.48, 0.54, 1.0])

    # Notification and pinned overlay contract frames.
    notification = module.ach_ui.notification_frame(index=0, elapsed=module.ach_ui.NOTIFY_SLIDE_IN)
    pinned = module.ach_ui.pinned_frame(notification_count=1)
    draw_rect(
        pixels,
        width,
        height,
        (notification.x, notification.y, notification.width, notification.height),
        [0.10, 0.12, 0.16, 1.0],
    )
    draw_rect(pixels, width, height, (notification.x, notification.y, 4, notification.height), [0.3, 0.8, 0.45, 1.0])
    draw_rect(
        pixels,
        width,
        height,
        (pinned.x, pinned.y, pinned.width, pinned.height),
        [0.12, 0.14, 0.18, 1.0],
    )
    draw_rect(pixels, width, height, (pinned.x, pinned.y, 4, pinned.height), [0.9, 0.75, 0.2, 1.0])

    image = bpy.data.images.new("achievements_ui_visual_contract", width=width, height=height, alpha=True)
    image.pixels.foreach_set(pixels)
    path.parent.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(path)
    image.file_format = "PNG"
    image.save()
    if not path.is_file() or path.stat().st_size == 0:
        fail(f"visual artifact was not saved: {path}")


def main() -> None:
    module = load_addon()
    if not hasattr(module, "ach_ui"):
        fail("root runtime did not import achievements.ui")
    data_dir = Path(module.DATA_DIR)
    expected_home = Path(os.environ["USERPROFILE"])
    if expected_home not in data_dir.parents and data_dir != expected_home:
        fail(f"DATA_DIR is outside temp home: {data_dir}")
    if data_dir.exists():
        fail("root import created DATA_DIR before register")

    module.register()
    try:
        if module._tab_prop("TASKS") != "ach_page_tasks":
            fail("TASKS tab page property drifted")
        if module._tab_prop("STORAGE_GEO_NODES") != "ach_page_storage_geo_nodes":
            fail("category tab page property drifted")

        scene = bpy.context.scene
        for tab in module.ach_ui.TABS:
            scene.ach_tab = tab.key
            if scene.ach_tab != tab.key:
                fail(f"Scene ach_tab rejected {tab.key}")

        first = module.ach_ui.notification_frame(index=0, elapsed=module.ach_ui.NOTIFY_SLIDE_IN)
        second = module.ach_ui.notification_frame(index=1, elapsed=module.ach_ui.NOTIFY_SLIDE_IN)
        pinned = module.ach_ui.pinned_frame(notification_count=2)
        assert_inside_viewport(first, "first notification")
        assert_inside_viewport(second, "second notification")
        assert_inside_viewport(pinned, "pinned overlay")
        if second.y < first.y + first.height:
            fail("notification stack overlaps")
        if pinned.y < second.y + second.height:
            fail("pinned overlay overlaps notifications")

        artifact_dir = Path(os.environ["ACHIEVEMENTS_VISUAL_QA_DIR"])
        artifact = artifact_dir / "ui_visual_contract.png"
        save_visual_contract(module, artifact)
    finally:
        module.unregister()

    print(f"[smoke_ui_visual:PASS] visual contract artifact saved: {artifact}")


if __name__ == "__main__":
    main()
