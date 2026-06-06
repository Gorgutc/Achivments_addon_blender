from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def make_change(change_id, *, updated_at=1, source="local", payload=None):
    from achievements import sync

    return sync.SyncChange(
        change_id=change_id,
        entity="achievement",
        entity_id="first_vertex",
        operation="update",
        payload=payload or {"unlocked": ["first_vertex"]},
        updated_at=updated_at,
        source=source,
    )


def test_sync_module_is_safe_to_import():
    sync_module = ROOT / "achievements" / "sync.py"
    assert sync_module.is_file(), "missing Iteration 10 sync module"

    text = sync_module.read_text(encoding="utf-8")
    forbidden_terms = (
        "import bpy",
        "BlenderAchievements",
        "Path.home()",
        "DATA_FILE",
        "import socket",
        "import requests",
        "import urllib",
        "import http.client",
        "import httpx",
        "import aiohttp",
        "urlopen",
    )
    for term in forbidden_terms:
        assert term not in text

    from achievements import sync

    assert sync.SYNC_DISABLED_BY_DEFAULT is True
    assert "pinned_ach_id" in sync.SYNC_EXCLUDED_STATE_KEYS


def test_default_backend_is_disabled_and_has_no_transport_hook():
    from achievements import sync

    backend = sync.DisabledSyncBackend()
    queue = sync.SyncQueue().enqueue(make_change("unlock-first"))

    push_result = backend.push(queue)
    pull_result = backend.pull()

    assert backend.enabled is False
    assert not hasattr(backend, "_transport")
    assert push_result.status == "disabled"
    assert pull_result.status == "disabled"
    assert push_result.processed == 0
    assert pull_result.changes == ()


def test_sync_queue_is_deterministic_and_deduplicates_by_change_id():
    from achievements import sync

    queue = (
        sync.SyncQueue()
        .enqueue(make_change("later", updated_at=20))
        .enqueue(make_change("earlier", updated_at=10))
        .enqueue(make_change("earlier", updated_at=30, payload={"unlocked": ["duplicate"]}))
    )

    pending = queue.pending()

    assert [change.change_id for change in pending] == ["earlier", "later"]
    assert pending[0].updated_at == 10
    assert queue.without("earlier").pending() == (make_change("later", updated_at=20),)


def test_sync_change_snapshots_mutable_payloads():
    from achievements import sync

    payload = {"unlocked": ["first_vertex"]}
    change = make_change("mutable-payload", payload=payload)
    queue = sync.SyncQueue().enqueue(change)

    payload["unlocked"].append("mutated")
    payload["extra"] = True

    pending = queue.pending()[0]
    assert pending.payload == {"unlocked": ("first_vertex",)}


def test_sync_change_recursively_freezes_payloads_and_sorts_sets():
    payload = {
        "stats": {"vertices_created": 1},
        "unlocked": {"b", "a"},
        "nested": {"items": [{"id": "first_vertex"}]},
    }
    change = make_change("nested-freeze", payload=payload)

    payload["stats"]["vertices_created"] = 99
    payload["unlocked"].add("c")
    payload["nested"]["items"][0]["id"] = "mutated"

    assert change.payload["stats"]["vertices_created"] == 1
    assert change.payload["unlocked"] == ("a", "b")
    assert change.payload["nested"]["items"][0]["id"] == "first_vertex"
    with pytest.raises(TypeError):
        change.payload["stats"] = {}
    with pytest.raises(TypeError):
        change.payload["stats"]["vertices_created"] = 2


def test_pinned_ui_state_is_excluded_from_sync_payload():
    from achievements import sync

    payload = {
        "schema_version": "1.0.0",
        "stats": {"vertices_created": 5},
        "unlocked": ["first_vertex"],
        "rewards_claimed": [],
        "pinned_ach_id": "first_vertex",
        "daily_sessions": ["2026-06-06"],
    }

    sync_payload = sync.sync_payload_from_state(payload)

    assert sync_payload == {
        "schema_version": "1.0.0",
        "stats": {"vertices_created": 5},
        "unlocked": ["first_vertex"],
        "rewards_claimed": [],
        "daily_sessions": ["2026-06-06"],
    }


def test_default_persistence_payload_keeps_schema_keys_except_pinned_state():
    from achievements import persistence, sync

    payload = persistence.default_payload()

    assert sync.sync_payload_from_state(payload) == {
        key: value for key, value in payload.items() if key != "pinned_ach_id"
    }
    assert "unlock_hashes" in sync.sync_payload_from_state(payload)
    assert "pinned_ach_id" not in sync.sync_payload_from_state(payload)


def test_sync_stub_is_not_wired_into_root_runtime_yet():
    root_text = (ROOT / "__init__.py").read_text(encoding="utf-8")

    assert "achievements.sync" not in root_text
    assert "from achievements import sync" not in root_text
    assert "sync_payload_from_state" not in root_text
    assert "DisabledSyncBackend" not in root_text


def test_conflict_policy_is_deterministic_offline_first():
    from achievements import sync

    older_local = make_change("local-old", updated_at=10, source="local")
    newer_remote = make_change("remote-new", updated_at=20, source="remote")
    same_time_local = make_change("local-same", updated_at=30, source="local")
    same_time_remote = make_change("remote-same", updated_at=30, source="remote")
    same_priority_a = make_change("a-change", updated_at=40, source="local")
    same_priority_b = make_change("b-change", updated_at=40, source="local")

    assert sync.resolve_conflict(older_local, newer_remote).winner == newer_remote

    offline_first = sync.resolve_conflict(same_time_local, same_time_remote)
    assert offline_first.winner == same_time_local
    assert offline_first.reason == "source_priority"

    stable_tiebreaker = sync.resolve_conflict(same_priority_b, same_priority_a)
    assert stable_tiebreaker.winner == same_priority_a
    assert stable_tiebreaker.reason == "stable_change_id"
