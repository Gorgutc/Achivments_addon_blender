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
        "_last_accounted_activity": 0.0,
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


def test_idle_flushes_do_not_open_time_window_but_keep_open_day_tracking():
    from achievements import events

    stats = make_stats(time_spent=10)
    events.reset_session_tracking(stats, now=100.0)

    for now in (160.0, 220.0, 280.0, 340.0):
        events.flush_session_time(
            stats,
            now=now,
            idle_timeout=120,
            today="2026-06-06",
        )
        assert stats.time_spent == 10

    assert stats._last_activity == 0.0
    assert stats._last_accounted_activity == 0.0
    assert stats.daily_sessions == ["2026-06-06"]


def test_activity_window_is_non_refreshing_and_idempotent():
    from achievements import events

    stats = make_stats()
    events.record_user_activity(stats, now=100.0, idle_timeout=120)
    assert stats.time_spent == 0

    events.flush_session_time(stats, now=160.0, idle_timeout=120)
    assert stats.time_spent == 60
    events.flush_session_time(stats, now=160.0, idle_timeout=120)
    assert stats.time_spent == 60
    events.flush_session_time(stats, now=220.0, idle_timeout=120)
    assert stats.time_spent == 120
    events.flush_session_time(stats, now=280.0, idle_timeout=120)
    events.flush_session_time(stats, now=340.0, idle_timeout=120)
    assert stats.time_spent == 120
    assert stats._last_activity == 100.0
    assert stats._last_accounted_activity == 220.0


def test_real_activity_extends_windows_without_counting_long_idle():
    from achievements import events

    stats = make_stats()
    events.record_user_activity(stats, now=100.0, idle_timeout=120)
    events.flush_session_time(stats, now=160.0, idle_timeout=120)
    events.record_user_activity(stats, now=200.0, idle_timeout=120)
    assert stats.time_spent == 100

    events.flush_session_time(stats, now=260.0, idle_timeout=120)
    assert stats.time_spent == 160
    events.flush_session_time(stats, now=320.0, idle_timeout=120)
    events.flush_session_time(stats, now=380.0, idle_timeout=120)
    assert stats.time_spent == 220

    events.record_user_activity(stats, now=500.0, idle_timeout=120)
    assert stats.time_spent == 220
    events.flush_session_time(stats, now=530.0, idle_timeout=120)
    assert stats.time_spent == 250

    rare_events = make_stats()
    events.record_user_activity(rare_events, now=100.0, idle_timeout=120)
    events.record_user_activity(rare_events, now=400.0, idle_timeout=120)
    assert rare_events.time_spent == 120
    events.flush_session_time(rare_events, now=430.0, idle_timeout=120)
    assert rare_events.time_spent == 150


def test_activity_window_handles_fractional_flushes_suspend_and_rollback():
    from achievements import events

    stats = make_stats()
    events.record_user_activity(stats, now=100.0, idle_timeout=120)
    events.flush_session_time(stats, now=100.4, idle_timeout=120)
    events.flush_session_time(stats, now=100.8, idle_timeout=120)
    assert stats.time_spent == 0
    events.flush_session_time(stats, now=101.2, idle_timeout=120)
    assert stats.time_spent == 1

    events.flush_session_time(stats, now=10_000.0, idle_timeout=120)
    assert stats.time_spent == 120
    events.flush_session_time(stats, now=90.0, idle_timeout=120)
    assert stats.time_spent == 120
    assert stats._last_activity == 0.0
    assert stats._last_accounted_activity == 0.0
    events.flush_session_time(stats, now=20_000.0, idle_timeout=120)
    assert stats.time_spent == 120

    frequent_events = make_stats()
    for now in (100.0, 100.4, 100.8, 101.2):
        events.record_user_activity(frequent_events, now=now, idle_timeout=120)
    assert frequent_events.time_spent == 1
    assert frequent_events._last_accounted_activity == 101.0


def test_flush_session_time_updates_daily_session_once_and_trims_history():
    from achievements import events

    days = [f"2026-04-{day:02d}" for day in range(1, 31)]
    days.extend(f"2026-05-{day:02d}" for day in range(1, 32))
    stats = make_stats(time_spent=5, daily_sessions=days)
    events.record_user_activity(stats, now=100.0, idle_timeout=120)

    events.flush_session_time(stats, now=130.0, idle_timeout=120, today="2026-06-06")
    assert stats.time_spent == 35
    assert stats._last_activity == 100.0
    assert stats._last_accounted_activity == 130.0
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
    assert stats._last_activity == 0.0
    assert stats._last_accounted_activity == 0.0
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
        _last_accounted_activity=100.0,
        _session_date="2026-06-13",
        _speed_model_verts=512,
        daily_sessions=["2026-06-01", "2026-06-02"],
        unlocked={"first_vertex", "first_render"},
        unlock_hashes={"first_vertex": "abc123", "first_render": "def456"},
        rewards_claimed={"first_render"},
        pinned_ach_id="first_vertex",
    )

    events.reset_progress(stats, activity_now=900.0, speed_model_now=1200.0)

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
    assert stats._last_activity == 0.0
    assert stats._last_accounted_activity == 0.0
    assert stats._time_at_session_start == 0
    assert stats._speed_model_start == 1200.0
    # _speed_model_verts was seeded to 512 and must be rebased to the now-zero
    # vertices_created, proving reset_speed_model_tracking actually ran.
    assert stats._speed_model_verts == 0
