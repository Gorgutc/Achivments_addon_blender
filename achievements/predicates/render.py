"""Pure render, lighting, compositor, and view-layer predicates."""

from __future__ import annotations

from .types import Predicate, PredicateContext


def _materials(context: PredicateContext):
    return context.data.materials


def _has_mesh(context: PredicateContext) -> bool:
    return any(obj.type == "MESH" for obj in context.scene.objects)


def _has_material_on_mesh(context: PredicateContext) -> bool:
    return any(
        obj.type == "MESH" and obj.data.materials and obj.data.materials[0]
        for obj in context.scene.objects
    )


def _has_light(context: PredicateContext) -> bool:
    return any(obj.type == "LIGHT" for obj in context.scene.objects)


def _render_done(context: PredicateContext) -> bool:
    return context.stats.renders_completed > 0


def _has_ten_lights(context: PredicateContext) -> bool:
    return len([obj for obj in context.scene.objects if obj.type == "LIGHT"]) >= 10


def _has_three_light_types(context: PredicateContext) -> bool:
    light_types = {
        obj.data.type for obj in context.scene.objects if obj.type == "LIGHT"
    }
    return len(light_types) >= 3


def _has_hdri(context: PredicateContext) -> bool:
    world = context.scene.world
    if world and world.use_nodes and world.node_tree:
        return any(
            node.bl_idname == "ShaderNodeTexEnvironment" and node.image is not None
            for node in world.node_tree.nodes
        )
    return False


def _has_depth_of_field(context: PredicateContext) -> bool:
    camera = context.scene.camera
    return bool(
        camera
        and camera.data.dof.use_dof
        and (
            camera.data.dof.focus_object is not None
            or camera.data.dof.focus_distance > 0
        )
    )


def _has_motion_blur(context: PredicateContext) -> bool:
    return context.scene.render.use_motion_blur


def _has_denoiser(context: PredicateContext) -> bool:
    return bool(
        context.event == "render_complete"
        and getattr(getattr(context.scene, "render", None), "engine", None)
        == "CYCLES"
        and getattr(getattr(context.scene, "cycles", None), "use_denoising", False)
    )


def _has_caustics(context: PredicateContext) -> bool:
    if not hasattr(context.scene, "cycles"):
        return False
    cycles = context.scene.cycles
    if not (cycles.caustics_reflective or cycles.caustics_refractive):
        return False
    for material in _materials(context):
        if not (material.use_nodes and material.node_tree):
            continue
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeBsdfGlass":
                return True
            if node.bl_idname == "ShaderNodeBsdfPrincipled":
                for node_input in node.inputs:
                    if (
                        node_input.name in ("Transmission", "Transmission Weight")
                        and node_input.default_value > 0
                    ):
                        return True
    return False


def _has_volume(context: PredicateContext) -> bool:
    volume_nodes = {
        "ShaderNodeVolumeScatter",
        "ShaderNodeVolumeAbsorption",
        "ShaderNodeVolumePrincipled",
    }
    for material in _materials(context):
        if material.use_nodes and material.node_tree and any(
            node.bl_idname in volume_nodes for node in material.node_tree.nodes
        ):
            return True
    world = context.scene.world
    if world and world.use_nodes and world.node_tree:
        return any(node.bl_idname in volume_nodes for node in world.node_tree.nodes)
    return False


def _has_compositor(context: PredicateContext) -> bool:
    node_tree = getattr(context.scene, "node_tree", None)
    if getattr(context.scene, "use_nodes", False) and node_tree:
        real_nodes = [
            node
            for node in node_tree.nodes
            if node.type not in ("R_LAYERS", "COMPOSITE", "VIEWER", "OUTPUT_FILE")
        ]
        return len(real_nodes) > 0
    return False


def _has_five_passes(context: PredicateContext) -> bool:
    view_layer = context.view_layer
    scene_layers = context.scene.view_layers
    if not view_layer or view_layer.name not in scene_layers:
        view_layer = scene_layers[0] if len(scene_layers) else None
    if not view_layer:
        return False
    pass_attributes = (
        "use_pass_diffuse_direct",
        "use_pass_diffuse_indirect",
        "use_pass_diffuse_color",
        "use_pass_glossy_direct",
        "use_pass_glossy_indirect",
        "use_pass_glossy_color",
        "use_pass_transmission_direct",
        "use_pass_transmission_indirect",
        "use_pass_transmission_color",
        "use_pass_emit",
        "use_pass_environment",
        "use_pass_shadow",
        "use_pass_ambient_occlusion",
        "use_pass_normal",
        "use_pass_vector",
        "use_pass_uv",
        "use_pass_mist",
        "use_pass_object_index",
        "use_pass_material_index",
        "use_pass_z",
    )
    return sum(
        1
        for attribute in pass_attributes
        if hasattr(view_layer, attribute) and getattr(view_layer, attribute)
    ) >= 5


RENDER_PREDICATES: dict[tuple[str, str], Predicate] = {
    ("first_render", "has_mesh"): _has_mesh,
    ("first_render", "has_material_on_mesh"): _has_material_on_mesh,
    ("first_render", "has_light"): _has_light,
    ("first_render", "render_done"): _render_done,
    ("ten_lights_scene", "has_10_lights"): _has_ten_lights,
    ("three_light_setup", "has_3_light_types"): _has_three_light_types,
    ("hdri_lighting", "has_hdri"): _has_hdri,
    ("depth_of_field", "has_dof"): _has_depth_of_field,
    ("motion_blur_render", "has_motion_blur"): _has_motion_blur,
    ("denoiser_render", "has_denoiser"): _has_denoiser,
    ("cycles_caustics", "has_caustics"): _has_caustics,
    ("volumetric_render", "has_volume"): _has_volume,
    ("compositing_node_render", "has_compositor"): _has_compositor,
    ("render_passes", "has_5_passes"): _has_five_passes,
}
