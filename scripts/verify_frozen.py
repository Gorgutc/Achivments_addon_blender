from __future__ import annotations

import ast
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "__init__.py"
DUPLICATE_ADDON = ROOT / "achievements_v01 (4).py"
ARCHIVED_100_LIST = ROOT / "docs" / "archive" / "achievements_100_list.md"
DUPLICATE_RETIREMENT_ADR = (
    ROOT / "docs" / "agent" / "adrs" / "0002-retire-legacy-runtime-duplicate.md"
)
sys.path.insert(0, str(ROOT))

from achievements import catalog, levels, predicates  # noqa: E402

USER_DATA_MARKERS = {"achievements_data.json", "BlenderAchievements"}
VALID_CHECK_TYPES = {"stat", "complex"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_REWARD_TYPES = {"tutorial", "material", "mesh", "geo_nodes", "none"}
ASSET_REWARD_TYPES = {"material", "mesh", "geo_nodes"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
FROZEN_CATEGORY_COUNTS = {
    "EDITING": 45,
    "MATERIALS": 17,
    "RENDERING": 17,
    "TIME": 12,
    "GEO_NODES": 14,
}
FROZEN_LESSON_CATEGORY_COUNTS = {
    "EDITING": 5,
    "MATERIALS": 1,
    "TIME": 1,
    "GEO_NODES": 1,
    "RENDERING": 1,
}
FROZEN_DIFFICULTY_COUNTS = {"easy": 10, "medium": 40, "hard": 55}
FROZEN_DIFFICULTY_XP = {"easy": 5, "medium": 10, "hard": 20}
FROZEN_LEVEL_BANDS = (20, 40, 80, 120, 140, 170, 200, 230, 260, 290)
FROZEN_LEVEL_STARTS = (0, 20, 60, 140, 260, 400, 570, 770, 1000, 1260)
FROZEN_LEVEL_ENDS = (20, 60, 140, 260, 400, 570, 770, 1000, 1260, 1550)
FROZEN_LEVEL_CAP = 1550
FROZEN_LEVEL_TITLES = {
    1: "Новичок",
    2: "Начинающий",
    3: "Ньюблинг",
    4: "Ученик",
    5: "Умелец",
    6: "Мастеровой",
    7: "Эксперт",
    8: "Виртуоз",
    9: "Гуру",
    10: "Легенда",
}
LEGACY_LEVEL_STARTS = (0, 20, 60, 140, 300, 620, 1260, 2540, 5100, 10220)
FROZEN_REWARD_TYPE_COUNTS = {
    "none": 82,
    "tutorial": 2,
    "material": 11,
    "geo_nodes": 5,
    "mesh": 5,
}
FROZEN_REWARD_CATEGORY_COUNTS = {"MESHES": 38, "SHADERS": 49, "GEO_NODES": 18}
FROZEN_STAT_KEY_COUNTS = {
    "vertices_created": 7,
    "faces_created": 6,
    "edges_created": 3,
    "materials_applied": 5,
    "renders_completed": 6,
    "time_spent": 6,
    "vertices_deleted": 3,
    "meshes_1000plus": 4,
}
FROZEN_COMPLEX_STEP_TOTAL = 85
FROZEN_COMPLEX_STEP_RANGE = (1, 4)
FROZEN_CONSTANTS = {
    "GRID_COLS": 2,
    "GRID_ROWS": 5,
    "CARD_WIDTH_UNITS": 15.6,
    "CARD_ICON_UNITS": 5.0,
    "NOTIFY_DURATION": 8.0,
    "NOTIFY_SLIDE_IN": 0.4,
    "NOTIFY_ICON_SIZE": 100,
    "NOTIFY_PADDING": 16,
    "NOTIFY_TEXT_GAP": 8,
    "NOTIFY_HEIGHT": 132,
    "NOTIFY_WIDTH": 500,
    "NOTIFY_MARGIN": 20,
    "PIN_MARGIN_X": 20,
    "PIN_MARGIN_Y": 20,
    "_IDLE_TIMEOUT": 120,
    "_REWARD_MARKER_ID": "_achievements_reward_id",
    "_REWARD_MARKER_TYPE": "_achievements_reward_type",
    "_REWARD_MARKER_NAME": "_achievements_reward_name",
    "_UNIT": 20.0,
    "_CARD_W": 15.6,
    "_CARD_H": 5.0,
    "_ICON_U": 5.0,
    "_GAP": 0.8,
}
FROZEN_FUNCTIONS = {
    "_add_notification",
    "_base_scene_properties",
    "_calc_level",
    "_calc_xp",
    "_category_scene_properties",
    "_check_complex",
    "_check_complex_step",
    "_difficulty_label",
    "_draw_grid_page",
    "_draw_header_button",
    "_draw_notifications",
    "_draw_pinned_achievement",
    "_draw_rect",
    "_draw_unified_card",
    "_ensure_icons",
    "_ensure_data_dirs",
    "_extension_management_target",
    "_flush_session_time",
    "_get_icon_id",
    "_get_mesh_counts",
    "_handler_pairs",
    "_make_unlock_hash",
    "_notification_redraw_tick",
    "_on_user_activity",
    "_register_draw_handlers",
    "_register_handlers",
    "_register_scene_properties",
    "_register_timers",
    "_reward_type_label",
    "_scene_property_names",
    "_tab_prop",
    "_tag_redraw_all",
    "_timer_tick",
    "_unlock_achievement",
    "_unregister_draw_handlers",
    "_unregister_handlers",
    "_unregister_scene_properties",
    "_unregister_timers",
    "_verify_unlock",
    "check_achievements",
    "check_complex_achievements",
    "load_data",
    "on_depsgraph_update",
    "on_load_post",
    "on_render_complete",
    "on_save_pre",
    "register",
    "save_data",
    "unregister",
}
FROZEN_CLASSES = {
    "ACH_OT_AchievementsDialog",
    "ACH_OT_ApplyReward",
    "ACH_OT_OpenTutorial",
    "ACH_OT_OpenWindow",
    "ACH_OT_PageNext",
    "ACH_OT_PagePrev",
    "ACH_OT_PinAchievement",
    "ACH_OT_ResetAchievements",
    "ACH_OT_OpenExtensionManager",
    "Stats",
}
FROZEN_REGISTER_CLASSES = {
    "ACH_OT_AchievementsDialog",
    "ACH_OT_ApplyReward",
    "ACH_OT_OpenTutorial",
    "ACH_OT_OpenWindow",
    "ACH_OT_PageNext",
    "ACH_OT_PagePrev",
    "ACH_OT_PinAchievement",
    "ACH_OT_ResetAchievements",
    "ACH_OT_OpenExtensionManager",
}
ACHIEVEMENT_FIELDS = {
    "id",
    "title",
    "description",
    "goal",
    "stat_key",
    "category",
    "check_type",
    "difficulty",
    "reward_type",
    "reward_data",
    "reward_category",
    "lesson_id",
    "icon_gray",
    "icon_color",
}
COMPLEX_ACHIEVEMENT_FIELDS = ACHIEVEMENT_FIELDS | {"complex_id", "steps"}
LESSON_FIELDS = {"id", "title", "description", "category", "url", "icon"}
STEP_FIELDS = {"label", "check"}


checks: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    checks.append((name, passed, detail))
    tag = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{tag}] {name}{suffix}")


def literal_assignment(module: ast.Module, name: str) -> Any:
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if any(isinstance(target, ast.Name) and target.id == name for target in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)


def eval_constant(node: ast.AST, env: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return env[node.id]
    if isinstance(node, ast.BinOp):
        left = eval_constant(node.left, env)
        right = eval_constant(node.right, env)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        if isinstance(node.op, ast.Div):
            return left / right
    raise ValueError(f"Unsupported constant expression: {ast.dump(node)}")


def constant_assignments(module: ast.Module, names: set[str]) -> dict[str, Any]:
    env: dict[str, Any] = {}
    found: dict[str, Any] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            try:
                env[target.id] = eval_constant(node.value, env)
            except Exception:  # noqa: BLE001 - ignore non-constant assignments.
                continue
            if target.id in names:
                found[target.id] = env[target.id]
    missing = names - set(found)
    if missing:
        raise KeyError(", ".join(sorted(missing)))
    return found


def addon_tree() -> ast.Module:
    return ast.parse(ADDON.read_text(encoding="utf-8"))


def runtime_python_files() -> tuple[Path, ...]:
    """Return every Python file that ships in the extension payload."""
    package_files = tuple(sorted((ROOT / "achievements").rglob("*.py")))
    return (ADDON, *package_files)


def runtime_import_policy_errors() -> list[str]:
    """Find imports/path access that would escape Blender's ``bl_ext`` namespace."""
    errors: list[str] = []
    for path in runtime_python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        relative_path = path.relative_to(ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "sys":
                        errors.append(
                            f"{relative_path}:{node.lineno}: shipped runtime imports sys"
                        )
                    if alias.name == "achievements" or alias.name.startswith("achievements."):
                        errors.append(
                            f"{relative_path}:{node.lineno}: absolute import {alias.name}"
                        )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if node.level == 0 and module_name == "sys":
                    errors.append(
                        f"{relative_path}:{node.lineno}: shipped runtime imports from sys"
                    )
                if node.level == 0 and (
                    module_name == "achievements"
                    or module_name.startswith("achievements.")
                ):
                    errors.append(
                        f"{relative_path}:{node.lineno}: absolute import {module_name}"
                    )
            elif isinstance(node, ast.Attribute):
                path_name = attribute_path(node)
                if path_name is not None and (
                    path_name == "sys.path" or path_name.startswith("sys.path.")
                ):
                    errors.append(
                        f"{relative_path}:{node.lineno}: shipped runtime accesses {path_name}"
                    )
    return sorted(set(errors))


def attribute_path(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = attribute_path(node.value)
        if parent:
            return f"{parent}.{node.attr}"
    return None


def top_level_assignment_paths(module: ast.Module, name: str) -> list[str | None]:
    """Return attribute paths assigned to one exact top-level runtime name."""
    return [
        attribute_path(node.value)
        for node in module.body
        if isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Name) and target.id == name
            for target in node.targets
        )
    ]


def call_paths_in(node: ast.AST | None) -> set[str]:
    if node is None:
        return set()
    return {
        path
        for child in ast.walk(node)
        if isinstance(child, ast.Call)
        if (path := attribute_path(child.func)) is not None
    }


def top_level_function(module: ast.Module, name: str) -> ast.FunctionDef | None:
    return next(
        (
            node
            for node in module.body
            if isinstance(node, ast.FunctionDef) and node.name == name
        ),
        None,
    )


def class_method(
    module: ast.Module, class_name: str, method_name: str
) -> ast.FunctionDef | None:
    class_node = next(
        (
            node
            for node in module.body
            if isinstance(node, ast.ClassDef) and node.name == class_name
        ),
        None,
    )
    if class_node is None:
        return None
    return next(
        (
            node
            for node in class_node.body
            if isinstance(node, ast.FunctionDef) and node.name == method_name
        ),
        None,
    )


def reward_atomicity_errors(
    addon_source: str,
    rewards_source: str,
    smoke_source: str,
) -> list[str]:
    """Validate the action -> prospective save -> runtime claim contract structurally."""
    errors: list[str] = []
    addon_module = ast.parse(addon_source)
    rewards_module = ast.parse(rewards_source)
    smoke_module = ast.parse(smoke_source)

    reward_result = next(
        (
            node
            for node in rewards_module.body
            if isinstance(node, ast.ClassDef) and node.name == "RewardResult"
        ),
        None,
    )
    result_fields = (
        {
            node.target.id
            for node in reward_result.body
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name)
        }
        if reward_result is not None
        else set()
    )
    compatibility_alias = class_method(rewards_module, "RewardResult", "mark_claimed")
    alias_returns = (
        [node for node in compatibility_alias.body if isinstance(node, ast.Return)]
        if compatibility_alias is not None
        else []
    )
    alias_is_exact_property = (
        compatibility_alias is not None
        and len(compatibility_alias.decorator_list) == 1
        and attribute_path(compatibility_alias.decorator_list[0]) == "property"
        and len(alias_returns) == 1
        and isinstance(alias_returns[0].value, ast.Attribute)
        and isinstance(alias_returns[0].value.value, ast.Name)
        and alias_returns[0].value.value.id == "self"
        and alias_returns[0].value.attr == "claim_after_apply"
    )
    if (
        "claim_after_apply" not in result_fields
        or "mark_claimed" in result_fields
        or not alias_is_exact_property
    ):
        errors.append(
            "RewardResult must expose claim_after_apply with a mark_claimed property alias"
        )

    save_function = top_level_function(addon_module, "save_data")
    if save_function is None:
        errors.append("save_data is missing")
    else:
        kwonly_names = {argument.arg for argument in save_function.args.kwonlyargs}
        if "reward_claim" not in kwonly_names:
            errors.append("save_data must accept keyword-only reward_claim")
        calls = [
            (node.lineno, attribute_path(node.func), node)
            for node in ast.walk(save_function)
            if isinstance(node, ast.Call)
        ]
        payload_calls = [item for item in calls if item[1] == "ach_persistence.payload_from_stats"]
        write_calls = [item for item in calls if item[1] == "ach_persistence.atomic_write_json"]
        runtime_claim_calls = [item for item in calls if item[1] == "stats.rewards_claimed.add"]
        if len(payload_calls) != 1 or not any(
            keyword.arg == "reward_claim"
            and isinstance(keyword.value, ast.Name)
            and keyword.value.id == "reward_claim"
            for keyword in payload_calls[0][2].keywords
        ):
            errors.append("save_data must build one prospective reward_claim payload")
        if (
            len(payload_calls) != 1
            or len(write_calls) != 1
            or len(runtime_claim_calls) != 1
            or not (
                payload_calls[0][0] < write_calls[0][0] < runtime_claim_calls[0][0]
            )
        ):
            errors.append("save_data order must be payload -> atomic write -> runtime claim")
        boolean_returns = {
            node.value.value
            for node in ast.walk(save_function)
            if isinstance(node, ast.Return)
            and isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, bool)
        }
        if boolean_returns != {False, True}:
            errors.append("save_data must report exact False/True outcomes")

    execute = class_method(addon_module, "ACH_OT_ApplyReward", "execute")
    apply_action = class_method(addon_module, "ACH_OT_ApplyReward", "_apply_action")
    if execute is None or apply_action is None:
        errors.append("reward operator execute/apply adapter is missing")
    else:
        execute_calls = [
            (node.lineno, attribute_path(node.func), node)
            for node in ast.walk(execute)
            if isinstance(node, ast.Call)
        ]
        apply_calls = [item for item in execute_calls if item[1] == "self._apply_action"]
        save_calls = [item for item in execute_calls if item[1] == "save_data"]
        direct_claims = [item for item in execute_calls if item[1] == "stats.rewards_claimed.add"]
        if (
            len(apply_calls) != 1
            or len(save_calls) != 1
            or apply_calls[0][0] >= save_calls[0][0]
            or direct_claims
        ):
            errors.append("operator must confirm apply before save and never mutate claim directly")

        no_op_guard = any(
            isinstance(node, ast.If)
            and isinstance(node.test, ast.UnaryOp)
            and isinstance(node.test.op, ast.Not)
            and isinstance(node.test.operand, ast.Name)
            and node.test.operand.id == "applied"
            and any(
                isinstance(child, ast.Return)
                and isinstance(child.value, ast.Set)
                and any(
                    isinstance(item, ast.Constant) and item.value == "CANCELLED"
                    for item in child.value.elts
                )
                for child in node.body
            )
            for node in ast.walk(execute)
        )
        if not no_op_guard:
            errors.append("operator must cancel an unconfirmed action before persistence")

        prospective_guard = any(
            isinstance(node, ast.If)
            and any(
                isinstance(child, ast.Call)
                and attribute_path(child.func) == "save_data"
                and any(keyword.arg == "reward_claim" for keyword in child.keywords)
                and any(
                    isinstance(parent, ast.UnaryOp)
                    and isinstance(parent.op, ast.Not)
                    and parent.operand is child
                    for parent in ast.walk(node.test)
                )
                for child in ast.walk(node.test)
            )
            and {"already_claimed"}.issubset(
                {child.id for child in ast.walk(node.test) if isinstance(child, ast.Name)}
            )
            and {"claim_after_apply"}.issubset(
                {child.attr for child in ast.walk(node.test) if isinstance(child, ast.Attribute)}
            )
            for node in ast.walk(execute)
        )
        if not prospective_guard:
            errors.append("operator must gate prospective claim save after apply")

        action_kinds = {
            node.value
            for node in ast.walk(apply_action)
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        }
        required_actions = {
            "link_asset",
            "placeholder_material",
            "placeholder_mesh",
            "placeholder_geo_nodes",
        }
        final_return = apply_action.body[-1] if apply_action.body else None
        if not required_actions.issubset(action_kinds) or not (
            isinstance(final_return, ast.Return)
            and isinstance(final_return.value, ast.Constant)
            and final_return.value.value is False
        ):
            errors.append("reward action dispatch must cover all asset kinds and fail closed")

    snapshot_method = class_method(addon_module, "ACH_OT_ApplyReward", "_data_id_snapshot")
    cleanup_method = class_method(addon_module, "ACH_OT_ApplyReward", "_remove_new_data_ids")
    snapshot_calls = (
        {
            attribute_path(node.func)
            for node in ast.walk(snapshot_method)
            if isinstance(node, ast.Call)
        }
        if snapshot_method is not None
        else set()
    )
    cleanup_calls = (
        {
            attribute_path(node.func)
            for node in ast.walk(cleanup_method)
            if isinstance(node, ast.Call)
        }
        if cleanup_method is not None
        else set()
    )
    if "bpy.data.user_map" not in snapshot_calls or not {
        "bpy.data.user_map",
        "bpy.data.batch_remove",
    }.issubset(cleanup_calls):
        errors.append("reward rollback must remove the complete new Blender ID delta")

    capture_material = class_method(
        addon_module, "ACH_OT_ApplyReward", "_capture_material_state"
    )
    restore_material = class_method(
        addon_module, "ACH_OT_ApplyReward", "_restore_material_state"
    )
    captures_active_material_index = capture_material is not None and any(
        isinstance(node, ast.Attribute) and node.attr == "active_material_index"
        for node in ast.walk(capture_material)
    )
    restores_active_material_index = restore_material is not None and any(
        isinstance(node, ast.Assign)
        and any(
            isinstance(target, ast.Attribute)
            and target.attr == "active_material_index"
            for target in node.targets
        )
        for node in ast.walk(restore_material)
    )
    smoke_active_material_indices = sum(
        1
        for node in ast.walk(smoke_module)
        if isinstance(node, ast.Attribute) and node.attr == "active_material_index"
    )
    if (
        not captures_active_material_index
        or not restores_active_material_index
        or smoke_active_material_indices < 3
    ):
        errors.append("material rollback must restore and smoke active material indices")

    retry_calls = sum(
        1
        for node in ast.walk(smoke_module)
        if isinstance(node, ast.Call) and attribute_path(node.func) == "exercise_save_failure_retry"
    )
    required_smoke_markers = {
        "forced reward claim write failure",
        "wrong-type mesh library left a loaded object behind",
        "wrong-type geo library left a loaded node group behind",
        "runtime reward claims are not exact",
        "incompatible linked geo denial changed Blender IDs",
        "incompatible fallback geo denial changed Blender IDs",
        "compatible curve geo reward was not applied",
        "failed material application left new Blender IDs",
        "failed material application did not restore linked material slots",
        "failed mesh application left new Blender IDs",
        "failed geo application left new Blender IDs",
        "linked/fallback action proof, no-op denial, prospective claims, and idempotent save retry clean",
    }
    smoke_literals = "\n".join(
        node.value
        for node in ast.walk(smoke_module)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )
    if retry_calls < 6 or not all(marker in smoke_literals for marker in required_smoke_markers):
        errors.append("reward smoke must cover six linked/fallback retries and exact failure invariants")
    return errors


