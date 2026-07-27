"""Pure Geometry Nodes predicates."""

from __future__ import annotations

from .types import Predicate, PredicateContext


def _geometry_node_trees(context: PredicateContext):
    for obj in context.scene.objects:
        if obj.type != "MESH":
            continue
        for modifier in obj.modifiers:
            if modifier.type == "NODES" and modifier.node_group:
                yield modifier.node_group


def _has_node(context: PredicateContext, bl_idname: str) -> bool:
    return any(
        node.bl_idname == bl_idname
        for node_tree in _geometry_node_trees(context)
        for node in node_tree.nodes
    )


def _has_node_label_or_name(context: PredicateContext, partial_name: str) -> bool:
    partial = partial_name.lower()
    return any(
        partial in node.name.lower()
        or partial in node.label.lower()
        or partial in node.bl_idname.lower()
        for node_tree in _geometry_node_trees(context)
        for node in node_tree.nodes
    )


def _has_mesh_with_material(context: PredicateContext) -> bool:
    return any(
        obj.type == "MESH" and obj.data.materials and obj.data.materials[0]
        for obj in context.scene.objects
    )


def _has_geometry_nodes_modifier(context: PredicateContext) -> bool:
    return any(True for _node_tree in _geometry_node_trees(context))


def _has_three_nodes(context: PredicateContext) -> bool:
    for node_tree in _geometry_node_trees(context):
        real_nodes = [
            node
            for node in node_tree.nodes
            if node.type not in ("GROUP_INPUT", "GROUP_OUTPUT", "FRAME", "REROUTE")
        ]
        if len(real_nodes) >= 3:
            return True
    return False


def _has_links(context: PredicateContext) -> bool:
    return any(len(node_tree.links) > 0 for node_tree in _geometry_node_trees(context))


def _has_instance(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeInstanceOnPoints")


def _has_scatter(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeDistributePointsOnFaces")


def _has_attribute(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeStoreNamedAttribute") or _has_node(
        context, "GeometryNodeInputNamedAttribute"
    )


def _has_curve_to_mesh(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeCurveToMesh")


def _has_noise(context: PredicateContext) -> bool:
    return _has_node(context, "ShaderNodeTexNoise")


def _has_set_position(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeSetPosition")


def _has_group_input(context: PredicateContext) -> bool:
    for node_tree in _geometry_node_trees(context):
        for node in node_tree.nodes:
            if node.type == "GROUP_INPUT" and len(node.outputs) > 2:
                return True
    return False


def _has_convex_hull(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeConvexHull")


def _has_boolean(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeMeshBoolean")


def _has_realize_instances(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeRealizeInstances")


def _has_field_math(context: PredicateContext) -> bool:
    return (
        _has_node(context, "GeometryNodeFieldAtIndex")
        or _has_node(context, "GeometryNodeSampleIndex")
        or _has_node_label_or_name(context, "evaluate")
    )


def _has_domain_switch(context: PredicateContext) -> bool:
    return (
        _has_node(context, "GeometryNodeSampleIndex")
        or _has_node_label_or_name(context, "transfer attribute")
        or _has_node_label_or_name(context, "interpolate domain")
    )


def _has_simulation(context: PredicateContext) -> bool:
    return _has_node(context, "GeometryNodeSimulationInput") or _has_node(
        context, "GeometryNodeSimulationOutput"
    )


GEOMETRY_NODE_PREDICATES: dict[tuple[str, str], Predicate] = {
    ("procedural_master", "has_mesh_with_mat"): _has_mesh_with_material,
    ("procedural_master", "has_geonodes_mod"): _has_geometry_nodes_modifier,
    ("procedural_master", "has_3_nodes"): _has_three_nodes,
    ("procedural_master", "has_links"): _has_links,
    ("first_geonode", "has_geonodes_mod"): _has_geometry_nodes_modifier,
    ("geonode_instance", "has_gn_instance"): _has_instance,
    ("geonode_scatter", "has_gn_scatter"): _has_scatter,
    ("geonode_attribute", "has_gn_attribute"): _has_attribute,
    ("geonode_curve_to_mesh", "has_gn_curve_to_mesh"): _has_curve_to_mesh,
    ("geonode_noise_deform", "has_gn_noise"): _has_noise,
    ("geonode_noise_deform", "has_gn_set_position"): _has_set_position,
    ("geonode_group_input", "has_gn_group_input"): _has_group_input,
    ("geonode_convex_hull", "has_gn_convex_hull"): _has_convex_hull,
    ("geonode_boolean_node", "has_gn_boolean"): _has_boolean,
    ("geonode_realize_instances", "has_gn_realize"): _has_realize_instances,
    ("geonode_field_math", "has_gn_field_math"): _has_field_math,
    ("geonode_domain_switch", "has_gn_domain_switch"): _has_domain_switch,
    ("geonode_simulation", "has_gn_simulation"): _has_simulation,
}
