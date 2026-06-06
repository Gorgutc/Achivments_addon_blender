"""Offline-first sync models for the Achievements add-on.

Iteration 10 intentionally provides only pure planning primitives: queue
ordering, payload filtering, conflict resolution, and a disabled backend.
Runtime networking is not enabled by this module.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any

SYNC_DISABLED_BY_DEFAULT = True
SYNC_EXCLUDED_STATE_KEYS = frozenset({"pinned_ach_id"})
SOURCE_PRIORITY = {
    "local": 2,
    "remote": 1,
}


@dataclass(frozen=True)
class SyncChange:
    change_id: str
    entity: str
    entity_id: str
    operation: str
    payload: Mapping[str, Any]
    updated_at: int
    source: str = "local"

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", _freeze_payload(self.payload))


def _freeze_payload(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    return MappingProxyType({key: _freeze_value(value) for key, value in payload.items()})


def _freeze_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _freeze_payload(value)
    if isinstance(value, list | tuple):
        return tuple(_freeze_value(item) for item in value)
    if isinstance(value, set | frozenset):
        return tuple(sorted((_freeze_value(item) for item in value), key=repr))
    return value


@dataclass(frozen=True)
class ConflictDecision:
    winner: SyncChange
    loser: SyncChange
    reason: str


@dataclass(frozen=True)
class SyncBackendResult:
    status: str
    detail: str = ""
    processed: int = 0
    changes: tuple[SyncChange, ...] = ()


class SyncQueue:
    """Immutable sync queue with deterministic ordering and ID dedupe."""

    def __init__(self, changes: tuple[SyncChange, ...] | None = None):
        self._changes = tuple(changes or ())

    def enqueue(self, change: SyncChange) -> SyncQueue:
        if any(item.change_id == change.change_id for item in self._changes):
            return self
        return SyncQueue((*self._changes, change))

    def pending(self) -> tuple[SyncChange, ...]:
        return tuple(
            sorted(
                self._changes,
                key=lambda change: (
                    change.updated_at,
                    change.change_id,
                    change.entity,
                    change.entity_id,
                    change.operation,
                ),
            )
        )

    def without(self, change_id: str) -> SyncQueue:
        return SyncQueue(
            tuple(change for change in self._changes if change.change_id != change_id)
        )


class DisabledSyncBackend:
    """Backend placeholder that preserves offline-first behavior."""

    enabled = False

    def push(self, queue: SyncQueue) -> SyncBackendResult:
        return SyncBackendResult(
            status="disabled",
            detail="Sync backend is disabled by default.",
            processed=0,
            changes=queue.pending(),
        )

    def pull(self) -> SyncBackendResult:
        return SyncBackendResult(
            status="disabled",
            detail="Sync backend is disabled by default.",
            processed=0,
            changes=(),
        )


def sync_payload_from_state(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Return the sync-visible state payload with local UI state removed."""
    return {
        str(key): value
        for key, value in payload.items()
        if str(key) not in SYNC_EXCLUDED_STATE_KEYS
    }


def resolve_conflict(left: SyncChange, right: SyncChange) -> ConflictDecision:
    """Resolve two competing changes deterministically.

    Newer changes win. When timestamps are equal, local changes win over remote
    changes. If both sides still tie, lexical change ID order decides the winner.
    """
    if left.updated_at != right.updated_at:
        winner, loser = (left, right) if left.updated_at > right.updated_at else (right, left)
        return ConflictDecision(winner=winner, loser=loser, reason="latest_updated_at")

    left_priority = SOURCE_PRIORITY.get(left.source, 0)
    right_priority = SOURCE_PRIORITY.get(right.source, 0)
    if left_priority != right_priority:
        winner, loser = (left, right) if left_priority > right_priority else (right, left)
        return ConflictDecision(winner=winner, loser=loser, reason="source_priority")

    winner, loser = (left, right) if left.change_id <= right.change_id else (right, left)
    return ConflictDecision(winner=winner, loser=loser, reason="stable_change_id")
