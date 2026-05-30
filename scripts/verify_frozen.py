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
USER_DATA_MARKERS = {"achievements_data.json", "BlenderAchievements"}
VALID_CHECK_TYPES = {"stat", "complex"}
VALID_DIFFICULTIES = {"easy", "medium", "hard"}
VALID_REWARD_TYPES = {"tutorial", "material", "mesh", "geo_nodes", "none"}
ASSET_REWARD_TYPES = {"material", "mesh", "geo_nodes"}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
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
LESSON_FIELDS = {"id", "title", "description", "category", "url", "icon"}


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


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def addon_tree() -> ast.Module:
    return ast.parse(ADDON.read_text(encoding="utf-8"))


def assignment_dict(module: ast.Module) -> dict[str, Any]:
    names = [
        "bl_info",
        "ACHIEVEMENTS_DEF",
        "LESSONS_DEF",
        "ACH_CATEGORIES",
        "LESSON_CATEGORIES",
        "REWARD_CATEGORIES",
        "DIFFICULTY_XP",
        "LEVEL_TITLES",
    ]
    return {name: literal_assignment(module, name) for name in names}


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
    record("bl_info exists", values["bl_info"].get("name") == "Achievements")
    record("bl_info current known drift preserved", values["bl_info"].get("blender") == (4, 5, 0))
    record("achievement count is 105", len(achievements) == 105, str(len(achievements)))
    record("lesson count is 9", len(lessons) == 9, str(len(lessons)))

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
        missing = ACHIEVEMENT_FIELDS - set(item)
        if missing:
            invalid.append(f"{aid}: missing {sorted(missing)[0]}")
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
        elif "complex_id" in item or "steps" in item:
            invalid.append(f"{aid}: stat complex fields")
    for item in lessons:
        lid = item.get("id", "<missing>")
        missing = LESSON_FIELDS - set(item)
        if missing:
            invalid.append(f"{lid}: missing {sorted(missing)[0]}")
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


def main() -> int:
    verify_addon_contract()
    verify_repo_contract()
    passed = sum(1 for _name, ok, _detail in checks if ok)
    failed = len(checks) - passed
    print(f"\nSUMMARY: {passed}/{len(checks)} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
