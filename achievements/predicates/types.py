"""Immutable inputs and outputs for pure complex-achievement predicates."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True, slots=True)
class StatsSnapshot:
    """Read-only subset of runtime stats used by complex predicates."""

    renders_completed: int = 0
    time_spent: float = 0.0
    time_at_session_start: float = 0.0
    daily_sessions: tuple[str, ...] = ()
    speed_model_start: float = 0.0
    speed_model_verts: int = 0
    vertices_created: int = 0
    unlocked: frozenset[str] = frozenset()

    @classmethod
    def from_runtime(cls, stats: Any) -> StatsSnapshot:
        """Copy mutable Blender runtime stats into an immutable snapshot."""
        return cls(
            renders_completed=stats.renders_completed,
            time_spent=stats.time_spent,
            time_at_session_start=stats._time_at_session_start,
            daily_sessions=tuple(stats.daily_sessions),
            speed_model_start=stats._speed_model_start,
            speed_model_verts=stats._speed_model_verts,
            vertices_created=stats.vertices_created,
            unlocked=frozenset(stats.unlocked),
        )


@dataclass(frozen=True, slots=True)
class ClockSnapshot:
    """Injected wall-clock values used by time-sensitive predicates."""

    now: datetime
    timestamp: float


@dataclass(frozen=True, slots=True)
class PredicateContext:
    """Duck-typed Blender state plus deterministic runtime snapshots."""

    scene: Any
    data: Any
    view_layer: Any
    stats: StatsSnapshot
    clock: ClockSnapshot


@dataclass(frozen=True, slots=True)
class SpeedModelReset:
    """A planned runtime mutation applied only by the Blender adapter."""

    started_at: float
    vertices_created: int


@dataclass(frozen=True, slots=True)
class PredicateResult:
    """Exception-safe predicate outcome and optional adapter work."""

    matched: bool
    speed_model_reset: SpeedModelReset | None = None
    error: str | None = None


Predicate = Callable[[PredicateContext], bool | PredicateResult]
