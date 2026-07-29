from __future__ import annotations

import importlib.util
import json
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


def unlock(module, ach_id: str) -> None:
    module.stats.unlocked.add(ach_id)
    module.stats.unlock_hashes[ach_id] = module._make_unlock_hash(ach_id)


def reward(module, ach_id: str) -> dict:
    return next(item for item in module.ACHIEVEMENTS_DEF if item["id"] == ach_id)


def reward_asset_path(module, achievement: dict) -> Path:
    path = Path(module.DATA_DIR) / achievement["reward_data"]["blend_file"]
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def set_active(obj) -> None:
    for selected in tuple(bpy.context.selected_objects):
        selected.select_set(False)
    bpy.context.view_layer.objects.active = obj
    if obj is not None:
        obj.select_set(True)


def apply_reward(ach_id: str):
    return bpy.ops.ach.apply_reward(ach_id=ach_id)


def expect_cancelled(ach_id: str, message: str) -> None:
    try:
        result = apply_reward(ach_id)
    except RuntimeError as error:
        if message not in str(error):
            fail(f"unexpected reward denial error: {error}")
        return
    if result != {"CANCELLED"}:
        fail(f"reward {ach_id} returned {result}, expected CANCELLED")


def marker_matches(module, datablock, achievement: dict) -> bool:
    return (
        datablock is not None
        and datablock.get(module._REWARD_MARKER_ID) == achievement["id"]
        and datablock.get(module._REWARD_MARKER_TYPE) == achievement["reward_type"]
        and datablock.get(module._REWARD_MARKER_NAME) == achievement["reward_data"]["name"]
    )


def material_witnesses(module, achievement: dict) -> tuple[int, ...]:
    pointers = {
        material.as_pointer()
        for obj in bpy.data.objects
        if obj.type == "MESH"
        for material in obj.data.materials
        if marker_matches(module, material, achievement)
    }
    return tuple(sorted(pointers))


def mesh_witnesses(module, achievement: dict) -> tuple[int, ...]:
    return tuple(
        sorted(
            obj.as_pointer()
            for obj in bpy.data.objects
            if obj.type == "MESH"
            and obj.users_collection
            and marker_matches(module, obj, achievement)
        )
    )


def geo_witnesses(module, achievement: dict) -> tuple[tuple[int, int, int], ...]:
    return tuple(
        sorted(
            (obj.as_pointer(), modifier.as_pointer(), modifier.node_group.as_pointer())
            for obj in bpy.data.objects
            for modifier in obj.modifiers
            if marker_matches(module, getattr(modifier, "node_group", None), achievement)
        )
    )


def saved_claims(module) -> set[str]:
    data_file = Path(module.DATA_FILE)
    if not data_file.is_file():
        return set()
    return set(json.loads(data_file.read_text(encoding="utf-8")).get("rewards_claimed", []))


def blender_id_pointers() -> set[int]:
    return {datablock.as_pointer() for datablock in bpy.data.user_map()}


def material_state_for_mesh(mesh) -> tuple:
    data_materials = tuple(
        material.as_pointer() if material is not None else 0
        for material in mesh.materials
    )
    owners = tuple(
        sorted(
            (
                obj.as_pointer(),
                obj.active_material_index,
                tuple(
                    (
                        slot.link,
                        slot.material.as_pointer() if slot.material is not None else 0,
                    )
                    for slot in obj.material_slots
                ),
            )
            for obj in bpy.data.objects
            if obj.type == "MESH" and obj.data == mesh
        )
    )
    return data_materials, owners


def write_material_library(path: Path, name: str) -> None:
    material = bpy.data.materials.new(name=name)
    try:
        bpy.data.libraries.write(str(path), {material})
    finally:
        bpy.data.materials.remove(material)


def write_mesh_library(path: Path, name: str) -> None:
    mesh = bpy.data.meshes.new(name=f"{name}_Mesh")
    obj = bpy.data.objects.new(name=name, object_data=mesh)
    try:
        bpy.data.libraries.write(str(path), {obj})
    finally:
        bpy.data.objects.remove(obj, do_unlink=True)
        if mesh.users == 0:
            bpy.data.meshes.remove(mesh)


