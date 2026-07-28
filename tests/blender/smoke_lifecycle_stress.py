from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(os.environ["ACHIEVEMENTS_ADDON_ROOT"])
ADDON_PATH = ROOT / "__init__.py"
MODULE_NAME = "achievements_blender_smoke_lifecycle_addon"
BASE_SCENE_PROPS = [
    "ach_tab",
    "ach_page_tasks",
    "ach_page_done",
    "ach_page_lessons",
    "ach_page_storage",
]


class FakeClock:
    def __init__(self, now: float) -> None:
        self.now = now

    def __call__(self) -> float:
        return self.now


def fail(message: str) -> None:
    print(f"[smoke_lifecycle_stress:FAIL] {message}")
    raise SystemExit(1)


def load_addon():
    spec = importlib.util.spec_from_file_location(
        MODULE_NAME,
        ADDON_PATH,
        submodule_search_locations=[str(ROOT)],
    )
    if spec is None or spec.loader is None:
        fail("cannot create module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def scene_props(module):
    props = list(BASE_SCENE_PROPS)
    for cat_id, _label in module.ACH_CATEGORIES:
        props.extend(
            [
                f"ach_acc_tasks_{cat_id}",
                f"ach_acc_done_{cat_id}",
                f"ach_acc_lessons_{cat_id}",
                f"ach_page_tasks_{cat_id.lower()}",
                f"ach_page_done_{cat_id.lower()}",
                f"ach_page_lessons_{cat_id.lower()}",
            ]
        )
    for cat_id, _label in module.REWARD_CATEGORIES:
        props.extend([f"ach_acc_storage_{cat_id}", f"ach_page_storage_{cat_id.lower()}"])
    return props


def handler_pairs(module):
    return [
        (module.on_depsgraph_update, bpy.app.handlers.depsgraph_update_post, "depsgraph"),
        (module.on_load_post, bpy.app.handlers.load_post, "load_post"),
        (module.on_save_pre, bpy.app.handlers.save_pre, "save_pre"),
        (module.on_render_complete, bpy.app.handlers.render_complete, "render_complete"),
    ]


def header_callbacks():
    callbacks = getattr(bpy.types.VIEW3D_HT_header, "_dyn_ui_initialize", [])
    if not isinstance(callbacks, (list, tuple)):
        return []
    return list(callbacks)


def assert_registered_once(module):
    missing_props = [prop for prop in scene_props(module) if not hasattr(bpy.types.Scene, prop)]
    if missing_props:
        fail(f"missing Scene props after register: {missing_props[:5]}")
    for callback, collection, name in handler_pairs(module):
        count = collection.count(callback)
        if count != 1:
            fail(f"{name} handler count is {count}, expected 1")
    header_count = header_callbacks().count(module._draw_header_button)
    if header_count > 1:
        fail(f"header callback duplicated: {header_count}")
    if not module._header_button_registered:
        fail("header registration flag missing after register")
    if not module._addon_registered:
        fail("addon registration flag missing after register")
    if not bpy.app.timers.is_registered(module._timer_tick):
        fail("timer tick missing after register")
    if not bpy.app.timers.is_registered(module._notification_redraw_tick):
        fail("notification redraw timer missing after register")
    if module._draw_handler is None:
        fail("notification draw handler missing after register")
    if module._draw_handler_pin is None:
        fail("pinned draw handler missing after register")


def assert_draw_handlers_unchanged(module, handles):
    draw_handler, draw_handler_pin = handles
    if module._draw_handler != draw_handler:
        fail("notification draw handler changed after repeated register")
    if module._draw_handler_pin != draw_handler_pin:
        fail("pinned draw handler changed after repeated register")


def assert_unregistered(module):
    remaining_props = [prop for prop in scene_props(module) if hasattr(bpy.types.Scene, prop)]
    if remaining_props:
        fail(f"remaining Scene props after unregister: {remaining_props[:5]}")
    for callback, collection, name in handler_pairs(module):
        if callback in collection:
            fail(f"{name} handler still registered after unregister")
    if module._draw_header_button in header_callbacks():
        fail("header callback still registered after unregister")
    if module._header_button_registered:
        fail("header registration flag still set after unregister")
    if module._addon_registered:
        fail("addon registration flag still set after unregister")
    if bpy.app.timers.is_registered(module._timer_tick):
        fail("timer tick still registered after unregister")
    if bpy.app.timers.is_registered(module._notification_redraw_tick):
        fail("notification redraw timer still registered after unregister")
    if module._draw_handler is not None or module._draw_handler_pin is not None:
        fail("draw handlers not cleared after unregister")


def call(label: str, func) -> None:
    try:
        func()
    except Exception as exc:
        fail(f"{label} raised {type(exc).__name__}: {exc}")


def assert_active_time_window(module, clock: FakeClock) -> None:
    if module.stats.time_spent != 0:
        fail(f"unexpected initial active time: {module.stats.time_spent}")

    clock.now = 160.0
    call("idle timer", module._timer_tick)
    if module.stats.time_spent != 0:
        fail(f"timer opened an activity window: {module.stats.time_spent}")

    clock.now = 200.0
    call("first real activity", module._on_user_activity)
    if module.stats.time_spent != 0:
        fail(f"first activity credited startup time: {module.stats.time_spent}")

    clock.now = 260.0
    call("first active timer", module._timer_tick)
    if module.stats.time_spent != 60:
        fail(f"first timer did not credit exactly once: {module.stats.time_spent}")
    call("same-time active timer", module._timer_tick)
    if module.stats.time_spent != 60:
        fail(f"same-time double flush was not idempotent: {module.stats.time_spent}")

    clock.now = 320.0
    call("activity cap timer", module._timer_tick)
    if module.stats.time_spent != 120:
        fail(f"activity window did not reach 120-second cap: {module.stats.time_spent}")
    clock.now = 380.0
    call("post-cap idle timer", module._timer_tick)
    if module.stats.time_spent != 120:
        fail(f"timer refreshed the capped activity window: {module.stats.time_spent}")

    clock.now = 90.0
    call("rollback timer", module._timer_tick)
    clock.now = 10_000.0
    call("post-rollback idle timer", module._timer_tick)
    if module.stats.time_spent != 120:
        fail(f"rollback or suspend changed active time: {module.stats.time_spent}")

    clock.now = 10_010.0
    call("post-rollback activity", module._on_user_activity)
    clock.now = 10_070.0
    call("post-rollback active timer", module._timer_tick)
    if module.stats.time_spent != 180:
        fail(f"new activity did not reopen a clean window: {module.stats.time_spent}")


def main() -> None:
    module = load_addon()
    clock = FakeClock(100.0)
    module._activity_clock = clock
    data_dir = Path(module.DATA_DIR)
    expected_home = Path(os.environ["USERPROFILE"])
    if expected_home not in data_dir.parents and data_dir != expected_home:
        fail(f"DATA_DIR is outside temp home: {data_dir}")
    if data_dir.exists():
        fail("root import created DATA_DIR before register")
    data_file = Path(module.DATA_FILE)

    call("initial unregister", module.unregister)
    assert_unregistered(module)
    if data_file.exists():
        fail("initial unregister wrote achievements_data.json")

    call("first register", module.register)
    assert_registered_once(module)
    draw_handles = (module._draw_handler, module._draw_handler_pin)
    assert_active_time_window(module, clock)

    call("second register", module.register)
    assert_registered_once(module)
    assert_draw_handlers_unchanged(module, draw_handles)

    clock.now = 20_000.0
    call("reloaded idle timer", module._timer_tick)
    if module.stats.time_spent != 180:
        fail(f"reload credited offline idle: {module.stats.time_spent}")
    clock.now = 20_010.0
    call("pre-unregister activity", module._on_user_activity)
    clock.now = 20_070.0

    call("first unregister", module.unregister)
    assert_unregistered(module)
    if module.stats.time_spent != 240:
        fail(f"unregister did not credit the tail exactly once: {module.stats.time_spent}")

    call("second unregister", module.unregister)
    assert_unregistered(module)
    if module.stats.time_spent != 240:
        fail(f"second unregister changed active time: {module.stats.time_spent}")

    print("[smoke_lifecycle_stress:PASS] repeated register/unregister lifecycle clean")


if __name__ == "__main__":
    main()
