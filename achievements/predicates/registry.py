"""Canonical complex-predicate registry and exception-safe evaluator."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .geometry_nodes import GEOMETRY_NODE_PREDICATES
from .material import MATERIAL_PREDICATES
from .object_modifier import OBJECT_MODIFIER_PREDICATES
from .render import RENDER_PREDICATES
from .time_state import TIME_STATE_PREDICATES
from .types import Predicate, PredicateContext, PredicateResult

PredicateKey = tuple[str, str]


def _merge_registries(*registries: Mapping[PredicateKey, Predicate]) -> dict[PredicateKey, Predicate]:
    merged: dict[PredicateKey, Predicate] = {}
    for registry in registries:
        duplicates = merged.keys() & registry.keys()
        if duplicates:
            names = ", ".join(f"{complex_id}/{step}" for complex_id, step in sorted(duplicates))
            raise ValueError(f"duplicate complex predicate registrations: {names}")
        merged.update(registry)
    return merged


PREDICATE_REGISTRY = _merge_registries(
    OBJECT_MODIFIER_PREDICATES,
    RENDER_PREDICATES,
    MATERIAL_PREDICATES,
    GEOMETRY_NODE_PREDICATES,
    TIME_STATE_PREDICATES,
)
PREDICATE_PAIRS = frozenset(PREDICATE_REGISTRY)


def catalog_pairs(achievements: Iterable[dict[str, Any]]) -> frozenset[PredicateKey]:
    """Return the exact declared complex-id/step pairs from a catalog."""
    return frozenset(
        (achievement["complex_id"], step["check"])
        for achievement in achievements
        if achievement.get("check_type") == "complex"
        for step in achievement["steps"]
    )


def registry_bijection_errors(achievements: Iterable[dict[str, Any]]) -> tuple[str, ...]:
    """Report missing and orphan registrations relative to the catalog."""
    declared = catalog_pairs(achievements)
    errors = [
        *(f"missing: {complex_id}/{step}" for complex_id, step in sorted(declared - PREDICATE_PAIRS)),
        *(f"orphan: {complex_id}/{step}" for complex_id, step in sorted(PREDICATE_PAIRS - declared)),
    ]
    return tuple(errors)


def evaluate_predicate(
    complex_id: str,
    step_check: str,
    context: PredicateContext,
) -> PredicateResult:
    """Evaluate one registered pair without leaking malformed-state exceptions."""
    predicate = PREDICATE_REGISTRY.get((complex_id, step_check))
    if predicate is None:
        return PredicateResult(False)
    try:
        result = predicate(context)
    except Exception as error:  # noqa: BLE001 - Blender adapter reports and degrades to False.
        return PredicateResult(False, error=f"{type(error).__name__}: {error}")
    if isinstance(result, PredicateResult):
        return result
    return PredicateResult(bool(result))
