"""Runtime event helpers for activity and scene snapshot state.

The helpers stay free of ``bpy`` imports so normal unit tests can cover the
state transitions that Blender handlers and timers trigger.
"""

from __future__ import annotations

import datetime
from typing import Any


def _accrue_activity_window(stats: Any, *, now: float, idle_timeout: int) -> None:
    """Accrue the uncounted part of the current non-refreshing activity window."""
    last_activity = float(stats._last_activity)
    if last_activity <= 0:
        return

    accounted_until = float(
        getattr(stats, "_last_accounted_activity", last_activity)
    )
    if accounted_until <= 0:
        accounted_until = last_activity
    if now < last_activity or now < accounted_until:
        # A monotonic clock should not roll back. Fail closed if an injected
        # clock does: abandon the current window until the next real event.
        stats._last_activity = 0.0
        stats._last_accounted_activity = 0.0
        return

    window_end = min(now, last_activity + max(0, idle_timeout))
    whole_seconds = int(max(0.0, window_end - accounted_until))
    if whole_seconds > 0:
        stats.time_spent += whole_seconds
        # Advance by credited whole seconds instead of directly to ``now`` so
        # frequent sub-second UI flushes do not discard fractional remainder.
        stats._last_accounted_activity = accounted_until + whole_seconds


def record_user_activity(stats: Any, *, now: float, idle_timeout: int) -> None:
    """Finish the previous window, then open one from a real activity event."""
    last_activity = float(stats._last_activity)
    accounted_until = float(
        getattr(stats, "_last_accounted_activity", last_activity)
    )
    if (
        last_activity <= 0
        or now < last_activity
        or now < accounted_until
    ):
        stats._last_activity = now
        stats._last_accounted_activity = now
        return

    previous_window_end = last_activity + max(0, idle_timeout)
    _accrue_activity_window(stats, now=now, idle_timeout=idle_timeout)
    stats._last_activity = now
    if now > previous_window_end:
        # A real idle gap starts a disconnected activity window. Overlapping
        # windows retain the cursor so sub-second events keep their remainder.
        stats._last_accounted_activity = now


def flush_session_time(
    stats: Any,
    *,
    now: float,
    idle_timeout: int,
    today: str | None = None,
) -> None:
    """Accrue a bounded activity tail and update daily session state."""
    _accrue_activity_window(stats, now=now, idle_timeout=idle_timeout)

    session_day = today or datetime.date.today().isoformat()
    stats._session_date = session_day
    if session_day not in stats.daily_sessions:
        stats.daily_sessions.append(session_day)
        if len(stats.daily_sessions) > 60:
            stats.daily_sessions = stats.daily_sessions[-60:]


def reset_session_tracking(stats: Any, *, now: float) -> None:
    """Reset session timestamps without treating register/load as activity."""
    stats._session_start = now
    stats._last_activity = 0.0
    stats._last_accounted_activity = 0.0
    stats._time_at_session_start = stats.time_spent


def reset_scene_snapshots(stats: Any) -> None:
    """Clear cached scene snapshots used by depsgraph delta tracking."""
    stats._prev_verts.clear()
    stats._prev_edges.clear()
    stats._prev_faces.clear()
    stats._prev_mats.clear()


def reset_speed_model_tracking(stats: Any, *, now: float) -> None:
    """Reset speed-modeler debounce window to the current vertex count."""
    stats._speed_model_start = now
    stats._speed_model_verts = stats.vertices_created


def reset_progress(
    stats: Any,
    *,
    activity_now: float,
    speed_model_now: float,
) -> None:
    """Reset all achievement progress to a clean profile (testing/dev reset).

    Zeroes every persisted stat counter, clears unlock/reward/pin/streak state,
    then resets runtime snapshots and the session/speed-modeler windows so the
    next activity accumulates from a fresh baseline.

    Note: this clears ``daily_sessions``/``_session_date`` to the empty state,
    but a later ``save_data`` flush re-records *today* as an open-day session
    (exactly like a brand-new profile's first save), so the persisted streak
    list becomes ``[today]`` rather than staying empty. A single day cannot
    satisfy any streak achievement, so this is the intended fresh-session state.
    """
    for field in (
        "vertices_created",
        "vertices_deleted",
        "edges_created",
        "faces_created",
        "meshes_1000plus",
        "materials_applied",
        "time_spent",
        "renders_completed",
    ):
        setattr(stats, field, 0)
    stats.unlocked = set()
    stats.unlock_hashes = {}
    stats.rewards_claimed = set()
    stats.pinned_ach_id = ""
    stats.daily_sessions = []
    stats._session_date = ""
    reset_scene_snapshots(stats)
    reset_session_tracking(stats, now=activity_now)
    reset_speed_model_tracking(stats, now=speed_model_now)
