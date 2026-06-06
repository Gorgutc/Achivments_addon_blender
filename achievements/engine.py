"""Pure rule-evaluation helpers for Achievements.

The module owns stat thresholds, complex-step orchestration, progress DTOs, and
small pure helpers. Blender scene predicates stay in the runtime entrypoint and
are passed in as callbacks.
"""

from __future__ import annotations

import datetime
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any

FILLED_BAR = "\u2588"
EMPTY_BAR = "\u2591"


@dataclass(frozen=True)
class StepProof:
    key: str
    achieved: bool
    value: int | float | None = None
    goal: int | float | None = None
    label: str = ""
    kind: str = "unknown"


@dataclass(frozen=True)
class RuleEvaluation:
    achievement_id: str
    check_type: str
    achieved: bool
    proofs: tuple[StepProof, ...]


@dataclass(frozen=True)
class AchievementProgress:
    achievement_id: str
    check_type: str
    value: int | float = 0
    goal: int | float = 0
    done_count: int = 0
    total_count: int = 0
    ratio: float = 0.0
    percent: int = 0
    bar: str = ""


StepEvaluator = Callable[[str, str], bool]


def _number(value: Any) -> int | float:
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, float)):
        return value
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def clamp_ratio(value: int | float, goal: int | float) -> float:
    if goal <= 0:
        return 0.0
    return max(0.0, min(float(value) / float(goal), 1.0))


def progress_bar(ratio: float, *, bar_len: int = 10) -> str:
    safe_ratio = max(0.0, min(float(ratio), 1.0))
    filled = int(safe_ratio * bar_len)
    return FILLED_BAR * filled + EMPTY_BAR * (bar_len - filled)


def evaluate_stat_achievement(achievement: dict[str, Any], stats: Any) -> RuleEvaluation:
    stat_key = achievement["stat_key"]
    goal = _number(achievement.get("goal", 0))
    value = _number(getattr(stats, stat_key, 0))
    achieved = value >= goal
    return RuleEvaluation(
        achievement_id=achievement["id"],
        check_type="stat",
        achieved=achieved,
        proofs=(
            StepProof(
                key=stat_key,
                achieved=achieved,
                value=value,
                goal=goal,
                kind="stat_threshold",
            ),
        ),
    )


def stat_progress(
    achievement: dict[str, Any],
    stats: Any,
    *,
    bar_len: int = 10,
) -> AchievementProgress:
    stat_key = achievement["stat_key"]
    goal = _number(achievement.get("goal", 0))
    value = _number(getattr(stats, stat_key, 0))
    ratio = clamp_ratio(value, goal)
    return AchievementProgress(
        achievement_id=achievement["id"],
        check_type="stat",
        value=value,
        goal=goal,
        ratio=ratio,
        percent=int(ratio * 100),
        bar=progress_bar(ratio, bar_len=bar_len),
    )


def evaluate_complex_achievement(
    achievement: dict[str, Any],
    step_evaluator: StepEvaluator,
) -> RuleEvaluation:
    complex_id = achievement.get("complex_id", "")
    proofs = []
    for step in achievement.get("steps", []):
        step_key = step["check"]
        achieved = bool(step_evaluator(complex_id, step_key))
        proofs.append(
            StepProof(
                key=step_key,
                achieved=achieved,
                label=step.get("label", ""),
                kind="complex_step",
            )
        )
    return RuleEvaluation(
        achievement_id=achievement["id"],
        check_type="complex",
        achieved=bool(proofs) and all(proof.achieved for proof in proofs),
        proofs=tuple(proofs),
    )


def complex_progress(
    achievement: dict[str, Any],
    step_evaluator: StepEvaluator,
) -> AchievementProgress:
    result = evaluate_complex_achievement(achievement, step_evaluator)
    total = len(result.proofs)
    done = sum(1 for proof in result.proofs if proof.achieved)
    ratio = clamp_ratio(done, total)
    return AchievementProgress(
        achievement_id=achievement["id"],
        check_type="complex",
        done_count=done,
        total_count=total,
        ratio=ratio,
        percent=int(ratio * 100),
    )


def pending_stat_unlocks(
    achievements: Iterable[dict[str, Any]],
    stats: Any,
    *,
    unlocked: set[str] | None = None,
) -> list[RuleEvaluation]:
    unlocked_ids = unlocked if unlocked is not None else set(getattr(stats, "unlocked", set()))
    results = []
    for achievement in achievements:
        if achievement.get("check_type") != "stat" or achievement["id"] in unlocked_ids:
            continue
        result = evaluate_stat_achievement(achievement, stats)
        if result.achieved:
            results.append(result)
    return results


def pending_complex_unlocks(
    achievements: Iterable[dict[str, Any]],
    *,
    unlocked: set[str],
    step_evaluator: StepEvaluator,
) -> list[RuleEvaluation]:
    results = []
    for achievement in achievements:
        if achievement.get("check_type") != "complex" or achievement["id"] in unlocked:
            continue
        result = evaluate_complex_achievement(achievement, step_evaluator)
        if result.achieved:
            results.append(result)
    return results


def has_streak(daily_sessions: Iterable[str], required_days: int) -> bool:
    dates = list(daily_sessions)
    if len(dates) < required_days:
        return False
    try:
        normalized = sorted(set(datetime.date.fromisoformat(item) for item in dates))
    except (TypeError, ValueError):
        return False
    streak = 1
    for index in range(1, len(normalized)):
        if (normalized[index] - normalized[index - 1]).days == 1:
            streak += 1
            if streak >= required_days:
                return True
        else:
            streak = 1
    return False