def assignment_dict(module: ast.Module) -> dict[str, Any]:
    names = ["bl_info"]
    values = {name: literal_assignment(module, name) for name in names}
    values.update(
        {
            "ACHIEVEMENTS_DEF": catalog.ACHIEVEMENTS_DEF,
            "LESSONS_DEF": catalog.LESSONS_DEF,
            "ACH_CATEGORIES": catalog.ACH_CATEGORIES,
            "LESSON_CATEGORIES": catalog.LESSON_CATEGORIES,
            "REWARD_CATEGORIES": catalog.REWARD_CATEGORIES,
            "DIFFICULTY_XP": levels.DIFFICULTY_XP,
            "XP_LEVELS": levels.XP_LEVELS,
            "LEVEL_TITLES": levels.LEVEL_TITLES,
        }
    )
    values.update(constant_assignments(module, set(FROZEN_CONSTANTS)))
    return values


def level_root_aliases(module: ast.Module) -> dict[str, str]:
    expected_names = {"DIFFICULTY_XP", "XP_LEVELS", "LEVEL_TITLES"}
    aliases: dict[str, str] = {}
    for node in module.body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Attribute):
            continue
        if not isinstance(node.value.value, ast.Name) or node.value.value.id != "ach_levels":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in expected_names:
                aliases[target.id] = node.value.attr
    return aliases


