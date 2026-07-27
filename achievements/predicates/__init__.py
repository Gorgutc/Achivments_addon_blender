"""Pure complex-achievement predicates for Blender-facing adapters."""

from __future__ import annotations

from .registry import (
    PREDICATE_PAIRS,
    PREDICATE_REGISTRY,
    catalog_pairs,
    evaluate_predicate,
    registry_bijection_errors,
)
from .types import (
    ClockSnapshot,
    PredicateContext,
    PredicateResult,
    SpeedModelReset,
    StatsSnapshot,
)

__all__ = [
    "ClockSnapshot",
    "PREDICATE_PAIRS",
    "PREDICATE_REGISTRY",
    "PredicateContext",
    "PredicateResult",
    "SpeedModelReset",
    "StatsSnapshot",
    "catalog_pairs",
    "evaluate_predicate",
    "registry_bijection_errors",
]
