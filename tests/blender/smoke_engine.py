from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(os.environ["ACHIEVEMENTS_ADDON_ROOT"])
ADDON_PATH = ROOT / "__init__.py"
MODULE_NAME = "achievements_blender_smoke_engine_addon"
ERROR_MARKER = "[Achievements] complex step check error"


def fail(message: str) -> None:
    print(f"[smoke_engine:FAIL] {message}")
    raise SystemExit(1)


def load_addon():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, ADDON_PATH)
    if spec is None or spec.loader is None:
        fail("cannot create module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def assert_step(module, scene, complex_id: str, step_check: str, expected: bool) -> None:
    actual = module._check_complex_step(complex_id, step_check, scene)
    if actual is not expected:
        fail(
            f"{complex_id}/{step_check}: expected {expected}, got {actual}"
        )


def clear_scene_objects() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def exercise_object_modifier_predicates(module, scene) -> None:
    assert_step(module, scene, "smooth_cube", "has_mesh", False)
    mesh = bpy.data.meshes.new("ACH_SmokeMesh")
    obj = bpy.data.objects.new("ACH_SmokeObject", mesh)
    scene.collection.objects.link(obj)
    assert_step(module, scene, "smooth_cube", "has_mesh", True)
    assert_step(module, scene, "smooth_cube", "has_subsurf", False)
    obj.modifiers.new(name="ACH_SmokeSubdivision", type="SUBSURF")
    assert_step(module, scene, "smooth_cube", "has_subsurf", True)


def exercise_render_predicates(module, scene) -> None:
    assert_step(module, scene, "first_render", "has_light", False)
    light_data = bpy.data.lights.new("ACH_SmokeLightData", type="POINT")
    light = bpy.data.objects.new("ACH_SmokeLight", light_data)
    scene.collection.objects.link(light)
    assert_step(module, scene, "first_render", "has_light", True)


def exercise_material_predicates(module, scene) -> None:
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    assert_step(module, scene, "normal_map_material", "has_normal_map", False)
    material = bpy.data.materials.new("ACH_SmokeMaterial")
    material.use_nodes = True
    material.node_tree.nodes.new("ShaderNodeNormalMap")
    assert_step(module, scene, "normal_map_material", "has_normal_map", True)


def exercise_geometry_nodes_predicates(module, scene) -> None:
    mesh_object = next(obj for obj in scene.objects if obj.type == "MESH")
    assert_step(module, scene, "first_geonode", "has_geonodes_mod", False)
    modifier = mesh_object.modifiers.new(name="ACH_SmokeGeometryNodes", type="NODES")
    modifier.node_group = bpy.data.node_groups.new(
        "ACH_SmokeGeometryTree",
        type="GeometryNodeTree",
    )
    assert_step(module, scene, "first_geonode", "has_geonodes_mod", True)


def exercise_time_state_predicates(module, scene) -> None:
    original_unlocked = set(module.stats.unlocked)
    try:
        module.stats.unlocked.clear()
        assert_step(module, scene, "blender_legend", "has_50_unlocked", False)
        module.stats.unlocked.update(f"smoke-{index}" for index in range(50))
        assert_step(module, scene, "blender_legend", "has_50_unlocked", True)
    finally:
        module.stats.unlocked.clear()
        module.stats.unlocked.update(original_unlocked)


def main() -> None:
    module = load_addon()
    module.register()
    try:
        scene = bpy.context.scene
        clear_scene_objects()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exercise_object_modifier_predicates(module, scene)
            exercise_render_predicates(module, scene)
            exercise_material_predicates(module, scene)
            exercise_geometry_nodes_predicates(module, scene)
            exercise_time_state_predicates(module, scene)
            module._check_complex_step(
                "compositing_node_render",
                "has_compositor",
                scene,
            )
            module._check_complex_step(
                "render_passes",
                "has_5_passes",
                scene,
            )
            module.check_complex_achievements(scene)
        output = buffer.getvalue()
        if ERROR_MARKER in output:
            fail(f"complex step checks emitted error marker: {output.strip()}")
    finally:
        module.unregister()

    print(
        "[smoke_engine:PASS] five predicate categories have real true/false fixtures "
        "and complex rule evaluation emits no error markers"
    )


if __name__ == "__main__":
    main()
