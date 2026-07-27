from __future__ import annotations

import ast
import datetime
import sys
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from achievements.catalog import ACHIEVEMENTS_DEF  # noqa: E402
from achievements.predicates import (  # noqa: E402
    PREDICATE_PAIRS,
    ClockSnapshot,
    PredicateContext,
    StatsSnapshot,
    evaluate_predicate,
    registry_bijection_errors,
)


class Inputs(list):
    def get(self, name: str):
        return next((node_input for node_input in self if node_input.name == name), None)


class ViewLayers(list):
    def __contains__(self, value):
        if isinstance(value, str):
            return any(layer.name == value for layer in self)
        return super().__contains__(value)


def ns(**values):
    return SimpleNamespace(**values)


def node(
    bl_idname: str,
    *,
    node_type: str = "CUSTOM",
    name: str | None = None,
    label: str = "",
    inputs: Inputs | None = None,
    outputs: list[object] | None = None,
    image: object | None = None,
):
    return ns(
        bl_idname=bl_idname,
        type=node_type,
        name=name or bl_idname,
        label=label,
        inputs=inputs or Inputs(),
        outputs=outputs or [],
        image=image,
    )


def material(name: str, nodes: list[object]):
    return ns(name=name, use_nodes=True, node_tree=ns(nodes=nodes))


def modifier(modifier_type: str, **values):
    return ns(type=modifier_type, **values)


def mesh_data(name: str, material_value, *, animated: bool = True):
    animation_data = ns(action=object()) if animated else None
    return ns(
        name=name,
        materials=[material_value],
        uv_layers=[object()],
        shape_keys=ns(key_blocks=[object(), object()], animation_data=animation_data),
    )


def mesh_object(name: str, data, *, modifiers=None, location_length: float = 0.0):
    return ns(
        name=name,
        type="MESH",
        data=data,
        modifiers=list(modifiers or []),
        particle_systems=[object()],
        location=ns(length=location_length),
    )


def rich_context() -> PredicateContext:
    linked_input = lambda name, value=0.0: ns(  # noqa: E731 - concise fixture factory.
        name=name,
        default_value=value,
        is_linked=True,
    )
    principled_inputs = Inputs(
        [
            linked_input("Base Color"),
            linked_input("Normal"),
            linked_input("Transmission Weight", 1.0),
            linked_input("Subsurface Weight", 1.0),
        ]
    )
    glass_inputs = Inputs([linked_input("IOR", 1.45)])
    output_inputs = Inputs([linked_input("Displacement")])
    material_nodes = [
        node("ShaderNodeTexImage"),
        node("ShaderNodeEmission"),
        node("ShaderNodeBsdfGlass", inputs=glass_inputs),
        node("ShaderNodeMixShader"),
        node("ShaderNodeBsdfPrincipled", inputs=principled_inputs),
        node("ShaderNodeNormalMap"),
        node("ShaderNodeVertexColor"),
        node("ShaderNodeAttribute"),
        node("ShaderNodeOutputMaterial", inputs=output_inputs),
        node("ShaderNodeVolumeScatter"),
    ]
    materials = [
        material("Primary", material_nodes),
        material("ProceduralOnly", [node("ShaderNodeTexNoise")]),
        material("Unique2", []),
        material("Unique3", []),
    ]

    geometry_nodes = [
        node("NodeGroupInput", node_type="GROUP_INPUT", outputs=[object()] * 3),
        node("GeometryNodeInstanceOnPoints"),
        node("GeometryNodeDistributePointsOnFaces"),
        node("GeometryNodeStoreNamedAttribute"),
        node("GeometryNodeCurveToMesh"),
        node("ShaderNodeTexNoise"),
        node("GeometryNodeSetPosition"),
        node("GeometryNodeConvexHull"),
        node("GeometryNodeMeshBoolean"),
        node("GeometryNodeRealizeInstances"),
        node("GeometryNodeSampleIndex"),
        node("GeometryNodeSimulationInput"),
    ]
    geometry_tree = ns(name="Smooth Geometry", nodes=geometry_nodes, links=[object()])
    modifiers = [
        modifier("SUBSURF"),
        modifier("SMOOTH"),
        modifier("MIRROR"),
        modifier("BOOLEAN"),
        modifier("SOLIDIFY"),
        modifier("BEVEL"),
        modifier("SCREW"),
        modifier("ARRAY", use_object_offset=True, offset_object=object()),
        modifier("SHRINKWRAP", target=object()),
        modifier("ARMATURE", object=object()),
        modifier("CURVE", object=object()),
        modifier("SKIN"),
        modifier("WEIGHTED_NORMAL"),
        modifier("MULTIRES", levels=2),
        modifier("NODES", node_group=geometry_tree),
    ]
    shared_data = mesh_data("SharedMesh", materials[0])
    primary = mesh_object(
        "Primary",
        shared_data,
        modifiers=modifiers,
        location_length=1.0,
    )
    linked = [mesh_object(f"Linked{index}", shared_data) for index in range(19)]
    unique = [
        mesh_object("Unique2", mesh_data("Unique2", materials[2])),
        mesh_object("Unique3", mesh_data("Unique3", materials[3])),
    ]
    light_types = ("POINT", "AREA", "SUN")
    lights = [
        ns(type="LIGHT", data=ns(type=light_types[index % 3])) for index in range(10)
    ]
    objects = [primary, *linked, *unique, *lights]
    collections = [ns(objects=[primary, *unique])] + [ns(objects=[primary]) for _ in range(4)]

    view_layer = ns(
        name="Main",
        use_pass_diffuse_direct=True,
        use_pass_diffuse_indirect=True,
        use_pass_diffuse_color=True,
        use_pass_glossy_direct=True,
        use_pass_glossy_indirect=True,
    )
    world_nodes = [
        node("ShaderNodeTexEnvironment", image=object()),
        node("ShaderNodeVolumeScatter"),
    ]
    scene = ns(
        objects=objects,
        tool_settings=ns(use_snap=True, snap_elements={"FACE"}),
        world=ns(use_nodes=True, node_tree=ns(nodes=world_nodes)),
        camera=ns(
            data=ns(
                dof=ns(use_dof=True, focus_object=object(), focus_distance=10.0)
            )
        ),
        render=ns(use_motion_blur=True),
        cycles=ns(
            use_denoising=True,
            caustics_reflective=True,
            caustics_refractive=False,
        ),
        use_nodes=True,
        node_tree=ns(nodes=[node("CompositorNodeBlur", node_type="BLUR")]),
        view_layers=ViewLayers([view_layer]),
    )
    stats = StatsSnapshot(
        renders_completed=1,
        time_spent=7 * 3600,
        time_at_session_start=0,
        daily_sessions=tuple(
            (datetime.date(2026, 1, 1) + datetime.timedelta(days=index)).isoformat()
            for index in range(30)
        ),
        speed_model_start=900.0,
        speed_model_verts=100,
        vertices_created=700,
        unlocked=frozenset(f"achievement-{index}" for index in range(50)),
    )
    return PredicateContext(
        scene=scene,
        data=ns(collections=collections, materials=materials, images=[ns(is_dirty=True)]),
        view_layer=view_layer,
        stats=stats,
        clock=ClockSnapshot(datetime.datetime(2026, 1, 3, 23, 0), 1000.0),
    )


