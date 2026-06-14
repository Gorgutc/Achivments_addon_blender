from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def make_stats(**overrides):
    values = {
        "time_spent": 0,
        "_last_activity": 0.0,
        "_session_start": 0.0,
        "_time_at_session_start": 0,
        "_session_date": "",
        "daily_sessions": [],
        "_prev_verts": {"Cube": 8},
        "_prev_edges": {"Cube": 12},
        "_prev_faces": {"Cube": 6},
        "_prev_mats": {"Cube"},
        "_speed_model_start": 0.0,
        "_speed_model_verts": 0,
        "vertices_created": 0,
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def test_record_user_activity_counts_only_non_idle_gaps():
    from achievements import events

    stats = make_stats(time_spent=10, _last_activity=100.0)

    events.record_user_activity(stats, now=130.0, idle_timeout=120)
    assert stats.time_spent == 40
    assert stats._last_activity == 130.0

    events.record_user_activity(stats, now=260.0, idle_timeout=120)
    assert stats.time_spent == 40
    assert stats._last_activity == 260.0


def test_flush_session_time_updates_daily_session_once_and_trims_history():
    from achievements import events

    days = [f"2026-04-{day:02d}" for day in range(1, 31)]
    days.extend(f"2026-05-{day:02d}" for day in range(1, 32))
    stats = make_stats(time_spent=5, _last_activity=100.0, daily_sessions=days)

    events.flush_session_time(stats, now=130.0, idle_timeout=120, today="2026-06-06")
    assert stats.time_spent == 35
    assert stats._last_activity == 130.0
    assert stats._session_date == "2026-06-06"
    assert stats.daily_sessions[-1] == "2026-06-06"
    assert len(stats.daily_sessions) == 60

    events.flush_session_time(stats, now=140.0, idle_timeout=120, today="2026-06-06")
    assert stats.daily_sessions.count("2026-06-06") == 1


def test_reset_tracking_helpers_clear_runtime_snapshots():
    from achievements import events

    stats = make_stats(time_spent=42, vertices_created=128)

    events.reset_session_tracking(stats, now=500.0)
    assert stats._session_start == 500.0
    assert stats._last_activity == 500.0
    assert stats._time_at_session_start == 42

    events.reset_scene_snapshots(stats)
    assert stats._prev_verts == {}
    assert stats._prev_edges == {}
    assert stats._prev_faces == {}
    assert stats._prev_mats == set()

    events.reset_speed_model_tracking(stats, now=700.0)
    assert stats._speed_model_start == 700.0
    assert stats._speed_model_verts == 128


def test_reset_progress_clears_counters_unlocks_and_runtime_state():
    from achievements import events
    from achievements.persistence import STAT_FIELDS

    # Seed every canonical stat counter (cross-checked against the persistence
    # source of truth, so a future counter added there but missed by
    # reset_progress is caught) plus runtime/session state, all non-zero.
    counters = {field: 100 + index for index, field in enumerate(STAT_FIELDS)}
    stats = make_stats(
        **counters,
        _last_activity=100.0,
        _session_date="2026-06-13",
        _speed_model_verts=512,
        daily_sessions=["2026-06-01", "2026-06-02"],
        unlocked={"first_vertex", "first_render"},
        unlock_hashes={"first_vertex": "abc123", "first_render": "def456"},
        rewards_claimed={"first_render"},
        pinned_ach_id="first_vertex",
    )

    events.reset_progress(stats, now=900.0)

    for field in STAT_FIELDS:
        assert getattr(stats, field) == 0, field
    assert stats.unlocked == set()
    assert stats.unlock_hashes == {}
    assert stats.rewards_claimed == set()
    assert stats.pinned_ach_id == ""
    assert stats.daily_sessions == []
    assert stats._session_date == ""

    # Runtime snapshots and session/speed windows are rebased to the clean state.
    assert stats._prev_verts == {}
    assert stats._prev_edges == {}
    assert stats._prev_faces == {}
    assert stats._prev_mats == set()
    assert stats._session_start == 900.0
    assert stats._last_activity == 900.0
    assert stats._time_at_session_start == 0
    assert stats._speed_model_start == 900.0
    # _speed_model_verts was seeded to 512 and must be rebased to the now-zero
    # vertices_created, proving reset_speed_model_tracking actually ran.
    assert stats._speed_model_verts == 0
