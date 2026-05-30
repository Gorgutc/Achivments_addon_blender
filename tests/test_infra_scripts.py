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
