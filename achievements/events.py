"""Runtime event helpers for activity and scene snapshot state.

The helpers stay free of ``bpy`` imports so normal unit tests can cover the
state transitions that Blender handlers and timers trigger.
"""

from __future__ import annotations

import datetime
from typing import Any


def record_user_activity(stats: Any, *, now: float, idle_timeout: int) -> None:
    """Count active time since the previous activity unless the gap is idle."""
    if stats._last_activity > 0:
        gap = now - stats._last_activity
        if gap <= idle_timeout:
            stats.time_spent += int(gap)
    stats._last_activity = now


def flush_session_time(
    stats: Any,
    *,
    now: float,
    idle_timeout: int,
    today: str | None = None,
) -> None:
    """Finalize the current active-time window and update daily session state."""
    if stats._last_activity > 0:
        gap = now - stats._last_activity
        if gap <= idle_timeout:
            stats.time_spent += int(gap)
            stats._last_activity = now

    session_day = today or datetime.date.today().isoformat()
    stats._session_date = session_day
    if session_day not in stats.daily_sessions:
        stats.daily_sessions.append(session_day)
        if len(stats.daily_sessions) > 60:
            stats.daily_sessions = stats.daily_sessions[-60:]


def reset_session_tracking(stats: Any, *, now: float) -> None:
    """Reset session timestamps after register/load while preserving counters."""
    stats._session_start = now
    stats._last_activity = now
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