def empty_context() -> PredicateContext:
    scene = ns(
        objects=[],
        tool_settings=ns(use_snap=False, snap_elements=set()),
        world=None,
        camera=None,
        render=ns(use_motion_blur=False),
        cycles=ns(
            use_denoising=False,
            caustics_reflective=False,
            caustics_refractive=False,
        ),
        use_nodes=False,
        node_tree=None,
        view_layers=ViewLayers(),
    )
    return PredicateContext(
        scene=scene,
        data=ns(collections=[], materials=[], images=[]),
        view_layer=None,
        stats=StatsSnapshot(),
        clock=ClockSnapshot(datetime.datetime(2026, 1, 5, 12, 0), 1000.0),
    )


CATALOG_PAIRS = sorted(
    (achievement["complex_id"], step["check"])
    for achievement in ACHIEVEMENTS_DEF
    if achievement["check_type"] == "complex"
    for step in achievement["steps"]
)


def positive_context(pair: tuple[str, str]) -> PredicateContext:
    context = rich_context()
    if pair == ("early_bird", "is_early_bird"):
        return replace(
            context,
            clock=ClockSnapshot(datetime.datetime(2026, 1, 3, 6, 0), 1000.0),
        )
    return context


def with_scene(context: PredicateContext, **changes) -> PredicateContext:
    scene_values = vars(context.scene) | changes
    return replace(context, scene=ns(**scene_values))


def test_registry_is_exact_catalog_bijection():
    assert len(CATALOG_PAIRS) == 85
    assert len({complex_id for complex_id, _step in CATALOG_PAIRS}) == 65
    assert frozenset(CATALOG_PAIRS) == PREDICATE_PAIRS
    assert registry_bijection_errors(ACHIEVEMENTS_DEF) == ()


@pytest.mark.parametrize(("complex_id", "step_check"), CATALOG_PAIRS)
def test_each_catalog_predicate_has_positive_characterization(complex_id, step_check):
    result = evaluate_predicate(
        complex_id,
        step_check,
        positive_context((complex_id, step_check)),
    )
    assert result.error is None
    assert result.matched is True