def reachable_xp_totals(
    achievements: list[dict[str, Any]], difficulty_xp: dict[str, int]
) -> set[int]:
    reachable = {0}
    for achievement in achievements:
        award = difficulty_xp[achievement["difficulty"]]
        reachable |= {xp + award for xp in tuple(reachable)}
    return reachable


def level_from_starts(xp: int, starts: tuple[int, ...]) -> int:
    return max(level for level, start in enumerate(starts, start=1) if xp >= start)


def imports_catalog_definitions(module: ast.Module) -> bool:
    required = {
        "ACHIEVEMENTS_DEF",
        "LESSONS_DEF",
        "ACH_CATEGORIES",
        "LESSON_CATEGORIES",
        "REWARD_CATEGORIES",
    }
    imported: set[str] = set()
    for node in module.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module == "achievements.catalog"
        ):
            imported.update(alias.name for alias in node.names)
    return required <= imported


def registered_classes(module: ast.Module) -> set[str]:
    for node in module.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == "_classes" for target in node.targets):
            continue
        if not isinstance(node.value, ast.Tuple):
            return set()
        return {item.id for item in node.value.elts if isinstance(item, ast.Name)}
    return set()


def git_files() -> tuple[bool, list[str], str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        return False, [], result.stdout.strip() or f"git ls-files returned {result.returncode}"
    return True, result.stdout.splitlines(), ""


def verify_addon_contract() -> None:
    module = addon_tree()
    values = assignment_dict(module)
    achievements: list[dict[str, Any]] = values["ACHIEVEMENTS_DEF"]
    lessons: list[dict[str, Any]] = values["LESSONS_DEF"]
    ach_categories = {key for key, _label in values["ACH_CATEGORIES"]}
    lesson_categories = {key for key, _label in values["LESSON_CATEGORIES"]}
    reward_categories = {key for key, _label in values["REWARD_CATEGORIES"]}
    stat_keys = {
        "vertices_created",
        "vertices_deleted",
        "edges_created",
        "faces_created",
        "meshes_1000plus",
        "materials_applied",
        "time_spent",
        "renders_completed",
        "_complex",
    }

    record("addon parses as AST without importing bpy", isinstance(module, ast.Module))
    record("addon imports catalog definitions", imports_catalog_definitions(module))
    catalog_errors = catalog.validate_catalog()
    record("catalog module validates", not catalog_errors, ", ".join(catalog_errors[:10]))
    record(
        "catalog digest frozen",
        catalog.catalog_digest() == catalog.FROZEN_CATALOG_DIGEST,
        catalog.catalog_digest(),
    )
    record("bl_info exists", values["bl_info"].get("name") == "Achievements")
    record("bl_info version is 0.2.2", values["bl_info"].get("version") == (0, 2, 2))
    record("bl_info Blender floor is 5.0", values["bl_info"].get("blender") == (5, 0, 0))
    record(
        "bl_info advertises 105 achievements",
        "105 achievements" in values["bl_info"].get("description", ""),
    )
    record(
        "runtime does not read loader-consumed bl_info",
        not any(
            isinstance(node, ast.Name)
            and node.id == "bl_info"
            and isinstance(node.ctx, ast.Load)
            for node in ast.walk(module)
        ),
    )
    policy_errors = runtime_import_policy_errors()
    record(
        "shipped runtime stays inside Blender extension import policy",
        not policy_errors,
        "; ".join(policy_errors[:10]),
    )
    record("achievement count is 105", len(achievements) == 105, str(len(achievements)))
    record("lesson count is 9", len(lessons) == 9, str(len(lessons)))
    record(
        "root level compatibility aliases frozen",
        level_root_aliases(module)
        == {
            "DIFFICULTY_XP": "DIFFICULTY_XP",
            "XP_LEVELS": "XP_LEVELS",
            "LEVEL_TITLES": "LEVEL_TITLES",
        },
    )
    record(
        "difficulty XP awards frozen",
        values["DIFFICULTY_XP"] == FROZEN_DIFFICULTY_XP,
        str(values["DIFFICULTY_XP"]),
    )
    level_entries = values["XP_LEVELS"]
    level_starts = tuple(entry.get("xp_start") for entry in level_entries)
    level_ends = tuple(entry.get("xp_end") for entry in level_entries)
    level_bands = tuple(
        end - start for start, end in zip(level_starts, level_ends, strict=True)
    )
    record(
        "XP level table shape frozen",
        len(level_entries) == 10
        and all(
            set(entry) == {"level", "xp_start", "xp_end"}
            and entry["level"] == level
            for level, entry in enumerate(level_entries, start=1)
        ),
    )
    record(
        "XP level bands frozen",
        level_bands == FROZEN_LEVEL_BANDS,
        str(level_bands),
    )
    record(
        "XP level starts and ends frozen",
        level_starts == FROZEN_LEVEL_STARTS and level_ends == FROZEN_LEVEL_ENDS,
        f"starts={level_starts}, ends={level_ends}",
    )
    record(
        "level titles frozen",
        values["LEVEL_TITLES"] == FROZEN_LEVEL_TITLES,
    )
    frozen_constants = {key: values[key] for key in FROZEN_CONSTANTS}
    record(
        "UI/runtime constants frozen",
        frozen_constants == FROZEN_CONSTANTS,
        ", ".join(f"{key}={value}" for key, value in sorted(frozen_constants.items())),
    )
    activity_clock_paths = top_level_assignment_paths(module, "_activity_clock")
    record(
        "active-time clock uses time.monotonic",
        activity_clock_paths == ["time.monotonic"],
        ", ".join(path or "<non-attribute>" for path in activity_clock_paths),
    )
    functions = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
    classes = {node.name for node in module.body if isinstance(node, ast.ClassDef)}
    record("top-level function map frozen", functions == FROZEN_FUNCTIONS)
    record("top-level class map frozen", classes == FROZEN_CLASSES)
    record("registered operator classes frozen", registered_classes(module) == FROZEN_REGISTER_CLASSES)
    call_paths = {
        path
        for node in ast.walk(module)
        if isinstance(node, ast.Call)
        if (path := attribute_path(node.func)) is not None
    }
    record(
        "root delegates XP aggregation to pure helper",
        "ach_levels.calculate_xp" in call_paths_in(top_level_function(module, "_calc_xp")),
    )
    record(
        "root delegates XP level calculation to pure helper",
        "ach_levels.calculate_level"
        in call_paths_in(top_level_function(module, "_calc_level")),
    )
    record(
        "dialog uses cap-aware XP progress formatter",
        "ach_levels.format_level_progress"
        in call_paths_in(class_method(module, "ACH_OT_AchievementsDialog", "draw")),
    )
    record(
        "runtime opens native extension management without self-uninstall",
        "bpy.ops.screen.userpref_show" in call_paths
        and not any(
            path.startswith("bpy.ops.extensions.package_uninstall")
            for path in call_paths
        )
        and "bpy.ops.preferences.addon_remove" not in call_paths,
    )
    atomicity_errors = reward_atomicity_errors(
        ADDON.read_text(encoding="utf-8"),
        (ROOT / "achievements" / "rewards.py").read_text(encoding="utf-8"),
        (ROOT / "tests" / "blender" / "smoke_rewards.py").read_text(encoding="utf-8"),
    )
    record(
        "reward action, prospective claim, and retry contract frozen",
        not atomicity_errors,
        "; ".join(atomicity_errors),
    )

    achievement_ids = [item.get("id") for item in achievements]
    lesson_ids = [item.get("id") for item in lessons]
    complex_ids_all = [
        item.get("complex_id") for item in achievements if item.get("check_type") == "complex"
    ]
    complex_ids = [complex_id for complex_id in complex_ids_all if isinstance(complex_id, str)]

    record("achievement ids unique", len(achievement_ids) == len(set(achievement_ids)))
    record("lesson ids unique", len(lesson_ids) == len(set(lesson_ids)))
    record("complex ids unique", len(complex_ids_all) == len(set(complex_ids_all)))

    invalid: list[str] = []
    lesson_id_set = set(lesson_ids)
    for item in achievements:
        aid = item.get("id", "<missing>")
        expected_fields = (
            COMPLEX_ACHIEVEMENT_FIELDS
            if item.get("check_type") == "complex"
            else ACHIEVEMENT_FIELDS
        )
        missing = expected_fields - set(item)
        extra = set(item) - expected_fields
        if missing:
            invalid.append(f"{aid}: missing {sorted(missing)[0]}")
        if extra:
            invalid.append(f"{aid}: extra {sorted(extra)[0]}")
        if not isinstance(item.get("id"), str) or not ID_PATTERN.match(item["id"]):
            invalid.append(f"{aid}: id")
        for text_key in ["title", "description", "icon_gray", "icon_color"]:
            if not isinstance(item.get(text_key), str) or not item[text_key]:
                invalid.append(f"{aid}: {text_key}")
        if not isinstance(item.get("goal"), int) or item["goal"] <= 0:
            invalid.append(f"{aid}: goal")
        if item.get("category") not in ach_categories:
            invalid.append(f"{aid}: category")
        if item.get("check_type") not in VALID_CHECK_TYPES:
            invalid.append(f"{aid}: check_type")
        if item.get("difficulty") not in VALID_DIFFICULTIES:
            invalid.append(f"{aid}: difficulty")
        if item.get("reward_type") not in VALID_REWARD_TYPES:
            invalid.append(f"{aid}: reward_type")
        if item.get("reward_category") not in reward_categories:
            invalid.append(f"{aid}: reward_category")
        if item.get("stat_key") not in stat_keys:
            invalid.append(f"{aid}: stat_key")
        lesson_id = item.get("lesson_id")
        if lesson_id is not None and lesson_id not in lesson_id_set:
            invalid.append(f"{aid}: lesson_id")
        reward_type = item.get("reward_type")
        reward_data = item.get("reward_data")
        if reward_type == "tutorial" and not isinstance(reward_data, dict):
            invalid.append(f"{aid}: tutorial reward_data")
        elif reward_type == "tutorial" and not reward_data.get("url"):
            invalid.append(f"{aid}: tutorial url")
        if reward_type in ASSET_REWARD_TYPES:
            for key in ["name", "description", "blend_file"]:
                if not isinstance(reward_data, dict) or not reward_data.get(key):
                    invalid.append(f"{aid}: reward {key}")
        if reward_type == "none" and reward_data != {}:
            invalid.append(f"{aid}: none reward_data")
        if item.get("check_type") == "complex":
            if item.get("stat_key") != "_complex":
                invalid.append(f"{aid}: complex stat_key")
            complex_id = item.get("complex_id")
            if not isinstance(complex_id, str) or not complex_id:
                invalid.append(f"{aid}: complex_id")
            steps = item.get("steps")
            if not isinstance(steps, list) or not steps:
                invalid.append(f"{aid}: steps")
            else:
                for step in steps:
                    if not isinstance(step, dict) or not step.get("label") or not step.get("check"):
                        invalid.append(f"{aid}: step")
                    elif set(step) != STEP_FIELDS:
                        invalid.append(f"{aid}: step fields")
        elif "complex_id" in item or "steps" in item:
            invalid.append(f"{aid}: stat complex fields")
    for item in lessons:
        lid = item.get("id", "<missing>")
        missing = LESSON_FIELDS - set(item)
        extra = set(item) - LESSON_FIELDS
        if missing:
            invalid.append(f"{lid}: missing {sorted(missing)[0]}")
        if extra:
            invalid.append(f"{lid}: extra {sorted(extra)[0]}")
        if not isinstance(item.get("id"), str) or not ID_PATTERN.match(item["id"]):
            invalid.append(f"{lid}: lesson id")
        if item.get("category") not in lesson_categories:
            invalid.append(f"{lid}: lesson category")
        for text_key in ["title", "description", "url", "icon"]:
            if not isinstance(item.get(text_key), str) or not item[text_key]:
                invalid.append(f"{lid}: {text_key}")
    record("achievement and lesson enums valid", not invalid, ", ".join(invalid[:10]))

    predicate_errors = predicates.registry_bijection_errors(achievements)
    registered_complex_ids = {
        complex_id for complex_id, _step_check in predicates.PREDICATE_PAIRS
    }
    record(
        "complex ids covered",
        registered_complex_ids == set(complex_ids),
        ", ".join(sorted(set(complex_ids) ^ registered_complex_ids)[:10]),
    )
    record(
        "complex step checks covered by exact registry bijection",
        not predicate_errors,
        "; ".join(predicate_errors[:5]),
    )

    counts = Counter(item.get("check_type") for item in achievements)
    record(
        "stat/complex split frozen",
        counts == {"stat": 40, "complex": 65},
        ", ".join(f"{key}={value}" for key, value in sorted(counts.items())),
    )
    category_counts = Counter(item.get("category") for item in achievements)
    record(
        "achievement category counts frozen",
        category_counts == FROZEN_CATEGORY_COUNTS,
        ", ".join(f"{key}={value}" for key, value in sorted(category_counts.items())),
    )
    lesson_category_counts = Counter(item.get("category") for item in lessons)
    record(
        "lesson category counts frozen",
        lesson_category_counts == FROZEN_LESSON_CATEGORY_COUNTS,
        ", ".join(f"{key}={value}" for key, value in sorted(lesson_category_counts.items())),
    )
    difficulty_counts = Counter(item.get("difficulty") for item in achievements)
    record(
        "difficulty counts frozen",
        difficulty_counts == FROZEN_DIFFICULTY_COUNTS,
        ", ".join(f"{key}={value}" for key, value in sorted(difficulty_counts.items())),
    )
    all_achievement_ids = {item["id"] for item in achievements}
    catalog_max_xp = levels.calculate_xp(achievements, all_achievement_ids)
    summed_catalog_xp = sum(
        values["DIFFICULTY_XP"][item["difficulty"]] for item in achievements
    )
    record(
        "catalog maximum XP equals level cap",
        catalog_max_xp == summed_catalog_xp == FROZEN_LEVEL_CAP
        and levels.MAX_XP == FROZEN_LEVEL_CAP
        and level_ends[-1] == FROZEN_LEVEL_CAP,
        (
            f"catalog={catalog_max_xp}, summed={summed_catalog_xp}, "
            f"helper={levels.MAX_XP}, table={level_ends[-1]}"
        ),
    )
    reachable_xp = reachable_xp_totals(achievements, values["DIFFICULTY_XP"])
    record(
        "catalog XP state space is fully reachable",
        reachable_xp == set(range(0, FROZEN_LEVEL_CAP + 1, 5)),
        f"states={len(reachable_xp)}",
    )
    record(
        "all ten level starts are reachable",
        set(FROZEN_LEVEL_STARTS) <= reachable_xp,
    )
    level_deltas = [
        levels.calculate_level(xp)[0] - level_from_starts(xp, LEGACY_LEVEL_STARTS)
        for xp in sorted(reachable_xp)
    ]
    record(
        "level rebalance never lowers existing reachable progress",
        min(level_deltas) >= 0 and max(level_deltas) <= 3,
        f"delta={min(level_deltas)}..{max(level_deltas)}",
    )
    pre_cap = levels.calculate_level(FROZEN_LEVEL_CAP - 1)
    at_cap = levels.calculate_level(FROZEN_LEVEL_CAP)
    record(
        "level ten progresses until exact MAX cap",
        pre_cap[0] == 10
        and pre_cap[2:] == (290, 289)
        and at_cap == (10, 1.0, 0, 0)
        and max(reachable_xp - {FROZEN_LEVEL_CAP}) == FROZEN_LEVEL_CAP - 5,
        f"pre_cap={pre_cap}, at_cap={at_cap}",
    )
    reward_type_counts = Counter(item.get("reward_type") for item in achievements)
    record(
        "reward type counts frozen",
        reward_type_counts == FROZEN_REWARD_TYPE_COUNTS,
        ", ".join(f"{key}={value}" for key, value in sorted(reward_type_counts.items())),
    )
    reward_category_counts = Counter(item.get("reward_category") for item in achievements)
    record(
        "reward category counts frozen",
        reward_category_counts == FROZEN_REWARD_CATEGORY_COUNTS,
        ", ".join(f"{key}={value}" for key, value in sorted(reward_category_counts.items())),
    )
    stat_key_counts = Counter(
        item.get("stat_key") for item in achievements if item.get("check_type") == "stat"
    )
    record(
        "stat key counts frozen",
        stat_key_counts == FROZEN_STAT_KEY_COUNTS,
        ", ".join(f"{key}={value}" for key, value in sorted(stat_key_counts.items())),
    )
    step_counts = [
        len(item.get("steps", [])) for item in achievements if item.get("check_type") == "complex"
    ]
    record("complex step total frozen", sum(step_counts) == FROZEN_COMPLEX_STEP_TOTAL)
    record(
        "complex step range frozen",
        (min(step_counts), max(step_counts)) == FROZEN_COMPLEX_STEP_RANGE,
        f"{min(step_counts)}..{max(step_counts)}",
    )


def verify_repo_contract() -> None:
    record("legacy duplicate addon is retired", not DUPLICATE_ADDON.exists())
    record("historical 100-achievement list is archived", ARCHIVED_100_LIST.is_file())
    if ARCHIVED_100_LIST.is_file():
        result = subprocess.run(
            [
                "git",
                "hash-object",
                "--path=docs/archive/achievements_100_list.md",
                str(ARCHIVED_100_LIST),
            ],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        record(
            "archived 100-achievement list preserves baseline Git blob",
            result.returncode == 0
            and result.stdout.strip() == "daf6a8c858551fcffe4e6e7c8354f4420966cbc0",
            result.stdout.strip(),
        )
    record("duplicate retirement ADR exists", DUPLICATE_RETIREMENT_ADR.is_file())
    if DUPLICATE_RETIREMENT_ADR.is_file():
        retirement_text = DUPLICATE_RETIREMENT_ADR.read_text(encoding="utf-8")
        required_evidence = (
            "04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3",
            "21d5023697370800ced934959463da1e4be7cd5f",
            "9CB06CA4B4CECF48B2CA52E59F5F930B45FC537F5A945D262EBC086551090681",
            "62DDB0163B29C8C4A39347DEAF19D201F71C50A3D0F9A48F803387444DB24DAE",
            "git restore --source=04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3",
        )
        record(
            "duplicate retirement ADR preserves exact recovery evidence",
            all(marker in retirement_text for marker in required_evidence),
        )

    tracked_ok, tracked, tracked_error = git_files()
    record("git tracked files available", tracked_ok, tracked_error)
    data_files = [
        path
        for path in tracked
        if any(marker.lower() in path.lower() for marker in USER_DATA_MARKERS)
    ]
    record(
        "user BlenderAchievements data not tracked",
        tracked_ok and not data_files,
        ", ".join(data_files) if tracked_ok else "git ls-files failed",
    )

    pyproject = ROOT / "pyproject.toml"
    record("pyproject exists for uv tooling", pyproject.is_file())
    if pyproject.is_file():
        text = pyproject.read_text(encoding="utf-8")
        record("pytest avoids importing addon package", "--confcutdir=tests" in text)

    contract = ROOT / "docs" / "agent" / "frozen-application-contract.md"
    record("frozen application contract exists", contract.is_file())
    if contract.is_file():
        text = contract.read_text(encoding="utf-8")
        required_markers = [
            "105 total",
            "9 total",
            "UI Design Freeze",
            "Function Map",
            "Runtime Lifecycle",
            "schema_version",
            "same-directory atomic JSON writes",
            "Corrupt JSON is quarantined",
            "Future Change Rule",
            "ACH_OT_ApplyReward",
            "_check_complex_step",
            "Steam-style bottom-left GPU overlay",
            "ADR 0005",
            "non-refreshing 120-second activity window",
            "open-day/session tracker",
            "`achievements/levels.py`",
            "`20, 40, 80, 120, 140, 170, 200, 230, 260, 290`",
            "`MAX` appears only at `1550`",
            "ADR 0007",
            "prospective reward claim",
            "_achievements_reward_id",
        ]
        missing = [marker for marker in required_markers if marker not in text]
        record("frozen application contract covers design and functions", not missing, ", ".join(missing))


def main() -> int:
    verify_addon_contract()
    verify_repo_contract()
    passed = sum(1 for _name, ok, _detail in checks if ok)
    failed = len(checks) - passed
    print(f"\nSUMMARY: {passed}/{len(checks)} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
