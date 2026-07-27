"""Pure clock- and persisted-state predicates."""

from __future__ import annotations

from ..engine import has_streak
from .types import Predicate, PredicateContext, PredicateResult, SpeedModelReset


def _is_night_session(context: PredicateContext) -> bool:
    hour = context.clock.now.hour
    return hour >= 22 or hour < 2


def _is_early_bird(context: PredicateContext) -> bool:
    return 5 <= context.clock.now.hour < 8


def _is_weekend_marathon(context: PredicateContext) -> bool:
    if context.clock.now.weekday() < 5:
        return False
    active_session = context.stats.time_spent - context.stats.time_at_session_start
    return active_session >= 6 * 3600


def _has_seven_day_streak(context: PredicateContext) -> bool:
    return has_streak(context.stats.daily_sessions, 7)


def _has_thirty_day_streak(context: PredicateContext) -> bool:
    return has_streak(context.stats.daily_sessions, 30)


def _is_speed_modeler(context: PredicateContext) -> PredicateResult:
    stats = context.stats
    if stats.speed_model_start > 0:
        elapsed = context.clock.timestamp - stats.speed_model_start
        gained = stats.vertices_created - stats.speed_model_verts
        if elapsed <= 300 and gained >= 500:
            return PredicateResult(True)
        if elapsed > 300:
            return PredicateResult(
                False,
                speed_model_reset=SpeedModelReset(
                    started_at=context.clock.timestamp,
                    vertices_created=stats.vertices_created,
                ),
            )
    return PredicateResult(False)


def _has_fifty_unlocked(context: PredicateContext) -> bool:
    return len(context.stats.unlocked) >= 50


TIME_STATE_PREDICATES: dict[tuple[str, str], Predicate] = {
    ("night_session", "is_night_session"): _is_night_session,
    ("daily_streak_7", "has_7_day_streak"): _has_seven_day_streak,
    ("weekend_marathon", "is_weekend_marathon"): _is_weekend_marathon,
    ("daily_streak_30", "has_30_day_streak"): _has_thirty_day_streak,
    ("speed_modeler", "is_speed_modeler"): _is_speed_modeler,
    ("early_bird", "is_early_bird"): _is_early_bird,
    ("blender_legend", "has_50_unlocked"): _has_fifty_unlocked,
}
