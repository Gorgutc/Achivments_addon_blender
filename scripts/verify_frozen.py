from __future__ import annotations

import ast
import hashlib
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ADDON = ROOT / "__init__.py"
DUPLICATE_ADDON = ROOT / "achievements_v01 (4).py"
sys.path.insert(0, str(ROOT))

from achievements import catalog  # noqa: E402

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
    "_check_streak",
    "_difficulty_label",
    "_draw_grid_page",
    "_draw_header_button",
    "_draw_notifications",
    "_draw_pinned_achievement",
    "_draw_rect",
    "_draw_unified_card",
    "_ease_out_cubic",
    "_ensure_icons",
    "_ensure_data_dirs",
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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def addon_tree() -> ast.Module:
    return ast.parse(ADDON.read_text(encoding="utf-8"))


def assignment_dict(module: ast.Module) -> dict[str, Any]:
    names = [
        "bl_info",
        "DIFFICULTY_XP",
        "LEVEL_TITLES",
    ]
    values = {name: literal_assignment(module, name) for name in names}
    values.update(
        {
            "ACHIEVEMENTS_DEF": catalog.ACHIEVEMENTS_DEF,
            "LESSONS_DEF": catalog.LESSONS_DEF,
            "ACH_CATEGORIES": catalog.ACH_CATEGORIES,
            "LESSON_CATEGORIES": catalog.LESSON_CATEGORIES,
            "REWARD_CATEGORIES": catalog.REWARD_CATEGORIES,
        }
    )
    values.update(constant_assignments(module, set(FROZEN_CONSTANTS)))
    return values


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
        if isinstance(node, ast.ImportFrom) and node.module == "achievements.catalog":
            imported.update(alias.name for alias in node.names)
    return required <= imported


def function_source(name: str) -> str:
    text = ADDON.read_text(encoding="utf-8")
    module = ast.parse(text)
    lines = text.splitlines()
    for node in module.body:
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return "\n".join(lines[node.lineno - 1 : node.end_lineno])
    raise KeyError(name)


def compare_name_to_string(test: ast.AST, name: str) -> str | None:
    if not isinstance(test, ast.Compare) or len(test.ops) != 1 or not isinstance(test.ops[0], ast.Eq):
        return None

    left = test.left
    right = test.comparators[0]
    if isinstance(left, ast.Name) and left.id == name and isinstance(right, ast.Constant):
        return right.value if isinstance(right.value, str) else None
    if isinstance(right, ast.Name) and right.id == name and isinstance(left, ast.Constant):
        return left.value if isinstance(left.value, str) else None
    return None


def complex_step_coverage() -> dict[str, set[str]]:
    source = function_source("_check_complex_step")
    module = ast.parse(source)
    function = next(node for node in module.body if isinstance(node, ast.FunctionDef))
    coverage: dict[str, set[str]] = {}
    for node in ast.walk(function):
        if not isinstance(node, ast.If):
            continue
        complex_id = compare_name_to_string(node.test, "complex_id")
        if complex_id is None:
            continue
        steps: set[str] = set()
        for child in ast.walk(ast.Module(body=node.body, type_ignores=[])):
            if isinstance(child, ast.If):
                step = compare_name_to_string(child.test, "step_check")
                if step is not None:
                    steps.add(step)
        coverage[complex_id] = steps
    return coverage


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
    record("bl_info current known drift preserved", values["bl_info"].get("blender") == (4, 5, 0))
    record("achievement count is 105", len(achievements) == 105, str(len(achievements)))
    record("lesson count is 9", len(lessons) == 9, str(len(lessons)))
    frozen_constants = {key: values[key] for key in FROZEN_CONSTANTS}
    record(
        "UI/runtime constants frozen",
        frozen_constants == FROZEN_CONSTANTS,
        ", ".join(f"{key}={value}" for key, value in sorted(frozen_constants.items())),
    )
    functions = {node.name for node in module.body if isinstance(node, ast.FunctionDef)}
    classes = {node.name for node in module.body if isinstance(node, ast.ClassDef)}
    record("top-level function map frozen", functions == FROZEN_FUNCTIONS)
    record("top-level class map frozen", classes == FROZEN_CLASSES)
    record("registered operator classes frozen", registered_classes(module) == FROZEN_REGISTER_CLASSES)

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

    source = function_source("_check_complex_step")
    uncovered = [
        complex_id
        for complex_id in complex_ids
        if not re.search(rf"complex_id\s*==\s*['\"]{re.escape(complex_id)}['\"]", source)
    ]
    record("complex ids covered", not uncovered, ", ".join(uncovered[:10]))

    branch_steps = complex_step_coverage()
    uncovered_steps = []
    for item in achievements:
        if item.get("check_type") != "complex":
            continue
        complex_id = item.get("complex_id")
        steps = item.get("steps")
        if not isinstance(complex_id, str) or not isinstance(steps, list):
            continue
        declared = {
            step["check"]
            for step in steps
            if isinstance(step, dict) and isinstance(step.get("check"), str)
        }
        missing_steps = declared - branch_steps.get(complex_id, set())
        if missing_steps:
            uncovered_steps.append(f"{complex_id}: {', '.join(sorted(missing_steps))}")
    record("complex step checks covered", not uncovered_steps, "; ".join(uncovered_steps[:5]))

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
    record("duplicate addon file exists", DUPLICATE_ADDON.is_file())
    if DUPLICATE_ADDON.is_file():
        record("duplicate addon hash matches __init__.py", sha256(ADDON) == sha256(DUPLICATE_ADDON))

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
