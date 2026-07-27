"""Pure object, collection, and modifier predicates."""

from __future__ import annotations

from collections import Counter

from .types import Predicate, PredicateContext


def _mesh_objects(context: PredicateContext):
    return (obj for obj in context.scene.objects if obj.type == "MESH")


def _has_mesh(context: PredicateContext) -> bool:
    return any(obj.type == "MESH" for obj in context.scene.objects)


def _has_modifier(context: PredicateContext, modifier_type: str) -> bool:
    return any(
        modifier.type == modifier_type
        for obj in _mesh_objects(context)
        for modifier in obj.modifiers
    )


def _has_subsurf(context: PredicateContext) -> bool:
    return _has_modifier(context, "SUBSURF")


def _five_modifier_stack(context: PredicateContext) -> bool:
    return any(len(obj.modifiers) >= 5 for obj in _mesh_objects(context))


def _has_mirror(context: PredicateContext) -> bool:
    return _has_modifier(context, "MIRROR")


def _has_boolean(context: PredicateContext) -> bool:
    return _has_modifier(context, "BOOLEAN")


def _has_solidify(context: PredicateContext) -> bool:
    return _has_modifier(context, "SOLIDIFY")


def _has_bevel(context: PredicateContext) -> bool:
    return _has_modifier(context, "BEVEL")


def _has_screw(context: PredicateContext) -> bool:
    return _has_modifier(context, "SCREW")


def _has_collection(context: PredicateContext) -> bool:
    return len(context.data.collections) > 0


def _has_three_meshes(context: PredicateContext) -> bool:
    return any(
        len([obj for obj in collection.objects if obj.type == "MESH"]) >= 3
        for collection in context.data.collections
    )


def _has_unique_materials(context: PredicateContext) -> bool:
    for collection in context.data.collections:
        materials = set()
        for obj in collection.objects:
            if obj.type == "MESH" and obj.data.materials and obj.data.materials[0]:
                materials.add(obj.data.materials[0].name)
        if len(materials) >= 3:
            return True
    return False


def _has_array(context: PredicateContext) -> bool:
    return _has_modifier(context, "ARRAY")


def _has_five_collections(context: PredicateContext) -> bool:
    filled = sum(1 for collection in context.data.collections if len(collection.objects) > 0)
    return filled >= 5


def _custom_origin_set(context: PredicateContext) -> bool:
    # Preserve the current indirect approximation: any non-origin mesh location.
    return any(obj.location.length > 0.001 for obj in _mesh_objects(context))


def _has_twenty_linked(context: PredicateContext) -> bool:
    mesh_users = Counter(
        obj.data.name for obj in _mesh_objects(context) if obj.data
    )
    return any(count >= 20 for count in mesh_users.values())


def _ten_modifier_stack(context: PredicateContext) -> bool:
    return any(len(obj.modifiers) >= 10 for obj in _mesh_objects(context))


def _has_shrinkwrap(context: PredicateContext) -> bool:
    return any(
        modifier.type == "SHRINKWRAP" and modifier.target is not None
        for obj in _mesh_objects(context)
        for modifier in obj.modifiers
    )


def _has_armature(context: PredicateContext) -> bool:
    return any(
        modifier.type == "ARMATURE" and modifier.object is not None
        for obj in _mesh_objects(context)
        for modifier in obj.modifiers
    )


def _has_curve_modifier(context: PredicateContext) -> bool:
    return any(
        modifier.type == "CURVE" and modifier.object is not None
        for obj in _mesh_objects(context)
        for modifier in obj.modifiers
    )


def _has_skin(context: PredicateContext) -> bool:
    return _has_modifier(context, "SKIN")


def _has_weighted_normal(context: PredicateContext) -> bool:
    return _has_modifier(context, "WEIGHTED_NORMAL")


def _has_array_with_empty(context: PredicateContext) -> bool:
    return any(
        modifier.type == "ARRAY"
        and modifier.use_object_offset
        and modifier.offset_object is not None
        for obj in _mesh_objects(context)
        for modifier in obj.modifiers
    )