@pytest.mark.parametrize(("complex_id", "step_check"), CATALOG_PAIRS)
def test_each_catalog_predicate_has_negative_characterization(complex_id, step_check):
    result = evaluate_predicate(complex_id, step_check, empty_context())
    assert result.error is None
    assert result.matched is False


@pytest.mark.parametrize(("complex_id", "step_check"), CATALOG_PAIRS)
def test_each_catalog_predicate_is_exception_safe(complex_id, step_check):
    context = replace(empty_context(), scene=None, data=None, view_layer=None)
    result = evaluate_predicate(complex_id, step_check, context)
    assert result.matched is False


def test_speed_modeler_returns_immutable_reset_plan_without_mutation():
    context = rich_context()
    expired_stats = replace(
        context.stats,
        speed_model_start=100.0,
        vertices_created=321,
        speed_model_verts=0,
    )
    result = evaluate_predicate(
        "speed_modeler",
        "is_speed_modeler",
        replace(context, stats=expired_stats, clock=replace(context.clock, timestamp=1000.0)),
    )
    assert result.matched is False
    assert result.speed_model_reset is not None
    assert result.speed_model_reset.started_at == 1000.0
    assert result.speed_model_reset.vertices_created == 321
    assert expired_stats.speed_model_start == 100.0


def test_unknown_pair_fails_closed():
    result = evaluate_predicate("unknown", "unknown", rich_context())
    assert result.matched is False
    assert result.error is None


def test_mirror_and_subdivision_keep_cross_object_step_semantics():
    context = empty_context()
    mirror_object = mesh_object(
        "Mirror",
        mesh_data("Mirror", material("Mirror", [])),
        modifiers=[modifier("MIRROR")],
    )
    subdivision_object = mesh_object(
        "Subdivision",
        mesh_data("Subdivision", material("Subdivision", [])),
        modifiers=[modifier("SUBSURF")],
    )
    context = with_scene(context, objects=[mirror_object, subdivision_object])
    assert evaluate_predicate(
        "mirror_subdivision", "has_mirror", context
    ).matched
    assert evaluate_predicate(
        "mirror_subdivision", "has_subsurf", context
    ).matched


def test_custom_origin_keeps_nonzero_location_approximation():
    context = empty_context()
    moved_mesh = mesh_object(
        "Moved",
        mesh_data("Moved", material("Moved", [])),
        location_length=0.002,
    )
    context = with_scene(context, objects=[moved_mesh])
    assert evaluate_predicate("custom_origin", "custom_origin_set", context).matched


def test_particle_predicate_does_not_silently_add_wind_support():
    context = with_scene(
        empty_context(),
        objects=[ns(type="FIELD", field=ns(type="WIND"))],
    )
    assert not evaluate_predicate("particle_system", "has_particles", context).matched


def test_procedural_without_image_requires_one_qualifying_material():
    mixed = material(
        "Mixed",
        [node("ShaderNodeTexNoise"), node("ShaderNodeTexImage")],
    )
    context = replace(empty_context(), data=ns(collections=[], materials=[mixed], images=[]))
    assert evaluate_predicate(
        "procedural_texture", "has_procedural", context
    ).matched
    assert not evaluate_predicate(
        "procedural_texture", "no_image_texture", context
    ).matched


def test_predicate_package_has_no_bpy_imports():
    for path in sorted((ROOT / "achievements" / "predicates").glob("*.py")):
        module = ast.parse(path.read_text(encoding="utf-8"))
        for syntax_node in ast.walk(module):
            if isinstance(syntax_node, ast.Import):
                assert all(alias.name != "bpy" for alias in syntax_node.names)
            if isinstance(syntax_node, ast.ImportFrom):
                assert syntax_node.module != "bpy"


def test_root_complex_step_function_is_only_a_blender_adapter():
    module = ast.parse((ROOT / "__init__.py").read_text(encoding="utf-8"))
    function = next(
        syntax_node
        for syntax_node in module.body
        if isinstance(syntax_node, ast.FunctionDef)
        and syntax_node.name == "_check_complex_step"
    )
    calls = {
        syntax_node.func.attr
        for syntax_node in ast.walk(function)
        if isinstance(syntax_node, ast.Call)
        and isinstance(syntax_node.func, ast.Attribute)
    }
    embedded_complex_ids = {
        syntax_node.value
        for syntax_node in ast.walk(function)
        if isinstance(syntax_node, ast.Constant)
        and isinstance(syntax_node.value, str)
        and syntax_node.value in {complex_id for complex_id, _step in PREDICATE_PAIRS}
    }
    assert "evaluate_predicate" in calls
    assert not embedded_complex_ids
    assert function.end_lineno - function.lineno < 50
