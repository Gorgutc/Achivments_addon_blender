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


def assert_step(
    module,
    scene,
    complex_id: str,
    step_check: str,
    expected: bool,
    *,
    event: str | None = None,
) -> None:
    actual = module._check_complex_step(
        complex_id,
        step_check,
        scene,
        event=event,
    )
    if actual is not expected:
        fail(
            f"{complex_id}/{step_check}: expected {expected}, got {actual}"
        )


def clear_scene_objects() -> None:
    for obj in list(bpy.data.objects):
        bpy.data.objects.remove(obj, do_unlink=True)


def exercise_factory_default_unlocks(module, scene) -> None:
    target_ids = {"subsurface_skin", "denoiser_render"}
    original_catalog = module.ACHIEVEMENTS_DEF
    original_unlocked = set(module.stats.unlocked)
    original_hashes = dict(module.stats.unlock_hashes)
    try:
        module.ACHIEVEMENTS_DEF = [
            achievement
            for achievement in original_catalog
            if achievement["id"] in target_ids
        ]
        module.stats.unlocked.difference_update(target_ids)
        for achievement_id in target_ids:
            module.stats.unlock_hashes.pop(achievement_id, None)
        module.check_complex_achievements(scene)
        unexpected = target_ids & module.stats.unlocked
        if unexpected:
            fail(f"factory defaults unlocked achievements: {sorted(unexpected)}")
    finally:
        module.ACHIEVEMENTS_DEF = original_catalog
        module.stats.unlocked.clear()
        module.stats.unlocked.update(original_unlocked)
        module.stats.unlock_hashes.clear()
        module.stats.unlock_hashes.update(original_hashes)


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

    original_engine = scene.render.engine
    original_denoising = scene.cycles.use_denoising
    try:
        scene.render.engine = "BLENDER_EEVEE"
        scene.cycles.use_denoising = True
        assert_step(module, scene, "denoiser_render", "has_denoiser", False)
        assert_step(
            module,
            scene,
            "denoiser_render",
            "has_denoiser",
            False,
            event="render_complete",
        )

        scene.render.engine = "CYCLES"
        assert_step(module, scene, "denoiser_render", "has_denoiser", False)
        scene.cycles.use_denoising = False
        assert_step(
            module,
            scene,
            "denoiser_render",
            "has_denoiser",
            False,
            event="render_complete",
        )
        scene.cycles.use_denoising = True
        assert_step(
            module,
            scene,
            "denoiser_render",
            "has_denoiser",
            True,
            event="render_complete",
        )
    finally:
        scene.render.engine = original_engine
        scene.cycles.use_denoising = original_denoising


def exercise_material_predicates(module, scene) -> None:
    for material in list(bpy.data.materials):
        bpy.data.materials.remove(material)
    assert_step(module, scene, "normal_map_material", "has_normal_map", False)
    material = bpy.data.materials.new("ACH_SmokeMaterial")
    material.use_nodes = True
    principled = material.node_tree.nodes.get("Principled BSDF")
    if principled is None:
        fail("default Principled BSDF node is missing")
    assert_step(module, scene, "subsurface_skin", "has_subsurface", False)
    principled.inputs["Subsurface Weight"].default_value = 0.25
    assert_step(module, scene, "subsurface_skin", "has_subsurface", True)
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


def exercise_denoiser_handler(module, context_scene) -> None:
    denoiser = next(
        achievement
        for achievement in module.ACHIEVEMENTS_DEF
        if achievement["id"] == "denoiser_render"
    )
    original_catalog = module.ACHIEVEMENTS_DEF
    original_unlocked = set(module.stats.unlocked)
    original_hashes = dict(module.stats.unlock_hashes)
    original_renders = module.stats.renders_completed
    rendered_scene = bpy.data.scenes.new("ACH_SmokeRenderedScene")
    try:
        context_scene.render.engine = "BLENDER_EEVEE"
        context_scene.cycles.use_denoising = True
        rendered_scene.render.engine = "CYCLES"
        rendered_scene.cycles.use_denoising = True
        module.ACHIEVEMENTS_DEF = [denoiser]
        module.stats.unlocked.discard("denoiser_render")
        module.stats.unlock_hashes.pop("denoiser_render", None)

        module.check_complex_achievements(rendered_scene)
        if "denoiser_render" in module.stats.unlocked:
            fail("generic complex check unlocked denoiser without a render event")

        module.on_render_complete(rendered_scene)
        if "denoiser_render" not in module.stats.unlocked:
            fail("render handler did not use the supplied rendered Cycles scene")
    finally:
        module.ACHIEVEMENTS_DEF = original_catalog
        module.stats.unlocked.clear()
        module.stats.unlocked.update(original_unlocked)
        module.stats.unlock_hashes.clear()
        module.stats.unlock_hashes.update(original_hashes)
        module.stats.renders_completed = original_renders
        bpy.data.scenes.remove(rendered_scene)


def main() -> None:
    module = load_addon()
    module.register()
    try:
        scene = bpy.context.scene
        assert_step(module, scene, "subsurface_skin", "has_subsurface", False)
        assert_step(module, scene, "denoiser_render", "has_denoiser", False)
        exercise_factory_default_unlocks(module, scene)
        clear_scene_objects()
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            exercise_object_modifier_predicates(module, scene)
            exercise_render_predicates(module, scene)
            exercise_material_predicates(module, scene)
            exercise_geometry_nodes_predicates(module, scene)
            exercise_time_state_predicates(module, scene)
            exercise_denoiser_handler(module, scene)
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