def _has_multires(context: PredicateContext) -> bool:
    return any(
        modifier.type == "MULTIRES" and modifier.levels > 1
        for obj in _mesh_objects(context)
        for modifier in obj.modifiers
    )


def _has_shape_keys(context: PredicateContext) -> bool:
    return any(
        obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) >= 2
        for obj in _mesh_objects(context)
    )


def _has_shape_key_animation(context: PredicateContext) -> bool:
    for obj in _mesh_objects(context):
        if obj.data.shape_keys:
            shape_keys = obj.data.shape_keys
            if shape_keys.animation_data and shape_keys.animation_data.action:
                return True
    return False


def _has_snap_face(context: PredicateContext) -> bool:
    tool_settings = context.scene.tool_settings
    try:
        return tool_settings.use_snap and "FACE" in tool_settings.snap_elements
    except Exception:  # noqa: BLE001 - matches Blender's version-tolerant fallback.
        return False


def _has_particles(context: PredicateContext) -> bool:
    # Preserve current behavior: FORCE_WIND objects are not accepted here.
    return any(len(obj.particle_systems) > 0 for obj in _mesh_objects(context))


def _has_smooth(context: PredicateContext) -> bool:
    for obj in _mesh_objects(context):
        for modifier in obj.modifiers:
            if modifier.type == "SMOOTH":
                return True
            if (
                modifier.type == "NODES"
                and modifier.node_group
                and "smooth" in modifier.node_group.name.lower()
            ):
                return True
    return False


OBJECT_MODIFIER_PREDICATES: dict[tuple[str, str], Predicate] = {
    ("five_modifier_stack", "has_mesh"): _has_mesh,
    ("five_modifier_stack", "five_modifier_stack"): _five_modifier_stack,
    ("mirror_subdivision", "has_mirror"): _has_mirror,
    ("mirror_subdivision", "has_subsurf"): _has_subsurf,
    ("boolean_master", "has_boolean"): _has_boolean,
    ("solidify_bevel_combo", "has_solidify"): _has_solidify,
    ("solidify_bevel_combo", "has_bevel"): _has_bevel,
    ("screw_modifier", "has_screw"): _has_screw,
    ("collection_organizer", "has_5_collections"): _has_five_collections,
    ("custom_origin", "custom_origin_set"): _custom_origin_set,
    ("linked_duplicate", "has_20_linked"): _has_twenty_linked,
    ("array_circle", "has_array_with_empty"): _has_array_with_empty,
    ("ten_modifier_stack", "ten_modifier_stack"): _ten_modifier_stack,
    ("shrinkwrap_use", "has_shrinkwrap"): _has_shrinkwrap,
    ("armature_modifier", "has_armature"): _has_armature,
    ("curve_deform", "has_curve_mod"): _has_curve_modifier,
    ("skin_modifier", "has_skin"): _has_skin,
    ("weighted_normals", "has_weighted_normal"): _has_weighted_normal,
    ("shape_key_animation", "has_shape_keys"): _has_shape_keys,
    ("shape_key_animation", "has_shape_key_anim"): _has_shape_key_animation,
    ("multiresolution_sculpt", "has_multires"): _has_multires,
    ("retopology_work", "has_snap_face"): _has_snap_face,
    ("particle_system", "has_particles"): _has_particles,
    ("smooth_cube", "has_mesh"): _has_mesh,
    ("smooth_cube", "has_subsurf"): _has_subsurf,
    ("sphere_from_cube", "has_mesh"): _has_mesh,
    ("sphere_from_cube", "has_subsurf"): _has_subsurf,
    ("sphere_from_cube", "has_smooth"): _has_smooth,
    ("architect", "has_collection"): _has_collection,
    ("architect", "has_3_meshes"): _has_three_meshes,
    ("architect", "has_unique_mats"): _has_unique_materials,
    ("architect", "has_array"): _has_array,
}
