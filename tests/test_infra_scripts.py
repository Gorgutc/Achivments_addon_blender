import ast
import json
import os
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG_DIGEST = "db0e8d4bd5d596c9b0e54dac158a5c4742c33071a023914ee8287b01eea71e67"


def run_script(*args, env=None):
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )


def assert_clean_verifier(result):
    assert result.returncode == 0, result.stdout
    assert re.search(r"SUMMARY: \d+/\d+ PASS, 0 FAIL", result.stdout), result.stdout


def fake_blender(tmp_path):
    if os.name == "nt":
        path = tmp_path / "fake_blender.cmd"
        path.write_text("@echo off\necho Blender 5.0.1\n", encoding="utf-8")
    else:
        path = tmp_path / "fake_blender"
        path.write_text("#!/bin/sh\necho 'Blender 5.0.1'\n", encoding="utf-8")
        path.chmod(0o755)
    return path


def test_smoke_runner_tolerates_windows_acl_cleanup_after_process_result():
    text = (ROOT / "scripts" / "run_blender_smoke.py").read_text(encoding="utf-8")

    assert "shutil.rmtree(temp_home, ignore_errors=True)" in text
    assert "[smoke-runner:WARN] temporary profile cleanup incomplete" in text


def test_smoke_runner_requires_exact_pass_marker_and_rejects_tracebacks():
    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import run_blender_smoke

    assert run_blender_smoke.smoke_result_code(
        "register", 0, "[smoke_register:PASS] clean"
    ) == 0
    assert run_blender_smoke.smoke_result_code("register", 2, "") == 2
    assert run_blender_smoke.smoke_result_code("register", 0, "Blender quit") == 1
    assert run_blender_smoke.smoke_result_code(
        "register",
        0,
        "Traceback (most recent call last):\n[smoke_register:PASS]",
    ) == 1
    assert run_blender_smoke.smoke_result_code(
        "register", 0, "[smoke_register:FAIL] bad"
    ) == 1


def top_level_assigned_names(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name):
                names.add(target.id)
    return names