def write_wrong_object_library(path: Path, name: str) -> None:
    curve = bpy.data.curves.new(name=f"{name}_Curve", type="CURVE")
    material = bpy.data.materials.new(name=f"{name}_NestedMaterial")
    curve.materials.append(material)
    obj = bpy.data.objects.new(name=name, object_data=curve)
    try:
        bpy.data.libraries.write(str(path), {obj})
    finally:
        bpy.data.objects.remove(obj, do_unlink=True)
        if curve.users == 0:
            bpy.data.curves.remove(curve)
        if material.users == 0:
            bpy.data.materials.remove(material)


def configure_geometry_node_group(node_group) -> None:
    node_group.interface.new_socket(
        name="Geometry",
        in_out="INPUT",
        socket_type="NodeSocketGeometry",
    )
    node_group.interface.new_socket(
        name="Geometry",
        in_out="OUTPUT",
        socket_type="NodeSocketGeometry",
    )
    group_input = node_group.nodes.new("NodeGroupInput")
    group_output = node_group.nodes.new("NodeGroupOutput")
    node_group.links.new(
        group_input.outputs["Geometry"],
        group_output.inputs["Geometry"],
    )


def write_node_group_library(path: Path, name: str, tree_type: str) -> None:
    node_group = bpy.data.node_groups.new(name=name, type=tree_type)
    dependency_image = None
    try:
        if tree_type == "GeometryNodeTree":
            configure_geometry_node_group(node_group)
        elif tree_type == "ShaderNodeTree":
            dependency_image = bpy.data.images.new(
                name=f"{name}_NestedImage",
                width=1,
                height=1,
            )
            image_node = node_group.nodes.new("ShaderNodeTexImage")
            image_node.image = dependency_image
        bpy.data.libraries.write(str(path), {node_group})
    finally:
        bpy.data.node_groups.remove(node_group)
        if dependency_image is not None and dependency_image.users == 0:
            bpy.data.images.remove(dependency_image)


def exercise_save_failure_retry(module, achievement: dict, activate, witnesses) -> None:
    unlock(module, achievement["id"])
    activate()
    original_bytes = Path(module.DATA_FILE).read_bytes()
    original_writer = module.ach_persistence.atomic_write_json
    attempted_payloads = []

    def fail_write(_path, payload, **_kwargs):
        attempted_payloads.append(payload)
        raise OSError("forced reward claim write failure")

    module.ach_persistence.atomic_write_json = fail_write
    try:
        first_result = apply_reward(achievement["id"])
        first_witnesses = witnesses(module, achievement)
        activate()
        second_result = apply_reward(achievement["id"])
        second_witnesses = witnesses(module, achievement)
    finally:
        module.ach_persistence.atomic_write_json = original_writer

    if first_result != {"FINISHED"} or second_result != {"FINISHED"}:
        fail(f"save-failure retry returned {first_result}, {second_result}")
    if len(first_witnesses) != 1 or second_witnesses != first_witnesses:
        fail(
            f"reward retry duplicated or lost witness: first={first_witnesses}, "
            f"second={second_witnesses}"
        )
    if len(attempted_payloads) != 2:
        fail(f"expected two prospective claim writes, got {len(attempted_payloads)}")
    if any(achievement["id"] not in payload["rewards_claimed"] for payload in attempted_payloads):
        fail("prospective payload omitted reward claim")
    if achievement["id"] in module.stats.rewards_claimed:
        fail("failed save left a false in-memory reward claim")
    if achievement["id"] in saved_claims(module):
        fail("failed save changed the persisted reward claim")
    if Path(module.DATA_FILE).read_bytes() != original_bytes:
        fail("failed save changed the previous JSON bytes")

    activate()
    recovered_result = apply_reward(achievement["id"])
    if recovered_result != {"FINISHED"}:
        fail(f"recovered reward returned {recovered_result}")
    if witnesses(module, achievement) != first_witnesses:
        fail("successful retry duplicated the recovered reward witness")
    if achievement["id"] not in module.stats.rewards_claimed:
        fail("successful retry did not commit the in-memory claim")
    if achievement["id"] not in saved_claims(module):
        fail("successful retry did not persist the reward claim")


