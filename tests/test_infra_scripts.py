import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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


def test_verify_frozen_passes_current_addon_contract():
    result = run_script("scripts/verify_frozen.py")
    assert_clean_verifier(result)
    assert "achievement ids unique" in result.stdout
    assert "complex ids covered" in result.stdout


def test_verify_codex_plugin_passes_current_infra_contract():
    result = run_script("scripts/verify_codex_plugin.py")
    assert_clean_verifier(result)
    assert "plugin manifest exists" in result.stdout
    assert "codex agent exists" in result.stdout
    assert "docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md" in result.stdout
    assert "docs/handoff/iteration-handoff-template.md" in result.stdout
    assert "docs/handoff/current.md" in result.stdout


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
        "Iteration 2: Runtime And Documentation Alignment",
        "README.md",
        "scripts/find_blender.py",
        "uv run python scripts/verify_frozen.py",
        "uv run python scripts/verify_codex_plugin.py",
        "uv run ruff check .",
        "uv run pytest",
        "Blender smoke suites `register`, `persistence`, and `rewards` passed",
        "Final `/review` fallback status: PASS",
        "Continue `codex/implement-iterative-plan-baseline` from Iteration 3",
    ):
        assert phrase in current_text
    assert "Final gate to run" not in current_text
    assert "must be performed before final delivery" not in current_text
    assert "only inside negative test assertions" not in current_text


def test_runtime_docs_alignment_matches_current_policy():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Blender 5.0+" in readme
    assert "Blender 5.1 stable" in readme
    assert "Blender 5.2 alpha" in readme
    assert "105 достижений" in readme
    assert "9 уроков" in readme
    assert "Blender 4.5 / 5.0 / 5.1" not in readme
    assert "blender_achievements_addon_v01.zip" not in readme
    assert "blender_achievements.py" not in readme
    assert "Ожидаемые пользовательские ассеты" in readme

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
        assert "permanent byte-identical duplicate" in text, path
        assert "removed or archived" not in text, path

    stale_catalog_reference = (ROOT / "achievements_100_list.md").read_text(encoding="utf-8")
    assert "stale reference" in stale_catalog_reference
    assert "105 achievements" in stale_catalog_reference
    assert "9 lessons" in stale_catalog_reference