def imported_names_from_catalog(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in tree.body:
        if (
            isinstance(node, ast.ImportFrom)
            and node.level == 1
            and node.module == "achievements.catalog"
        ):
            names.update(alias.name for alias in node.names)
    return names


def test_verify_frozen_passes_current_addon_contract():
    result = run_script("scripts/verify_frozen.py")
    assert_clean_verifier(result)
    assert "achievement ids unique" in result.stdout
    assert "complex ids covered" in result.stdout


def test_archived_catalog_blob_check_is_stable_for_windows_crlf(tmp_path):
    source = ROOT / "docs" / "archive" / "achievements_100_list.md"
    crlf_copy = tmp_path / "achievements_100_list.md"
    lf_bytes = source.read_bytes().replace(b"\r\n", b"\n")
    crlf_copy.write_bytes(lf_bytes.replace(b"\n", b"\r\n"))

    result = subprocess.run(
        [
            "git",
            "-c",
            "core.autocrlf=true",
            "hash-object",
            "--path=docs/archive/achievements_100_list.md",
            str(crlf_copy),
        ],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )

    assert result.returncode == 0, result.stdout
    assert result.stdout.strip() == "daf6a8c858551fcffe4e6e7c8354f4420966cbc0"


def test_verify_codex_plugin_passes_current_infra_contract():
    result = run_script("scripts/verify_codex_plugin.py")
    assert_clean_verifier(result)
    assert "plugin manifest exists" in result.stdout
    assert "codex agent exists" in result.stdout
    assert "extension manifest exists: blender_manifest.toml" in result.stdout
    assert "release builder exists: scripts/build_extension.py" in result.stdout
    assert "package skeleton exists: achievements/__init__.py" in result.stdout
    assert "package metadata exists: achievements/metadata.py" in result.stdout
    assert "catalog module exists: achievements/catalog.py" in result.stdout
    assert "engine helpers exist: achievements/engine.py" in result.stdout
    assert "event helpers exist: achievements/events.py" in result.stdout
    assert "lifecycle helpers exist: achievements/lifecycle.py" in result.stdout
    assert "persistence helpers exist: achievements/persistence.py" in result.stdout
    assert "rewards helpers exist: achievements/rewards.py" in result.stdout
    assert "sync helpers exist: achievements/sync.py" in result.stdout
    assert "ui helpers exist: achievements/ui.py" in result.stdout
    assert "docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md" in result.stdout
    assert "docs/handoff/iteration-handoff-template.md" in result.stdout
    assert "docs/handoff/current.md" in result.stdout
    assert "docs/agent/adrs/0004-extension-namespace-and-files-permission.md" in result.stdout
    assert "workflow exists: .github/workflows/fast-gate.yml" in result.stdout
    assert "workflow exists: .github/workflows/blender-smoke.yml" in result.stdout


def test_find_blender_reports_a_usable_executable(tmp_path):
    env = {**os.environ, "BLENDER_BIN": str(fake_blender(tmp_path))}
    result = run_script("scripts/find_blender.py", env=env)
    assert result.returncode == 0, result.stdout
    assert "Blender 5.0.1" in result.stdout
    assert "fake_blender" in result.stdout


def test_blender_smoke_dry_run_uses_temp_home_and_register_suite(tmp_path):
    env = {**os.environ, "BLENDER_BIN": str(fake_blender(tmp_path))}
    result = run_script("scripts/run_blender_smoke.py", "--suite", "register", "--dry-run", env=env)
    assert result.returncode == 0, result.stdout
    assert "--background" in result.stdout
    assert "--factory-startup" in result.stdout
    assert "tests/blender/smoke_register.py" in result.stdout.replace("\\", "/")
    assert "BLENDER_USER_RESOURCES" in result.stdout


def test_blender_smoke_dry_run_uses_temp_home_and_lifecycle_stress_suite(tmp_path):
    env = {**os.environ, "BLENDER_BIN": str(fake_blender(tmp_path))}
    result = run_script(
        "scripts/run_blender_smoke.py", "--suite", "lifecycle_stress", "--dry-run", env=env
    )
    assert result.returncode == 0, result.stdout
    assert "--background" in result.stdout
    assert "--factory-startup" in result.stdout
    assert "tests/blender/smoke_lifecycle_stress.py" in result.stdout.replace("\\", "/")
    assert "HOME=" in result.stdout
    assert "USERPROFILE=" in result.stdout
    assert "BLENDER_USER_RESOURCES" in result.stdout


def test_blender_smoke_dry_run_uses_temp_home_and_persistence_suite(tmp_path):
    env = {**os.environ, "BLENDER_BIN": str(fake_blender(tmp_path))}
    result = run_script(
        "scripts/run_blender_smoke.py", "--suite", "persistence", "--dry-run", env=env
    )
    assert result.returncode == 0, result.stdout
    assert "--background" in result.stdout
    assert "--factory-startup" in result.stdout
    assert "tests/blender/smoke_persistence.py" in result.stdout.replace("\\", "/")
    assert "HOME=" in result.stdout
    assert "USERPROFILE=" in result.stdout
    assert "BLENDER_USER_RESOURCES" in result.stdout


def test_blender_smoke_dry_run_uses_temp_home_and_engine_suite(tmp_path):
    env = {**os.environ, "BLENDER_BIN": str(fake_blender(tmp_path))}
    result = run_script("scripts/run_blender_smoke.py", "--suite", "engine", "--dry-run", env=env)
    assert result.returncode == 0, result.stdout
    assert "--background" in result.stdout
    assert "--factory-startup" in result.stdout
    assert "tests/blender/smoke_engine.py" in result.stdout.replace("\\", "/")
    assert "HOME=" in result.stdout
    assert "USERPROFILE=" in result.stdout
    assert "BLENDER_USER_RESOURCES" in result.stdout


def test_blender_smoke_dry_run_uses_temp_home_and_ui_visual_suite(tmp_path):
    env = {**os.environ, "BLENDER_BIN": str(fake_blender(tmp_path))}
    result = run_script("scripts/run_blender_smoke.py", "--suite", "ui_visual", "--dry-run", env=env)
    assert result.returncode == 0, result.stdout
    assert "--background" in result.stdout
    assert "--factory-startup" in result.stdout
    assert "tests/blender/smoke_ui_visual.py" in result.stdout.replace("\\", "/")
    assert "HOME=" in result.stdout
    assert "USERPROFILE=" in result.stdout
    assert "BLENDER_USER_RESOURCES" in result.stdout
    assert "ACHIEVEMENTS_VISUAL_QA_DIR=" in result.stdout


def test_blender_source_smoke_loaders_treat_root_runtime_as_a_package():
    smoke_files = (
        "smoke_register.py",
        "smoke_lifecycle_stress.py",
        "smoke_persistence.py",
        "smoke_engine.py",
        "smoke_rewards.py",
        "smoke_ui_visual.py",
    )
    for filename in smoke_files:
        text = (ROOT / "tests" / "blender" / filename).read_text(encoding="utf-8")
        assert "submodule_search_locations=[str(ROOT)]" in text, filename


def test_installed_extension_policy_runner_is_isolated_and_fail_closed(tmp_path):
    env = {**os.environ, "BLENDER_BIN": str(fake_blender(tmp_path))}
    result = run_script(
        "scripts/run_installed_extension_policy.py",
        "--dry-run",
        env=env,
    )
    assert result.returncode == 0, result.stdout
    normalized = result.stdout.replace("\\", "/")
    assert "extension" in normalized and "build" in normalized
    assert "install-file" in normalized
    assert "remove" in normalized
    assert "user_default.achievements" in normalized
    assert "tests/blender/smoke_extension_policy.py" in normalized
    assert "HOME=" in result.stdout
    assert "USERPROFILE=" in result.stdout
    assert "BLENDER_USER_RESOURCES=" in result.stdout
    assert "ACHIEVEMENTS_EXTENSION_MODULE=bl_ext.user_default.achievements" in result.stdout
    assert "ACHIEVEMENTS_EXPECTED_EXTENSION_DIR=" in result.stdout
    assert "ACHIEVEMENTS_POLICY_PHASE=installed" in result.stdout
    assert "ACHIEVEMENTS_POLICY_PHASE=removed" in result.stdout

    scripts_dir = ROOT / "scripts"
    if str(scripts_dir) not in sys.path:
        sys.path.insert(0, str(scripts_dir))
    import run_installed_extension_policy

    pass_marker = "[smoke_extension_policy:PASS]"
    assert run_installed_extension_policy.clean_result_code(0, pass_marker) == 0
    assert (
        run_installed_extension_policy.clean_result_code(
            0,
            f"Policy violation with sys.path\n{pass_marker}",
            expected_marker=pass_marker,
        )
        == 1
    )

    data_root = tmp_path / "sentinel-home" / "BlenderAchievements"
    baseline = run_installed_extension_policy.create_sentinels(data_root)
    assert run_installed_extension_policy.sentinel_fingerprint(data_root) == baseline

    runner_text = (ROOT / "scripts" / "run_installed_extension_policy.py").read_text(
        encoding="utf-8"
    )
    assert 'revision="HEAD"' in runner_text
    assert "remove_command(blender, extension_id)" in runner_text
    assert "[smoke_extension_policy:REMOVED_PASS]" in runner_text
    assert "[installed-policy-runner:FAIL] temporary profile cleanup incomplete" in runner_text

    probe_text = (ROOT / "tests" / "blender" / "smoke_extension_policy.py").read_text(
        encoding="utf-8"
    )
    assert "if warning_map:" in probe_text
    assert "module.unregister()" in probe_text
    assert "module.register()" in probe_text
    assert (
        run_installed_extension_policy.clean_result_code(
            0,
            "Blender quit",
            expected_marker=pass_marker,
        )
        == 1
    )

    exact_archive = tmp_path / "exact-achievements-0.2.2.zip"
    exact_hash = "A" * 64
    exact_result = run_script(
        "scripts/run_installed_extension_policy.py",
        "--dry-run",
        "--archive",
        str(exact_archive),
        "--expected-sha256",
        exact_hash,
        env=env,
    )
    exact_output = exact_result.stdout.replace("\\", "/")
    assert exact_result.returncode == 0, exact_result.stdout
    assert str(exact_archive).replace("\\", "/") in exact_output
    assert "--source-dir" not in exact_output
    assert f"EXPECTED_ARCHIVE_SHA256={exact_hash}" in exact_result.stdout


def test_shipped_runtime_stays_inside_blender_extension_import_namespace():
    result = run_script("scripts/verify_frozen.py")
    assert_clean_verifier(result)
    assert "shipped runtime stays inside Blender extension import policy" in result.stdout

    runtime_files = (
        ROOT / "__init__.py",
        *(ROOT / "achievements").rglob("*.py"),
    )
    for path in runtime_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(alias.name == "sys" for alias in node.names), path
                assert not any(
                    alias.name == "achievements" or alias.name.startswith("achievements.")
                    for alias in node.names
                ), path
            if isinstance(node, ast.ImportFrom) and node.level == 0:
                module_name = node.module or ""
                assert module_name != "sys"
                assert module_name != "achievements"
                assert not module_name.startswith("achievements.")
            if isinstance(node, ast.Attribute):
                attribute = ast.unparse(node)
                assert attribute != "sys.path"
                assert not attribute.startswith("sys.path.")


def test_iteration_11_github_actions_workflows_are_present_and_match_contract():
    fast_workflow = ROOT / ".github" / "workflows" / "fast-gate.yml"
    blender_workflow = ROOT / ".github" / "workflows" / "blender-smoke.yml"

    assert fast_workflow.is_file(), "missing Iteration 11 fast gate workflow"
    assert blender_workflow.is_file(), "missing Iteration 11 Blender smoke workflow"

    fast_text = fast_workflow.read_text(encoding="utf-8")
    for phrase in (
        "name: Achievements Fast Gate",
        "pull_request:",
        "push:",
        "workflow_dispatch:",
        "permissions:",
        "contents: read",
        'python-version: "3.13"',
        "astral-sh/setup-uv@v5",
        "uv run python scripts/verify_frozen.py",
        "uv run python scripts/verify_codex_plugin.py",
        "uv run ruff check .",
        "uv run pytest",
    ):
        assert phrase in fast_text

    blender_text = blender_workflow.read_text(encoding="utf-8")
    for phrase in (
        "name: Achievements Blender Smoke",
        "pull_request:",
        "push:",
        "workflow_dispatch:",
        "permissions:",
        "contents: read",
        'python-version: "3.13"',
        "astral-sh/setup-uv@v5",
        "blender-5-0-1",
        "Blender5.0/blender-5.0.1-linux-x64.tar.xz",
        "blender-5-1-2",
        "Blender5.1/blender-5.1.2-linux-x64.tar.xz",
        "blender-5-2-0",
        "Blender5.2/blender-5.2.0-linux-x64.tar.xz",
        "BLENDER_BIN=",
        "uv run python scripts/run_blender_smoke.py --suite register",
        "uv run python scripts/run_blender_smoke.py --suite lifecycle_stress",
        "uv run python scripts/run_blender_smoke.py --suite persistence",
        "uv run python scripts/run_blender_smoke.py --suite engine",
        "uv run python scripts/run_blender_smoke.py --suite rewards",
        "uv run python scripts/run_blender_smoke.py --suite ui_visual",
        "uv run python scripts/run_installed_extension_policy.py",
    ):
        assert phrase in blender_text
    for forbidden in (
        "continue-on-error",
        "BLENDER_5_2_ALPHA_URL",
        "matrix.canary",
        "skip_smoke",
        "Skipping optional",
    ):
        assert forbidden not in blender_text


def test_iteration_plan_and_handoff_artifacts_are_present():
    plan = ROOT / "docs" / "superpowers" / "plans" / "2026-06-01-achievements-iterative-roadmap.md"
    handoff_template = ROOT / "docs" / "handoff" / "iteration-handoff-template.md"
    current_handoff = ROOT / "docs" / "handoff" / "current.md"

    for path in (plan, handoff_template, current_handoff):
        assert path.is_file(), f"missing required artifact: {path.relative_to(ROOT)}"

    plan_text = plan.read_text(encoding="utf-8")
    for phrase in (
        "## Sources",
        "## Product Concept",
        "## Constraints",
        "## Requirements",
        "Blender 5.1 stable",
        "Blender 5.2 alpha",
        "105 achievements",
        "9 lessons",
        "achievements_v01 (4).py",
        "https://github.com/Gorgutc/Achivments_addon_blender",
        "198tPsyvohUoVkImaLhOD05q1tIgCWL1X",
        "14_uK24navom4tmBFr0EabYQYHH-Ra4fg",
        "## Open Questions",
        "Handoff Gate",
    ):
        assert phrase in plan_text
    for phrase in (
        "- [x] Introduce a modular `achievements/` package without changing runtime behavior.",
        "- [x] Keep `__init__.py` as the Blender entrypoint and delegate only when smoke tests prove parity.",
        "- [x] Add a draft `blender_manifest.toml` early so extension packaging constraints shape later work.",
        "- [x] Extract all achievement and lesson definitions into schema-driven catalog modules.",
        "- [x] Preserve IDs, Russian user-facing strings, categories, rewards, lesson links, and complex steps.",
        "- [x] Add catalog validators for IDs, counts, references, reward types, stat keys, and complex step coverage.",
        "- [x] Split handlers, timers, activity tracking, scene snapshots, and debounce into runtime modules.",
        "- [x] Harden hot reload: repeated `register()` without `unregister()` and repeated `unregister()` must not leak or crash.",
        "- [x] Add repeated lifecycle stress smoke coverage.",
        "- [x] Add `schema_version`, state model, and idempotent migrations.",
        "- [x] Replace direct JSON writes with same-directory temp-file writes, flush/fsync, `os.replace`, and backup handling.",
        "- [x] Add corrupt JSON quarantine/recovery behavior and fixtures for current schema migration.",
        "- [x] Extract stat and complex achievement evaluation into pure modules.",
        "- [x] Add proof/result types and progress calculation interfaces.",
        "- [x] Cover compositor and render-pass checks that currently log `[Achievements] complex step check error` during `smoke_rewards`.",
        "- [x] Extract reward manifest, verifier, cache, importer, and manager modules.",
        "- [x] Preserve fallback behavior for missing material, mesh, and geo node `.blend` assets.",
        "- [x] Record asset licensing decisions before bundling any release assets.",
        "- [x] Split Scene properties, operators, popup tabs/cards, notifications, and pinned overlay into UI modules.",
        "- [x] Preserve tabs: `Задания`, `Выполнено`, `Уроки`, `Хранилище`.",
        "- [x] Run screenshot-based visual QA for header button, popup layout, pinned overlay, notifications, and long text.",
        "- [x] Add sync models, disabled backend interface, queue, and deterministic conflict policy.",
        "- [x] Keep networking disabled by default.",
        "- [x] Exclude pinned UI state from sync unless a future task explicitly changes that.",
        "- [x] Expand unit coverage for catalog, persistence, engine, rewards, and sync stub.",
        "- [x] Add GitHub Actions fast gate: `verify_frozen`, `verify_codex_plugin`, `ruff`, `pytest`.",
        "- [x] Add Blender 5.1 stable smoke gate and Blender 5.2 alpha canary gate.",
        "- [x] Align CI tooling with Python 3.13 while preserving the repository's local Python 3.11+ compatibility policy.",
        "- [x] Finalize extension manifest metadata and release documentation.",
        "- [x] Add validate/build commands for Blender extension packaging.",
        "- [x] Add optional static extension repository generation only after release packaging is stable.",
    ):
        assert phrase in plan_text

    template_text = handoff_template.read_text(encoding="utf-8")
    for heading in (
        "Goal",
        "Changed Files",
        "Done",
        "Remaining",
        "Verification",
        "Agents And Review",
        "Blockers",
        "Residual Risks",
        "Next Start Prompt",
    ):
        assert f"## {heading}" in template_text

    current_text = current_handoff.read_text(encoding="utf-8")
    for heading in (
        "Goal",
        "Changed Files",
        "Done",
        "Remaining",
        "Verification",
        "Agents And Review",
        "Blockers",
        "Residual Risks",
        "Next Start Prompt",
    ):
        assert f"## {heading}" in current_text
    for phrase in (
        "Achievements 0.2.2 — Blender Extension Policy Compliance",
        "`codex/extension-policy-022`",
        "`main@ba2b5c25b0164b61e7d8dcb55b01bd70176a9aa5`",
        "pull/14",
        "PR #14 (`codex/backlog-technical-closeout`) is confirmed merged",
        "pull/15",
        "Draft PR #15",
        "04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3",
        "Blender 5.0.1/5.1.2/5.2.0",
        "`reports/extension/achievements-0.2.2.zip`",
        "14defe9794539c8ffe57c1b9d6675a8662564d32",
        "7C564D30C10B650B0F004FC857424626F9B06E1C331609C619E39899D658617F",
        "`62,724` bytes",
        "`22` regular allowlisted members",
        "`237,778` uncompressed bytes",
        "Canonical member SHA-256 map",
        "blocking checks for implementation commit",
        "`SCHEMA_VERSION = \"1.0.0\"`",
        "ADR 0002",
        "ADR 0004",
        "Store progress and load local reward assets",
        "exact 65-ID/85-pair catalog bijection",
        "full GPL-3.0-or-later `LICENSE`",
        "raw LF SHA-256 `9CB06CA4",
        "Windows CRLF SHA-256 `62DDB016",
        "219 referenced PNG files",
        "11 placeholder tutorial URLs",
        "20 reward `.blend` names",
        "Owner Acceptance For 0.2.1",
        "final Blender-owned `Uninstall` completed successfully",
        "Do not merge, tag, create a GitHub Release",
        "modify any `instance_matcher` information",
    ):
        assert phrase in current_text
    assert "BLENDER_5_2_ALPHA_URL" not in current_text
    assert "Continue after Iteration 12 merge" not in current_text
    assert "must be filled in before delivery" not in current_text
    assert "pending committed-Git canonical ZIP matrix" not in current_text


def test_iteration_3_package_skeleton_and_manifest_are_safe_to_import(tmp_path):
    package_init = ROOT / "achievements" / "__init__.py"
    package_metadata = ROOT / "achievements" / "metadata.py"
    manifest = ROOT / "blender_manifest.toml"

    for path in (package_init, package_metadata, manifest):
        assert path.is_file(), f"missing Iteration 3 artifact: {path.relative_to(ROOT)}"

    for path in (package_init, package_metadata):
        text = path.read_text(encoding="utf-8")
        assert "import bpy" not in text
        assert "BlenderAchievements" not in text
        assert "Path.home()" not in text

    data = tomllib.loads(manifest.read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0.0"
    assert data["id"] == "achievements"
    assert data["version"] == "0.2.2"
    assert data["name"] == "Achievements"
    assert data["type"] == "add-on"
    assert data["blender_version_min"] == "5.0.0"
    assert data["license"] == ["SPDX:GPL-3.0-or-later"]
    assert data["permissions"] == {
        "files": "Store progress and load local reward assets"
    }
    assert "network" not in data["permissions"]

    home = tmp_path / "home"
    userprofile = tmp_path / "profile"
    resources = tmp_path / "resources"
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(userprofile),
        "BLENDER_USER_RESOURCES": str(resources),
        "PYTHONPATH": str(ROOT),
    }
    result = run_script(
        "-c",
        (
            "import achievements; "
            "print(achievements.ADDON_NAME); "
            "print(achievements.ADDON_VERSION); "
            "print(achievements.BLENDER_COMPATIBILITY_FLOOR); "
            "print(achievements.MINIMUM_VALIDATION_TARGET); "
            "print(achievements.PRIMARY_VALIDATION_TARGET); "
            "print(achievements.LATEST_VALIDATION_TARGET); "
            "print(achievements.CANARY_VALIDATION_TARGET)"
        ),
        env=env,
    )
    assert result.returncode == 0, result.stdout
    assert "Achievements" in result.stdout
    assert "(0, 2, 2)" in result.stdout
    assert "(5, 0, 0)" in result.stdout
    assert "Blender 5.0.1" in result.stdout
    assert "Blender 5.1.2" in result.stdout
    assert result.stdout.count("Blender 5.2.0") == 2
    assert not (home / "BlenderAchievements").exists()
    assert not (userprofile / "BlenderAchievements").exists()
    assert not (resources / "BlenderAchievements").exists()


def test_iteration_4_catalog_module_is_source_of_truth_and_safe_to_import(tmp_path):
    catalog = ROOT / "achievements" / "catalog.py"
    assert catalog.is_file(), "missing Iteration 4 catalog module"

    text = catalog.read_text(encoding="utf-8")
    assert "import bpy" not in text
    assert "BlenderAchievements" not in text
    assert "Path.home()" not in text

    assigned = top_level_assigned_names(ROOT / "__init__.py")
    assert "ACHIEVEMENTS_DEF" not in assigned
    assert "LESSONS_DEF" not in assigned

    imported = imported_names_from_catalog(ROOT / "__init__.py")
    for name in (
        "ACHIEVEMENTS_DEF",
        "LESSONS_DEF",
        "ACH_CATEGORIES",
        "LESSON_CATEGORIES",
        "REWARD_CATEGORIES",
    ):
        assert name in imported

    home = tmp_path / "home"
    userprofile = tmp_path / "profile"
    resources = tmp_path / "resources"
    env = {
        **os.environ,
        "HOME": str(home),
        "USERPROFILE": str(userprofile),
        "BLENDER_USER_RESOURCES": str(resources),
        "PYTHONPATH": str(ROOT),
    }
    result = run_script(
        "-c",
        (
            "import json; "
            "from achievements import catalog; "
            "print(json.dumps({"
            "'errors': catalog.validate_catalog(), "
            "'counts': catalog.catalog_counts(), "
            "'digest': catalog.catalog_digest(), "
            "}, ensure_ascii=False, sort_keys=True))"
        ),
        env=env,
    )
    assert result.returncode == 0, result.stdout
    payload = json.loads(result.stdout)
    assert payload["errors"] == []
    assert payload["digest"] == CATALOG_DIGEST
    assert payload["counts"] == {
        "achievement_categories": {
            "EDITING": 45,
            "GEO_NODES": 14,
            "MATERIALS": 17,
            "RENDERING": 17,
            "TIME": 12,
        },
        "achievement_count": 105,
        "check_types": {"complex": 65, "stat": 40},
        "complex_step_range": [1, 4],
        "complex_step_total": 85,
        "difficulty_counts": {"easy": 10, "hard": 55, "medium": 40},
        "first_achievement_id": "first_vertex",
        "first_lesson_id": "lesson_vertices_basics",
        "last_achievement_id": "geonode_domain_switch",
        "last_lesson_id": "lesson_render_basics",
        "lesson_categories": {
            "EDITING": 5,
            "GEO_NODES": 1,
            "MATERIALS": 1,
            "RENDERING": 1,
            "TIME": 1,
        },
        "lesson_count": 9,
        "reward_categories": {"GEO_NODES": 18, "MESHES": 38, "SHADERS": 49},
        "reward_types": {
            "geo_nodes": 5,
            "material": 11,
            "mesh": 5,
            "none": 82,
            "tutorial": 2,
        },
        "stat_keys": {
            "edges_created": 3,
            "faces_created": 6,
            "materials_applied": 5,
            "meshes_1000plus": 4,
            "renders_completed": 6,
            "time_spent": 6,
            "vertices_created": 7,
            "vertices_deleted": 3,
        },
    }
    assert not (home / "BlenderAchievements").exists()
    assert not (userprofile / "BlenderAchievements").exists()
    assert not (resources / "BlenderAchievements").exists()


def test_runtime_docs_alignment_matches_current_policy():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Blender 5.0+" in readme
    for version in ("Blender 5.0.1", "5.1.2", "5.2.0"):
        assert version in readme
    assert "105 достижений" in readme
    assert "9 уроков" in readme
    assert "Blender 4.5 / 5.0 / 5.1" not in readme
    assert "blender_achievements_addon_v01.zip" not in readme
    assert "blender_achievements.py" not in readme
    assert "achievements/catalog.py" in readme
    assert "achievements/predicates/" in readme
    assert "achievements/integrity.py" in readme
    assert "achievements/sync.py" in readme
    assert "networking is not wired into normal add-on use" in readme
    assert ".github/workflows/fast-gate.yml" in readme
    assert ".github/workflows/blender-smoke.yml" in readme
    assert "Python 3.13" in readme
    assert "BLENDER_5_2_ALPHA_URL" not in readme
    assert "optional canary" in readme
    assert "scripts/build_extension.py" in readme
    assert "extension validate" in readme
    assert "extension build" in readme
    assert "extension server-generate" in readme
    assert "release package excludes docs/tests/plugins/scripts" in readme
    assert "catalog, persistence, engine, rewards, sync, UI" in readme
    assert "Одиночный .py" not in readme
    assert "Ожидаемые пользовательские ассеты" in readme
    assert "step_check ==" not in readme
    for stale_line_reference in (
        "813–1527",
        "строка 119",
        "строка 127",
        "Строки 156–167",
        "Строки 190–196",
        "Строка 2325",
        "строки 251–357",
    ):
        assert stale_line_reference not in readme

    extension_guidance_paths = (
        ROOT / "README.md",
        ROOT / "docs" / "agent" / "packaging-release.md",
        ROOT / "docs" / "agent" / "quality-tooling.md",
        ROOT / "docs" / "agent" / "verification.md",
        ROOT
        / "plugins"
        / "achievements-blender-codex"
        / "skills"
        / "achievements-packaging"
        / "SKILL.md",
        ROOT
        / "plugins"
        / "achievements-blender-codex"
        / "skills"
        / "achievements-quality-gate"
        / "SKILL.md",
    )
    for path in extension_guidance_paths:
        text = path.read_text(encoding="utf-8")
        assert "--run-blender" in text, path
        assert "--factory-startup" in text, path
        assert re.search(r"fresh,?\s+(?:never-used\s+)?per-run", text), path
        assert "never-used" in text, path
        for profile_variable in ("HOME", "USERPROFILE", "BLENDER_USER_RESOURCES"):
            assert profile_variable in text, path
        for subcommand in ("validate", "build", "server-generate"):
            assert re.search(rf"extension\s+{re.escape(subcommand)}", text), path
        assert "blender --background --command extension" not in text, path

    for path in extension_guidance_paths[:4] + (extension_guidance_paths[4],):
        text = path.read_text(encoding="utf-8")
        assert "reports/extension/" in text, path
        assert "deliberately" in text, path
        assert "byte-copy" in text, path
        assert re.search(
            r"destination\s+must\s+not\s+already\s+exist",
            text,
            flags=re.IGNORECASE,
        ), path
        assert "source/destination SHA-256" in text, path
        assert re.search(
            r"never\s+rebuild\s+or\s+overwrite",
            text,
            flags=re.IGNORECASE,
        ), path
        assert "Copy-Item -Force" not in text, path
        assert re.search(
            r"per-version\s+self-built\s+ZIPs\s+(?:are|as)\s+build\s+evidence\s+only",
            text,
            flags=re.IGNORECASE,
        ), path
        assert re.search(r"exact\s+frozen\s+canonical\s+SHA", text), path

    for path in (
        ROOT / "README.md",
        ROOT / "docs" / "agent" / "packaging-release.md",
        ROOT / "docs" / "agent" / "verification.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "[extension-cli:WARN]" in text, path
        assert re.search(
            r"invalidates\s+release\s+acceptance\s+even\s+when",
            text,
        ), path
        assert "exits zero" in text, path

    find_blender = (ROOT / "scripts" / "find_blender.py").read_text(encoding="utf-8")
    assert "MIN_VERSION = (5, 0, 0)" in find_blender
    assert "Blender 5.2" in find_blender
    assert find_blender.index("Blender 5.1") < find_blender.index("Blender 5.2")
    assert "Blender 4.5" not in find_blender

    duplicate_policy_docs = (
        ROOT / "docs" / "agent" / "architecture.md",
        ROOT / "docs" / "agent" / "archive-policy.md",
        ROOT / "docs" / "agent" / "frozen-application-contract.md",
        ROOT / "docs" / "agent" / "packaging-release.md",
        ROOT / "docs" / "agent" / "frozen-decisions.md",
    )
    for path in duplicate_policy_docs:
        text = path.read_text(encoding="utf-8")
        assert "ADR 0002" in text, path
        assert "permanent byte-identical duplicate" not in text, path
    for path in (
        ROOT / "docs" / "agent" / "architecture.md",
        ROOT / "docs" / "agent" / "frozen-application-contract.md",
    ):
        text = path.read_text(encoding="utf-8")
        assert "achievements/catalog.py" in text, path
    architecture = (ROOT / "docs" / "agent" / "architecture.md").read_text(encoding="utf-8")
    assert "achievements/sync.py" in architecture
    assert "production networking is not wired into normal add-on use" in architecture

    frozen_contract = (
        ROOT / "docs" / "agent" / "frozen-application-contract.md"
    ).read_text(encoding="utf-8")
    assert "## Cloud Sync Stub" in frozen_contract
    assert "Sync payloads intentionally exclude `pinned_ach_id`" in frozen_contract

    assert not (ROOT / "achievements_100_list.md").exists()
    assert not (ROOT / "achievements_v01 (4).py").exists()
    stale_catalog_reference = (
        ROOT / "docs" / "archive" / "achievements_100_list.md"
    ).read_text(encoding="utf-8")
    assert "stale reference" in stale_catalog_reference
    assert "105 achievements" in stale_catalog_reference
    assert "9 lessons" in stale_catalog_reference

    packaging_release = (ROOT / "docs" / "agent" / "packaging-release.md").read_text(encoding="utf-8")
    assert "Achievements 0.2.2 candidate" in packaging_release
    assert "scripts/build_extension.py" in packaging_release
    assert "reports/extension-validation/<run-id>/blender-5.1.2/source" in packaging_release
    assert "release package excludes docs/tests/plugins/scripts" in packaging_release
    assert "ADR 0002 retired `achievements_v01 (4).py`" in packaging_release
    assert "`LICENSE`" in packaging_release
    assert "--revision HEAD" in packaging_release
    assert "extension validate" in packaging_release
    assert "extension build" in packaging_release
    assert "extension server-generate" in packaging_release
    assert "Whether a Blender extension manifest is introduced" not in packaging_release

    verification = (ROOT / "docs" / "agent" / "verification.md").read_text(encoding="utf-8")
    assert ".github/workflows/fast-gate.yml" in verification
    assert ".github/workflows/blender-smoke.yml" in verification
    for version in ("Blender 5.0.1", "5.1.2", "5.2.0"):
        assert version in verification
    assert "BLENDER_5_2_ALPHA_URL" not in verification
    assert "no target is skipped or non-blocking" in verification
    assert "scripts/build_extension.py" in verification
    assert "extension validate" in verification
    assert "extension build" in verification

    quality_tooling = (ROOT / "docs" / "agent" / "quality-tooling.md").read_text(encoding="utf-8")
    assert "Python 3.13" in quality_tooling
    for version in ("Blender 5.0.1", "5.1.2", "5.2.0"):
        assert version in quality_tooling
    assert "no repository URL variable, skipped row, canary, or `continue-on-error`" in quality_tooling
    assert "scripts/build_extension.py" in quality_tooling
    assert "Packaging tests freeze LF/CRLF behavior" in quality_tooling
    assert "uv run python scripts/run_blender_smoke.py --suite ui_visual" in quality_tooling
