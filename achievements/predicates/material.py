"""Pure material, texture, and shader-node predicates."""

from __future__ import annotations

from .types import Predicate, PredicateContext

PROCEDURAL_NODE_TYPES = {
    "ShaderNodeTexNoise",
    "ShaderNodeTexVoronoi",
    "ShaderNodeTexWave",
    "ShaderNodeTexMusgrave",
    "ShaderNodeTexChecker",
    "ShaderNodeTexBrick",
    "ShaderNodeTexGradient",
    "ShaderNodeTexMagic",
}


def _node_materials(context: PredicateContext):
    return (
        material
        for material in context.data.materials
        if material.use_nodes and material.node_tree
    )


def _has_node(context: PredicateContext, bl_idname: str) -> bool:
    return any(
        node.bl_idname == bl_idname
        for material in _node_materials(context)
        for node in material.node_tree.nodes
    )


def _has_texture_paint(context: PredicateContext) -> bool:
    return any(image.is_dirty for image in context.data.images)


def _has_uv(context: PredicateContext) -> bool:
    return any(
        obj.type == "MESH" and obj.data.uv_layers for obj in context.scene.objects
    )


def _has_image_texture(context: PredicateContext) -> bool:
    return _has_node(context, "ShaderNodeTexImage")


def _has_emission(context: PredicateContext) -> bool:
    return _has_node(context, "ShaderNodeEmission")


def _has_glass_ior(context: PredicateContext) -> bool:
    for material in _node_materials(context):
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeBsdfGlass":
                ior_input = node.inputs.get("IOR")
                if ior_input and 1.40 <= ior_input.default_value <= 1.60:
                    return True
    return False


def _has_mix_shader(context: PredicateContext) -> bool:
    return _has_node(context, "ShaderNodeMixShader")


def _principled_input_is_linked(context: PredicateContext, input_name: str) -> bool:
    for material in _node_materials(context):
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeBsdfPrincipled":
                node_input = node.inputs.get(input_name)
                if node_input and node_input.is_linked:
                    return True
    return False


def _has_base_color(context: PredicateContext) -> bool:
    return _principled_input_is_linked(context, "Base Color")


def _has_normal_input(context: PredicateContext) -> bool:
    return _principled_input_is_linked(context, "Normal")


def _has_normal_map(context: PredicateContext) -> bool:
    return _has_node(context, "ShaderNodeNormalMap")


def _has_subsurface(context: PredicateContext) -> bool:
    for material in _node_materials(context):
        for node in material.node_tree.nodes:
            if node.bl_idname != "ShaderNodeBsdfPrincipled":
                continue
            for node_input in node.inputs:
                name = node_input.name.lower()
                if (
                    "subsurface" in name
                    and "color" not in name
                    and "radius" not in name
                    and (node_input.default_value > 0.0 or node_input.is_linked)
                ):
                    return True
    return False


def _has_procedural(context: PredicateContext) -> bool:
    return any(
        node.bl_idname in PROCEDURAL_NODE_TYPES
        for material in _node_materials(context)
        for node in material.node_tree.nodes
    )


def _has_procedural_without_image(context: PredicateContext) -> bool:
    for material in _node_materials(context):
        nodes = material.node_tree.nodes
        has_procedural = any(node.bl_idname in PROCEDURAL_NODE_TYPES for node in nodes)
        has_image = any(node.bl_idname == "ShaderNodeTexImage" for node in nodes)
        if has_procedural and not has_image:
            return True
    return False


def _has_vertex_color(context: PredicateContext) -> bool:
    return _has_node(context, "ShaderNodeVertexColor") or _has_node(
        context, "ShaderNodeAttribute"
    )


def _has_displacement(context: PredicateContext) -> bool:
    for material in _node_materials(context):
        for node in material.node_tree.nodes:
            if node.bl_idname == "ShaderNodeOutputMaterial":
                displacement = node.inputs.get("Displacement")
                if displacement and displacement.is_linked:
                    return True
    return False


MATERIAL_PREDICATES: dict[tuple[str, str], Predicate] = {
    ("texture_paint", "has_texture_paint"): _has_texture_paint,
    ("uv_unwrap_material", "has_uv"): _has_uv,
    ("uv_unwrap_material", "has_image_texture"): _has_image_texture,
    ("emission_material", "has_emission"): _has_emission,
    ("glass_ior", "has_glass_ior"): _has_glass_ior,
    ("mix_shader", "has_mix_shader"): _has_mix_shader,
    ("principled_bsdf_full", "has_base_color"): _has_base_color,
    ("principled_bsdf_full", "has_normal_input"): _has_normal_input,
    ("normal_map_material", "has_normal_map"): _has_normal_map,
    ("subsurface_skin", "has_subsurface"): _has_subsurface,
    ("procedural_texture", "has_procedural"): _has_procedural,
    ("procedural_texture", "no_image_texture"): _has_procedural_without_image,
    ("vertex_color_material", "has_vertex_color"): _has_vertex_color,
    ("displacement_material", "has_displacement"): _has_displacement,
}
