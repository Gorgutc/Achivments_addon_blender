from __future__ import annotations

import importlib.util
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(os.environ["ACHIEVEMENTS_ADDON_ROOT"])
ADDON_PATH = ROOT / "__init__.py"
MODULE_NAME = "achievements_blender_smoke_rewards_addon"


def fail(message: str) -> None:
    print(f"[smoke_rewards:FAIL] {message}")
    raise SystemExit(1)


def load_addon():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, ADDON_PATH)
    if spec is None or spec.loader is None:
        fail("cannot create module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def unlock(module, ach_id: str) -> None:
    module.stats.unlocked.add(ach_id)
    module.stats.unlock_hashes[ach_id] = module._make_unlock_hash(ach_id)


def reward(module, ach_id: str) -> dict:
    return next(item for item in module.ACHIEVEMENTS_DEF if item["id"] == ach_id)


def main() -> None:
    module = load_addon()
    module.register()
    try:
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.object

        material_ach = reward(module, "thousand_vertices")
        unlock(module, material_ach["id"])
        result = bpy.ops.ach.apply_reward(ach_id=material_ach["id"])
        if result != {"FINISHED"}:
            fail(f"material reward returned {result}")
        material_name = material_ach["reward_data"]["name"]
        if material_name not in bpy.data.materials:
            fail("placeholder material was not created")
        if not cube.data.materials or cube.data.materials[0].name != material_name:
            fail("placeholder material was not applied to active mesh")

        mesh_ach = reward(module, "blender_legend")
        unlock(module, mesh_ach["id"])
        result = bpy.ops.ach.apply_reward(ach_id=mesh_ach["id"])
        if result != {"FINISHED"}:
            fail(f"mesh reward returned {result}")
        if mesh_ach["reward_data"]["name"] not in bpy.data.objects:
            fail("placeholder mesh object was not created")

        bpy.context.view_layer.objects.active = cube
        cube.select_set(True)
        geo_ach = reward(module, "architect")
        unlock(module, geo_ach["id"])
        result = bpy.ops.ach.apply_reward(ach_id=geo_ach["id"])
        if result != {"FINISHED"}:
            fail(f"geo reward returned {result}")
        if geo_ach["reward_data"]["name"] not in cube.modifiers:
            fail("placeholder geo nodes modifier was not created")
    finally:
        module.unregister()

    print("[smoke_rewards:PASS] material, mesh, and geo reward fallbacks clean")


if __name__ == "__main__":
    main()
