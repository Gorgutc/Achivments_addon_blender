from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(os.environ["ACHIEVEMENTS_ADDON_ROOT"])
ADDON_PATH = ROOT / "__init__.py"
MODULE_NAME = "achievements_blender_smoke_addon"
BASE_SCENE_PROPS = [
    "ach_tab",
    "ach_page_tasks",
    "ach_page_done",
    "ach_page_lessons",
    "ach_page_storage",
]


def fail(message: str) -> None:
    print(f"[smoke_register:FAIL] {message}")
    raise SystemExit(1)


def load_addon():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, ADDON_PATH)
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


def main() -> None:
    module = load_addon()
    data_dir = Path(module.DATA_DIR)
    expected_home = Path(os.environ["USERPROFILE"])
    if expected_home not in data_dir.parents and data_dir != expected_home:
        fail(f"DATA_DIR is outside temp home: {data_dir}")
    if data_dir.exists():
        fail("root import created DATA_DIR before register")

    module.register()
    preferences_operator = bpy.ops.screen.userpref_show.get_rna_type()
    if "section" not in preferences_operator.properties:
        fail("screen.userpref_show does not expose the section property")
    section_items = {
        item.identifier
        for item in preferences_operator.properties["section"].enum_items
    }
    if "EXTENSIONS" not in section_items:
        fail("screen.userpref_show section does not include EXTENSIONS")
    required_extension_properties = {
        "extension_type",
        "extension_show_panel_installed",
        "extension_show_panel_available",
        "extension_search",
        "extension_tags",
    }
    missing_extension_properties = sorted(
        name
        for name in required_extension_properties
        if not hasattr(bpy.context.window_manager, name)
    )
    if missing_extension_properties:
        fail(
            "extension management properties missing: "
            f"{missing_extension_properties}"
        )
    missing_props = [prop for prop in scene_props(module) if not hasattr(bpy.types.Scene, prop)]
    if missing_props:
        fail(f"register did not create Scene props: {missing_props[:5]}")
    for callback, collection, name in handler_pairs(module):
        if callback not in collection:
            fail(f"{name} handler missing after register")
    if not bpy.app.timers.is_registered(module._timer_tick):
        fail("timer tick missing after register")
    if not bpy.app.timers.is_registered(module._notification_redraw_tick):
        fail("notification redraw timer missing after register")
    callbacks = header_callbacks()
    if callbacks and module._draw_header_button not in callbacks:
        fail("header callback missing after register")
    if not module._header_button_registered:
        fail("header registration flag missing after register")
    if not module._addon_registered:
        fail("addon registration flag missing after register")

    module.unregister()
    remaining_props = [prop for prop in scene_props(module) if hasattr(bpy.types.Scene, prop)]
    if remaining_props:
        fail(f"unregister did not remove Scene props: {remaining_props[:5]}")
    for callback, collection, name in handler_pairs(module):
        if callback in collection:
            fail(f"{name} handler still registered after unregister")
    if bpy.app.timers.is_registered(module._timer_tick):
        fail("timer tick still registered after unregister")
    if bpy.app.timers.is_registered(module._notification_redraw_tick):
        fail("notification redraw timer still registered after unregister")
    if module._draw_header_button in header_callbacks():
        fail("header callback still registered after unregister")
    if module._header_button_registered:
        fail("header registration flag still set after unregister")
    if module._addon_registered:
        fail("addon registration flag still set after unregister")
    if module._draw_handler is not None or module._draw_handler_pin is not None:
        fail("draw handlers not cleared after unregister")

    print("[smoke_register:PASS] register/unregister lifecycle clean")


if __name__ == "__main__":
    main()
