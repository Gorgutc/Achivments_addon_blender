from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def make_stats(**overrides):
    values = {
        "vertices_created": 0,
        "vertices_deleted": 0,
        "edges_created": 0,
        "faces_created": 0,
        "meshes_1000plus": 0,
        "materials_applied": 0,
        "time_spent": 0,
        "renders_completed": 0,
        "unlocked": set(),
        "unlock_hashes": {},
        "rewards_claimed": set(),
        "pinned_ach_id": "",
        "daily_sessions": [],
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def hash_for(achievement_id: str) -> str:
    return f"hash-{achievement_id}"


def test_persistence_module_is_safe_to_import():
    persistence = ROOT / "achievements" / "persistence.py"
    assert persistence.is_file(), "missing Iteration 6 persistence module"

    text = persistence.read_text(encoding="utf-8")
    assert "import bpy" not in text
    assert "BlenderAchievements" not in text
    assert "Path.home()" not in text

    from achievements import persistence as ach_persistence

    assert ach_persistence.SCHEMA_VERSION == "1.0.0"
    assert ach_persistence.PersistenceState


def test_legacy_payload_migrates_idempotently_and_generates_missing_hashes():
    from achievements import persistence as ach_persistence

    legacy = {
        "stats": {"vertices_created": 12, "renders_completed": 1},
        "unlocked": ["first_vertex"],
        "unlock_hashes": {},
        "rewards_claimed": ["first_vertex"],
        "pinned_ach_id": "first_vertex",
        "daily_sessions": ["2026-06-01"],
    }

    migrated, first_report = ach_persistence.normalize_payload(legacy, make_unlock_hash=hash_for)
    remigrated, second_report = ach_persistence.normalize_payload(
        migrated, make_unlock_hash=hash_for
    )

    assert first_report.migrated
    assert not second_report.migrated
    assert migrated == remigrated
    assert migrated["schema_version"] == ach_persistence.SCHEMA_VERSION
    assert migrated["stats"] == {
        "vertices_created": 12,
        "vertices_deleted": 0,
        "edges_created": 0,
        "faces_created": 0,
        "meshes_1000plus": 0,
        "materials_applied": 0,
        "time_spent": 0,
        "renders_completed": 1,
    }
    assert migrated["unlock_hashes"] == {"first_vertex": "hash-first_vertex"}


def test_invalid_payload_values_are_sanitized_and_deduplicated():
    from achievements import persistence as ach_persistence

    payload = {
        "schema_version": ach_persistence.SCHEMA_VERSION,
        "stats": {
            "vertices_created": "7",
            "vertices_deleted": None,
            "edges_created": "bad",
            "faces_created": 2.9,
        },
        "unlocked": ["b", 3, "a", "a"],
        "unlock_hashes": {"b": 22},
        "rewards_claimed": ["reward_b", "reward_a", "reward_a", 5],
        "pinned_ach_id": 123,
        "daily_sessions": ["2026-06-01", None, "2026-06-02"],
    }

    normalized, report = ach_persistence.normalize_payload(payload, make_unlock_hash=hash_for)

    assert report.migrated
    assert normalized["stats"]["vertices_created"] == 7
    assert normalized["stats"]["vertices_deleted"] == 0
    assert normalized["stats"]["edges_created"] == 0
    assert normalized["stats"]["faces_created"] == 2
    assert normalized["unlocked"] == ["a", "b"]
    assert normalized["unlock_hashes"] == {"b": "22"}
    assert normalized["rewards_claimed"] == ["reward_a", "reward_b"]
    assert normalized["pinned_ach_id"] == ""
    assert normalized["daily_sessions"] == ["2026-06-01", "2026-06-02"]


def test_payload_round_trip_from_stats_uses_current_schema():
    from achievements import persistence as ach_persistence

    stats = make_stats(
        vertices_created=7,
        unlocked={"first_vertex"},
        unlock_hashes={"first_vertex": "hash-first_vertex"},
        rewards_claimed={"first_vertex"},
        pinned_ach_id="first_vertex",
        daily_sessions=["2026-06-06"],
    )

    payload = ach_persistence.payload_from_stats(stats)
    restored = make_stats()
    report = ach_persistence.apply_payload_to_stats(restored, payload, make_unlock_hash=hash_for)

    assert payload["schema_version"] == ach_persistence.SCHEMA_VERSION
    assert not report.migrated
    assert restored.vertices_created == 7
    assert restored.unlocked == {"first_vertex"}
    assert restored.unlock_hashes == {"first_vertex": "hash-first_vertex"}
    assert restored.rewards_claimed == {"first_vertex"}
    assert restored.pinned_ach_id == "first_vertex"
    assert restored.daily_sessions == ["2026-06-06"]


def test_current_schema_missing_or_forged_hash_is_not_backfilled():
    from achievements import persistence as ach_persistence

    current = ach_persistence.default_payload()
    current["unlocked"] = ["forged", "missing"]
    current["unlock_hashes"] = {"forged": "not-a-valid-marker"}

    normalized, report = ach_persistence.normalize_payload(
        current, make_unlock_hash=hash_for
    )

    assert not report.migrated
    assert normalized["unlock_hashes"] == {"forged": "not-a-valid-marker"}


def test_integrity_marker_survives_persistence_round_trip_without_repair():
    from achievements import persistence as ach_persistence
    from achievements.integrity import make_unlock_hash

    marker = make_unlock_hash("first_vertex", "junior")
    stats = make_stats(
        unlocked={"first_vertex"},
        unlock_hashes={"first_vertex": marker},
    )

    payload = ach_persistence.payload_from_stats(stats)
    restored = make_stats()
    report = ach_persistence.apply_payload_to_stats(
        restored, payload, make_unlock_hash=lambda achievement_id: "must-not-be-used"
    )

    assert not report.migrated
    assert restored.unlock_hashes == {"first_vertex": marker}


def test_atomic_write_uses_same_directory_replace_backup_and_leaves_no_temp_files(
    tmp_path, monkeypatch
):
    from achievements import persistence as ach_persistence

    data_file = tmp_path / "achievements_data.json"
    ach_persistence.atomic_write_json(data_file, ach_persistence.default_payload())
    payload = ach_persistence.default_payload()
    payload["stats"]["vertices_created"] = 5
    calls = []
    real_replace = os.replace

    def capture_replace(src, dst):
        calls.append((Path(src), Path(dst)))
        real_replace(src, dst)

    monkeypatch.setattr(ach_persistence.os, "replace", capture_replace)

    ach_persistence.atomic_write_json(data_file, payload)

    assert calls
    temp_path, target_path = calls[-1]
    assert temp_path.parent == tmp_path
    assert target_path == data_file
    assert json.loads(data_file.read_text(encoding="utf-8"))["stats"]["vertices_created"] == 5
    assert ach_persistence.backup_path(data_file).is_file()
    assert list(tmp_path.glob("*.tmp")) == []


def test_atomic_write_cleans_temp_and_preserves_old_target_when_replace_fails(
    tmp_path, monkeypatch
):
    from achievements import persistence as ach_persistence

    data_file = tmp_path / "achievements_data.json"
    data_file.write_text('{"old": true}', encoding="utf-8")
    payload = ach_persistence.default_payload()

    def fail_replace(src, dst):
        raise OSError("replace failed")

    monkeypatch.setattr(ach_persistence.os, "replace", fail_replace)

    with pytest.raises(OSError, match="replace failed"):
        ach_persistence.atomic_write_json(data_file, payload)

    assert data_file.read_text(encoding="utf-8") == '{"old": true}'
    assert ach_persistence.backup_path(data_file).is_file()
    assert list(tmp_path.glob("*.tmp")) == []


def test_corrupt_json_is_quarantined_and_recovered(tmp_path):
    from achievements import persistence as ach_persistence

    data_file = tmp_path / "achievements_data.json"
    data_file.write_text("{broken json", encoding="utf-8")

    payload, report = ach_persistence.load_payload(data_file, make_unlock_hash=hash_for)

    assert report.recovered_corrupt
    assert report.corrupt_path is not None
    assert report.corrupt_path.name.startswith("achievements_data.json.corrupt")
    assert report.corrupt_path.read_text(encoding="utf-8") == "{broken json"
    assert data_file.is_file()
    assert json.loads(data_file.read_text(encoding="utf-8"))["schema_version"] == "1.0.0"
    assert payload == ach_persistence.default_payload()
