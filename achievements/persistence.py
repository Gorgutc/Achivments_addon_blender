"""Pure JSON persistence helpers for the Achievements add-on.

This module stays free of ``bpy`` imports and user-home assumptions. The root
Blender entrypoint passes concrete paths and hash callbacks at runtime.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "1.0.0"
STAT_FIELDS = (
    "vertices_created",
    "vertices_deleted",
    "edges_created",
    "faces_created",
    "meshes_1000plus",
    "materials_applied",
    "time_spent",
    "renders_completed",
)


@dataclass(frozen=True)
class PersistenceReport:
    migrated: bool = False
    missing: bool = False
    recovered_corrupt: bool = False
    corrupt_path: Path | None = None


@dataclass(frozen=True)
class PersistenceState:
    schema_version: str
    stats: dict[str, int]
    unlocked: tuple[str, ...]
    unlock_hashes: dict[str, str]
    rewards_claimed: tuple[str, ...]
    pinned_ach_id: str
    daily_sessions: tuple[str, ...]

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "stats": dict(self.stats),
            "unlocked": list(self.unlocked),
            "unlock_hashes": dict(self.unlock_hashes),
            "rewards_claimed": list(self.rewards_claimed),
            "pinned_ach_id": self.pinned_ach_id,
            "daily_sessions": list(self.daily_sessions),
        }


def default_payload() -> dict[str, Any]:
    return PersistenceState(
        schema_version=SCHEMA_VERSION,
        stats={field: 0 for field in STAT_FIELDS},
        unlocked=(),
        unlock_hashes={},
        rewards_claimed=(),
        pinned_ach_id="",
        daily_sessions=(),
    ).to_payload()


def ensure_data_dirs(data_dir: str | Path) -> None:
    base = Path(data_dir)
    base.mkdir(parents=True, exist_ok=True)
    (base / "textures").mkdir(parents=True, exist_ok=True)
    (base / "rewards").mkdir(parents=True, exist_ok=True)


def _as_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _as_str_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str)]


def _as_str_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(key): str(item) for key, item in value.items()}


def normalize_payload(
    raw: Any,
    *,
    make_unlock_hash,
) -> tuple[dict[str, Any], PersistenceReport]:
    state, report = state_from_payload(raw, make_unlock_hash=make_unlock_hash)
    return state.to_payload(), report


def state_from_payload(raw: Any, *, make_unlock_hash) -> tuple[PersistenceState, PersistenceReport]:
    if not isinstance(raw, dict):
        return (
            PersistenceState(
                schema_version=SCHEMA_VERSION,
                stats={field: 0 for field in STAT_FIELDS},
                unlocked=(),
                unlock_hashes={},
                rewards_claimed=(),
                pinned_ach_id="",
                daily_sessions=(),
            ),
            PersistenceReport(migrated=True),
        )

    stats_payload = {field: 0 for field in STAT_FIELDS}
    migrated = raw.get("schema_version") != SCHEMA_VERSION
    raw_stats = raw.get("stats", {})
    if not isinstance(raw_stats, dict):
        raw_stats = {}
        migrated = True

    for field in STAT_FIELDS:
        value = _as_int(raw_stats.get(field, 0))
        stats_payload[field] = value
        if raw_stats.get(field, 0) != value:
            migrated = True

    unlocked = _as_str_list(raw.get("unlocked", []))
    rewards_claimed = _as_str_list(raw.get("rewards_claimed", []))
    daily_sessions = _as_str_list(raw.get("daily_sessions", []))
    unlock_hashes = _as_str_dict(raw.get("unlock_hashes", {}))

    for achievement_id in unlocked:
        if achievement_id not in unlock_hashes:
            unlock_hashes[achievement_id] = make_unlock_hash(achievement_id)
            migrated = True

    pinned_ach_id = raw.get("pinned_ach_id", "")
    state = PersistenceState(
        schema_version=SCHEMA_VERSION,
        stats=stats_payload,
        unlocked=tuple(sorted(set(unlocked))),
        unlock_hashes=unlock_hashes,
        rewards_claimed=tuple(sorted(set(rewards_claimed))),
        pinned_ach_id=pinned_ach_id if isinstance(pinned_ach_id, str) else "",
        daily_sessions=tuple(daily_sessions),
    )

    payload = state.to_payload()
    if raw.get("schema_version") == SCHEMA_VERSION and raw != payload:
        migrated = True
    return state, PersistenceReport(migrated=migrated)


def payload_from_stats(stats: Any) -> dict[str, Any]:
    payload = default_payload()
    payload["stats"] = {field: _as_int(getattr(stats, field, 0)) for field in STAT_FIELDS}
    payload["unlocked"] = sorted(str(item) for item in getattr(stats, "unlocked", set()))
    payload["unlock_hashes"] = dict(getattr(stats, "unlock_hashes", {}))
    payload["rewards_claimed"] = sorted(
        str(item) for item in getattr(stats, "rewards_claimed", set())
    )
    payload["pinned_ach_id"] = getattr(stats, "pinned_ach_id", "") or ""
    payload["daily_sessions"] = list(getattr(stats, "daily_sessions", []))
    return payload


def apply_payload_to_stats(stats: Any, payload: Any, *, make_unlock_hash) -> PersistenceReport:
    normalized, report = normalize_payload(payload, make_unlock_hash=make_unlock_hash)
    for field in STAT_FIELDS:
        setattr(stats, field, normalized["stats"][field])
    stats.unlocked = set(normalized["unlocked"])
    stats.unlock_hashes = normalized["unlock_hashes"]
    stats.rewards_claimed = set(normalized["rewards_claimed"])
    stats.pinned_ach_id = normalized["pinned_ach_id"]
    stats.daily_sessions = normalized["daily_sessions"]
    return report


def backup_path(path: str | Path) -> Path:
    target = Path(path)
    return target.with_name(f"{target.name}.bak")


def atomic_write_json(path: str | Path, payload: dict[str, Any], *, backup: bool = True) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f"{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_path = Path(handle.name)
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.flush()
            os.fsync(handle.fileno())
        if backup and target.exists():
            shutil.copy2(target, backup_path(target))
        os.replace(temp_path, target)
        temp_path = None
    finally:
        if temp_path is not None and temp_path.exists():
            temp_path.unlink()


def _next_corrupt_path(path: Path) -> Path:
    candidate = path.with_name(f"{path.name}.corrupt")
    if not candidate.exists():
        return candidate
    index = 1
    while True:
        candidate = path.with_name(f"{path.name}.corrupt.{index}")
        if not candidate.exists():
            return candidate
        index += 1


def load_payload(path: str | Path, *, make_unlock_hash) -> tuple[dict[str, Any], PersistenceReport]:
    source = Path(path)
    if not source.exists():
        return default_payload(), PersistenceReport(missing=True)

    try:
        raw = json.loads(source.read_text(encoding="utf-8"))
    except Exception:
        corrupt_path = _next_corrupt_path(source)
        os.replace(source, corrupt_path)
        payload = default_payload()
        atomic_write_json(source, payload)
        return payload, PersistenceReport(recovered_corrupt=True, corrupt_path=corrupt_path)

    return normalize_payload(raw, make_unlock_hash=make_unlock_hash)