def main() -> None:
    module = load_addon()
    module.register()
    try:
        bpy.ops.mesh.primitive_cube_add()
        cube = bpy.context.object

        integrity_ach = reward(module, "hundred_renders")
        module.stats.unlocked.add(integrity_ach["id"])
        module.stats.unlock_hashes.pop(integrity_ach["id"], None)
        expect_cancelled(integrity_ach["id"], "Unlock verification failed")
        module.stats.unlock_hashes[integrity_ach["id"]] = "forged"
        expect_cancelled(integrity_ach["id"], "Unlock verification failed")
        if integrity_ach["id"] in module.stats.rewards_claimed:
            fail("invalid integrity marker claimed material reward")

        write_calls = []
        original_writer = module.ach_persistence.atomic_write_json

        def spy_write(path, payload, **kwargs):
            write_calls.append((path, payload))
            return original_writer(path, payload, **kwargs)

        module.ach_persistence.atomic_write_json = spy_write
        try:
            no_target_material = reward(module, "thousand_faces")
            unlock(module, no_target_material["id"])
            set_active(None)
            before_materials = len(bpy.data.materials)
            expect_cancelled(no_target_material["id"], "Reward could not be applied")
            if len(bpy.data.materials) != before_materials:
                fail("no-target material fallback created an orphan material")

            no_target_geo = reward(module, "ten_dense_meshes")
            unlock(module, no_target_geo["id"])
            before_modifiers = sum(len(obj.modifiers) for obj in bpy.data.objects)
            expect_cancelled(no_target_geo["id"], "Reward could not be applied")
            if sum(len(obj.modifiers) for obj in bpy.data.objects) != before_modifiers:
                fail("no-target geo fallback created a modifier")
            if no_target_geo["id"] in module.stats.rewards_claimed:
                fail("no-target geo fallback created an in-memory claim")

            non_mesh_target = bpy.data.objects.new(name="RewardNonMeshTarget", object_data=None)
            bpy.context.collection.objects.link(non_mesh_target)
            non_mesh_material = reward(module, "ten_thousand_vertices")
            unlock(module, non_mesh_material["id"])
            set_active(non_mesh_target)
            before_materials = len(bpy.data.materials)
            expect_cancelled(non_mesh_material["id"], "Reward could not be applied")
            if len(bpy.data.materials) != before_materials:
                fail("non-mesh material fallback created an orphan material")

            incompatible_linked_geo = reward(module, "architect")
            unlock(module, incompatible_linked_geo["id"])
            write_node_group_library(
                reward_asset_path(module, incompatible_linked_geo),
                incompatible_linked_geo["reward_data"]["name"],
                "GeometryNodeTree",
            )
            light_data = bpy.data.lights.new(name="RewardIncompatibleLight", type="POINT")
            incompatible_target = bpy.data.objects.new(
                name="RewardIncompatibleTarget",
                object_data=light_data,
            )
            bpy.context.collection.objects.link(incompatible_target)
            set_active(incompatible_target)
            before_incompatible_ids = blender_id_pointers()
            before_incompatible_modifiers = len(incompatible_target.modifiers)
            expect_cancelled(incompatible_linked_geo["id"], "Reward could not be applied")
            if blender_id_pointers() != before_incompatible_ids:
                fail("incompatible linked geo denial changed Blender IDs")
            if len(incompatible_target.modifiers) != before_incompatible_modifiers:
                fail("incompatible linked geo denial created a modifier")
            expect_cancelled(no_target_geo["id"], "Reward could not be applied")
            if blender_id_pointers() != before_incompatible_ids:
                fail("incompatible fallback geo denial changed Blender IDs")
            if len(incompatible_target.modifiers) != before_incompatible_modifiers:
                fail("incompatible fallback geo denial created a modifier")
            for achievement in (incompatible_linked_geo, no_target_geo):
                if achievement["id"] in module.stats.rewards_claimed:
                    fail("incompatible geo denial created an in-memory claim")
                if achievement["id"] in saved_claims(module):
                    fail("incompatible geo denial created a persisted claim")
            bpy.data.objects.remove(incompatible_target, do_unlink=True)
            if light_data.users == 0:
                bpy.data.lights.remove(light_data)

            missing_datablock = reward(module, "five_hours")
            unlock(module, missing_datablock["id"])
            write_material_library(
                reward_asset_path(module, missing_datablock),
                "ACH_UnexpectedMaterial",
            )
            set_active(cube)
            expect_cancelled(missing_datablock["id"], "Reward could not be applied")

            missing_mesh = reward(module, "fifty_dense_meshes")
            unlock(module, missing_mesh["id"])
            write_mesh_library(
                reward_asset_path(module, missing_mesh),
                "ACH_UnexpectedMesh",
            )
            expect_cancelled(missing_mesh["id"], "Reward could not be applied")

            missing_geo = reward(module, "hundred_thousand_vertices")
            unlock(module, missing_geo["id"])
            write_node_group_library(
                reward_asset_path(module, missing_geo),
                "ACH_UnexpectedGeo",
                "GeometryNodeTree",
            )
            expect_cancelled(missing_geo["id"], "Reward could not be applied")

            wrong_mesh_type = reward(module, "million_vertices")
            unlock(module, wrong_mesh_type["id"])
            write_wrong_object_library(
                reward_asset_path(module, wrong_mesh_type),
                wrong_mesh_type["reward_data"]["name"],
            )
            before_object_ids = blender_id_pointers()
            expect_cancelled(wrong_mesh_type["id"], "Reward could not be applied")
            if blender_id_pointers() != before_object_ids:
                fail("wrong-type mesh library left a loaded object behind or dependency")

            wrong_geo_type = reward(module, "hundred_hours")
            unlock(module, wrong_geo_type["id"])
            write_node_group_library(
                reward_asset_path(module, wrong_geo_type),
                wrong_geo_type["reward_data"]["name"],
                "ShaderNodeTree",
            )
            before_group_ids = blender_id_pointers()
            expect_cancelled(wrong_geo_type["id"], "Reward could not be applied")
            if blender_id_pointers() != before_group_ids:
                fail("wrong-type geo library left a loaded node group behind or dependency")

            corrupt_asset = reward(module, "twenty_materials")
            unlock(module, corrupt_asset["id"])
            reward_asset_path(module, corrupt_asset).write_bytes(b"not a blend file")
            expect_cancelled(corrupt_asset["id"], "Reward application failed")

            rollback_material = reward(module, "hundred_materials")
            unlock(module, rollback_material["id"])
            set_active(cube)
            data_material = bpy.data.materials.new(name="RollbackDataMaterial")
            data_material_second = bpy.data.materials.new(
                name="RollbackDataMaterialSecond"
            )
            object_material = bpy.data.materials.new(name="RollbackObjectMaterial")
            shared_material = bpy.data.materials.new(name="RollbackSharedMaterial")
            cube.data.materials.append(data_material)
            cube.data.materials.append(None)
            cube.data.materials.append(data_material_second)
            cube.material_slots[0].link = "OBJECT"
            cube.material_slots[0].material = object_material
            cube.active_material_index = 2
            shared_owner = bpy.data.objects.new(
                name="RollbackSharedOwner",
                object_data=cube.data,
            )
            bpy.context.collection.objects.link(shared_owner)
            shared_owner.material_slots[0].link = "OBJECT"
            shared_owner.material_slots[0].material = shared_material
            shared_owner.material_slots[1].link = "OBJECT"
            shared_owner.material_slots[1].material = None
            shared_owner.active_material_index = 1
            before_material_ids = blender_id_pointers()
            before_material_slots = material_state_for_mesh(cube.data)
            original_apply_material = module.ACH_OT_ApplyReward._apply_material

            def fail_after_material_apply(self, material, obj):
                original_apply_material(self, material, obj)
                raise RuntimeError("forced material apply failure")

            module.ACH_OT_ApplyReward._apply_material = fail_after_material_apply
            try:
                expect_cancelled(rollback_material["id"], "forced material apply failure")
            finally:
                module.ACH_OT_ApplyReward._apply_material = original_apply_material
            if blender_id_pointers() != before_material_ids:
                fail("failed material application left new Blender IDs")
            if material_state_for_mesh(cube.data) != before_material_slots:
                fail("failed material application did not restore linked material slots")
            bpy.data.objects.remove(shared_owner, do_unlink=True)
            cube.data.materials.clear()
            for material in (
                data_material,
                data_material_second,
                object_material,
                shared_material,
            ):
                if material.users == 0:
                    bpy.data.materials.remove(material)

            rollback_mesh = reward(module, "fifty_hours")
            unlock(module, rollback_mesh["id"])
            before_mesh_ids = blender_id_pointers()
            original_ensure_linked = module.ACH_OT_ApplyReward._ensure_object_linked

            def fail_after_object_link(self, context, obj):
                original_ensure_linked(self, context, obj)
                raise RuntimeError("forced object link failure")

            module.ACH_OT_ApplyReward._ensure_object_linked = fail_after_object_link
            try:
                expect_cancelled(rollback_mesh["id"], "forced object link failure")
            finally:
                module.ACH_OT_ApplyReward._ensure_object_linked = original_ensure_linked
            if blender_id_pointers() != before_mesh_ids:
                fail("failed mesh application left new Blender IDs")

            rollback_geo = incompatible_linked_geo
            set_active(cube)
            before_geo_ids = blender_id_pointers()
            before_geo_modifiers = len(cube.modifiers)
            original_marker_matches = module.ACH_OT_ApplyReward._marker_matches

            def fail_after_modifier_assignment(self, datablock, reward_type, name):
                if (
                    datablock is not None
                    and datablock.get(module._REWARD_MARKER_ID) == rollback_geo["id"]
                ):
                    raise RuntimeError("forced modifier validation failure")
                return original_marker_matches(self, datablock, reward_type, name)

            module.ACH_OT_ApplyReward._marker_matches = fail_after_modifier_assignment
            try:
                expect_cancelled(rollback_geo["id"], "forced modifier validation failure")
            finally:
                module.ACH_OT_ApplyReward._marker_matches = original_marker_matches
            if blender_id_pointers() != before_geo_ids:
                fail("failed geo application left new Blender IDs")
            if len(cube.modifiers) != before_geo_modifiers:
                fail("failed geo application left a modifier")
            if rollback_geo["id"] in module.stats.rewards_claimed:
                fail("failed geo application created an in-memory claim")
            if rollback_geo["id"] in saved_claims(module):
                fail("failed geo application persisted a claim")
        finally:
            module.ach_persistence.atomic_write_json = original_writer

        if write_calls:
            fail(f"failed/no-op actions attempted persistence: {len(write_calls)}")
        denied_ids = {
            no_target_material["id"],
            non_mesh_material["id"],
            missing_datablock["id"],
            missing_mesh["id"],
            missing_geo["id"],
            wrong_mesh_type["id"],
            wrong_geo_type["id"],
            corrupt_asset["id"],
            rollback_material["id"],
            rollback_mesh["id"],
        }
        if denied_ids & module.stats.rewards_claimed:
            fail("failed/no-op action created a reward claim")

        curve_geo = no_target_geo
        curve_data = bpy.data.curves.new(name="RewardSupportedCurve", type="CURVE")
        curve_target = bpy.data.objects.new(
            name="RewardSupportedCurveTarget",
            object_data=curve_data,
        )
        bpy.context.collection.objects.link(curve_target)
        set_active(curve_target)
        curve_result = apply_reward(curve_geo["id"])
        curve_witness = geo_witnesses(module, curve_geo)
        if curve_result != {"FINISHED"} or len(curve_witness) != 1:
            fail("compatible curve geo reward was not applied")
        curve_modifier = next(
            modifier
            for modifier in curve_target.modifiers
            if marker_matches(module, getattr(modifier, "node_group", None), curve_geo)
        )
        if curve_modifier.type != "NODES" or curve_modifier.node_group is None:
            fail("compatible curve geo reward lacks its confirmed postcondition")
        if curve_geo["id"] not in module.stats.rewards_claimed:
            fail("compatible curve geo reward was not claimed")
        if curve_geo["id"] not in saved_claims(module):
            fail("compatible curve geo reward claim was not persisted")

        linked_material = reward(module, "thousand_vertices")
        linked_mesh = reward(module, "blender_legend")
        linked_geo = reward(module, "architect")
        write_material_library(
            reward_asset_path(module, linked_material),
            linked_material["reward_data"]["name"],
        )
        write_mesh_library(
            reward_asset_path(module, linked_mesh),
            linked_mesh["reward_data"]["name"],
        )
        write_node_group_library(
            reward_asset_path(module, linked_geo),
            linked_geo["reward_data"]["name"],
            "GeometryNodeTree",
        )
        if not module.save_data():
            fail("could not create baseline JSON before linked reward retries")
        exercise_save_failure_retry(
            module,
            linked_material,
            lambda: set_active(cube),
            material_witnesses,
        )
        exercise_save_failure_retry(
            module,
            linked_mesh,
            lambda: set_active(cube),
            mesh_witnesses,
        )
        exercise_save_failure_retry(
            module,
            linked_geo,
            lambda: set_active(curve_target),
            geo_witnesses,
        )

        if len(material_witnesses(module, linked_material)) != 1:
            fail("linked material was not applied as the expected marked datablock")
        if len(mesh_witnesses(module, linked_mesh)) != 1:
            fail("linked mesh object was not linked as the expected marked datablock")
        linked_geo_witness = geo_witnesses(module, linked_geo)
        if len(linked_geo_witness) != 1:
            fail("linked geo modifier was not applied")
        linked_modifier = next(
            modifier
            for obj in bpy.data.objects
            for modifier in obj.modifiers
            if marker_matches(module, getattr(modifier, "node_group", None), linked_geo)
        )
        if not marker_matches(module, linked_modifier.node_group, linked_geo):
            fail("linked geo modifier does not use the expected marked node group")

        before_reapply = mesh_witnesses(module, linked_mesh)
        original_json = Path(module.DATA_FILE).read_bytes()
        write_calls.clear()
        module.ach_persistence.atomic_write_json = spy_write
        try:
            result = apply_reward(linked_mesh["id"])
        finally:
            module.ach_persistence.atomic_write_json = original_writer
        after_reapply = mesh_witnesses(module, linked_mesh)
        if result != {"FINISHED"} or len(after_reapply) != len(before_reapply) + 1:
            fail("persisted mesh reward no longer preserves reapply behavior")
        if write_calls or Path(module.DATA_FILE).read_bytes() != original_json:
            fail("persisted reward reapply attempted redundant claim persistence")

        fallback_material = reward(module, "smooth_cube")
        fallback_mesh = reward(module, "sphere_from_cube")
        fallback_geo = reward(module, "procedural_master")
        exercise_save_failure_retry(
            module,
            fallback_material,
            lambda: set_active(cube),
            material_witnesses,
        )
        exercise_save_failure_retry(
            module,
            fallback_mesh,
            lambda: set_active(None),
            mesh_witnesses,
        )
        exercise_save_failure_retry(
            module,
            fallback_geo,
            lambda: set_active(cube),
            geo_witnesses,
        )

        expected_claims = {
            curve_geo["id"],
            linked_material["id"],
            linked_mesh["id"],
            linked_geo["id"],
            fallback_material["id"],
            fallback_mesh["id"],
            fallback_geo["id"],
        }
        if module.stats.rewards_claimed != expected_claims:
            fail(f"runtime reward claims are not exact: {module.stats.rewards_claimed}")
        saved_payload = json.loads(Path(module.DATA_FILE).read_text(encoding="utf-8"))
        if saved_payload.get("schema_version") != "1.0.0":
            fail("reward persistence changed schema_version")
        if set(saved_payload) != set(module.ach_persistence.default_payload()):
            fail("reward persistence changed the exact payload key set")
        saved_list = saved_payload.get("rewards_claimed", [])
        if saved_list != sorted(expected_claims) or len(saved_list) != len(set(saved_list)):
            fail(f"persisted reward claims are not exact/sorted/unique: {saved_list}")
        if denied_ids & set(saved_list):
            fail("failed/no-op reward IDs reached persisted claims")
        module.stats.rewards_claimed.clear()
        module.load_data()
        if module.stats.rewards_claimed != expected_claims:
            fail("exact reward claims did not survive load_data")
    finally:
        module.unregister()

    print(
        "[smoke_rewards:PASS] linked/fallback action proof, no-op denial, "
        "prospective claims, and idempotent save retry clean"
    )


if __name__ == "__main__":
    main()
