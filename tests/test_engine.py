from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def make_stats(**overrides):
    values = {
        "vertices_created": 0,
        "renders_completed": 0,
        "unlocked": set(),
        "daily_sessions": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_engine_module_is_safe_to_import_and_exposes_result_types():
    engine_path = ROOT / "achievements" / "engine.py"
    assert engine_path.is_file(), "missing Iteration 7 engine module"

    text = engine_path.read_text(encoding="utf-8")
    assert "import bpy" not in text
    assert "BlenderAchievements" not in text
    assert "Path.home()" not in text

    from achievements import engine

    assert engine.StepProof
    assert engine.RuleEvaluation
    assert engine.AchievementProgress


def test_stat_evaluation_and_progress_are_clamped_and_report_proof():
    from achievements import engine

    ach = {
        "id": "ten_vertices",
        "check_type": "stat",
        "stat_key": "vertices_created",
        "goal": 10,
    }

    pending = engine.evaluate_stat_achievement(ach, make_stats(vertices_created=4))
    complete = engine.evaluate_stat_achievement(ach, make_stats(vertices_created=15))
    progress = engine.stat_progress(ach, make_stats(vertices_created=15), bar_len=10)

    assert not pending.achieved
    assert pending.proofs == (
        engine.StepProof(
            key="vertices_created",
            achieved=False,
            value=4,
            goal=10,
            kind="stat_threshold",
        ),
    )
    assert complete.achieved
    assert complete.proofs[0].value == 15
    assert progress.value == 15
    assert progress.goal == 10
    assert progress.ratio == 1.0
    assert progress.percent == 100
    assert progress.bar == "██████████"


def test_complex_evaluation_uses_step_callback_and_reports_progress():
    from achievements import engine

    ach = {
        "id": "smooth_cube",
        "check_type": "complex",
        "complex_id": "smooth_cube",
        "steps": [
            {"label": "Mesh", "check": "has_mesh"},
            {"label": "Subsurf", "check": "has_subsurf"},
        ],
    }
    completed_steps = {"has_mesh"}

    def evaluator(complex_id, step_check):
        assert complex_id == "smooth_cube"
        return step_check in completed_steps

    result = engine.evaluate_complex_achievement(ach, evaluator)
    progress = engine.complex_progress(ach, evaluator)

    assert not result.achieved
    assert result.proofs == (
        engine.StepProof(
            key="has_mesh",
            achieved=True,
            label="Mesh",
            kind="complex_step",
        ),
        engine.StepProof(
            key="has_subsurf",
            achieved=False,
            label="Subsurf",
            kind="complex_step",
        ),
    )
    assert progress.done_count == 1
    assert progress.total_count == 2
    assert progress.ratio == 0.5
    assert progress.percent == 50


def test_engine_selects_pending_stat_and_complex_unlocks():
    from achievements import engine

    achievements = [
        {
            "id": "ten_vertices",
            "check_type": "stat",
            "stat_key": "vertices_created",
            "goal": 10,
        },
        {
            "id": "first_render",
            "check_type": "stat",
            "stat_key": "renders_completed",
            "goal": 1,
        },
        {
            "id": "smooth_cube",
            "check_type": "complex",
            "complex_id": "smooth_cube",
            "steps": [{"label": "Mesh", "check": "has_mesh"}],
        },
    ]
    stats = make_stats(vertices_created=12, renders_completed=1, unlocked={"first_render"})

    stat_results = engine.pending_stat_unlocks(achievements, stats)
    complex_results = engine.pending_complex_unlocks(
        achievements,
        unlocked=set(),
        step_evaluator=lambda complex_id, step_check: complex_id == "smooth_cube"
        and step_check == "has_mesh",
    )

    assert [item.achievement_id for item in stat_results] == ["ten_vertices"]
    assert [item.achievement_id for item in complex_results] == ["smooth_cube"]


def test_streak_validation_is_idempotent_and_rejects_bad_dates():
    from achievements import engine

    assert engine.has_streak(["2026-06-01", "2026-06-02", "2026-06-03"], 3)
    assert not engine.has_streak(["2026-06-01", "2026-06-03"], 2)
    assert not engine.has_streak(["2026-06-01", "bad", "2026-06-02"], 2)
