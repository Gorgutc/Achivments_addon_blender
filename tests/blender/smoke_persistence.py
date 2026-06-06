from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ["ACHIEVEMENTS_ADDON_ROOT"])
ADDON_PATH = ROOT / "__init__.py"
MODULE_NAME = "achievements_blender_smoke_persistence_addon"
EXPECTED_TOP_KEYS = {
    "schema_version",
    "stats",
    "unlocked",
    "unlock_hashes",
    "rewards_claimed",
    "pinned_ach_id",
    "daily_sessions",
}
EXPECTED_STAT_KEYS = {
    "vertices_created",
    "vertices_deleted",
    "edges_created",
    "faces_created",
    "meshes_1000plus",
    "materials_applied",
    "time_spent",
    "renders_completed",
}


def fail(message: str) -> None:
    print(f"[smoke_persistence:FAIL] {message}")
    raise SystemExit(1)


def load_addon():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, ADDON_PATH)
    if spec is None or spec.loader is None:
        fail("cannot create module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def assert_temp_path(path: Path) -> None:
    expected_home = Path(os.environ["USERPROFILE"])
    if expected_home not in path.parents and path != expected_home:
        fail(f"path is outside temp home: {path}")


def main() -> None:
    module = load_addon()
    assert_temp_path(Path(module.DATA_FILE))

    module.register()
    try:
        module.stats.vertices_created = 12
        module.stats.edges_created = 3
        module.stats.faces_created = 2
        module.stats.renders_completed = 1
        module.stats.unlocked = {"first_vertex"}
        module.stats.unlock_hashes = {"first_vertex": module._make_unlock_hash("first_vertex")}
        module.stats.rewards_claimed = {"first_vertex"}
        module.stats.pinned_ach_id = "first_vertex"
        module.stats.daily_sessions = ["2026-05-30"]
        module.save_data()

        data_path = Path(module.DATA_FILE)
        assert_temp_path(data_path)
        data = json.loads(data_path.read_text(encoding="utf-8"))
        if set(data) != EXPECTED_TOP_KEYS:
            fail(f"unexpected top-level keys: {sorted(data)}")
        if data["schema_version"] != "1.0.0":
            fail(f"unexpected schema_version: {data['schema_version']}")
        if set(data["stats"]) != EXPECTED_STAT_KEYS:
            fail(f"unexpected stat keys: {sorted(data['stats'])}")

        module.stats.vertices_created = 0
        module.stats.unlocked = set()
        module.stats.unlock_hashes = {}
        module.stats.rewards_claimed = set()
        module.stats.pinned_ach_id = ""
        module.load_data()
        if module.stats.vertices_created != 12 or "first_vertex" not in module.stats.unlocked:
            fail("load_data did not restore saved values")

        data.pop("schema_version", None)
        data["unlock_hashes"] = {}
        data_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        module.stats.unlock_hashes = {}
        module.load_data()
        if "first_vertex" not in module.stats.unlock_hashes:
            fail("load_data did not migrate missing unlock hash")
        if not module.ach_persistence.backup_path(data_path).is_file():
            fail("migration save did not create backup file")
        migrated = json.loads(data_path.read_text(encoding="utf-8"))
        if migrated.get("schema_version") != "1.0.0":
            fail("load_data did not persist schema_version migration")

        data_path.write_text("{broken json", encoding="utf-8")
        module.stats.vertices_created = 999
        module.load_data()
        corrupt_files = list(data_path.parent.glob("achievements_data.json.corrupt*"))
        if len(corrupt_files) != 1:
            fail(f"corrupt JSON was not quarantined: {corrupt_files}")
        recovered = json.loads(data_path.read_text(encoding="utf-8"))
        if recovered.get("schema_version") != "1.0.0":
            fail("corrupt recovery did not recreate current schema")
        if module.stats.vertices_created != 0:
            fail("corrupt recovery did not reset stats to default")
    finally:
        module.unregister()

    print("[smoke_persistence:PASS] JSON schema, load, save, migration, and corrupt recovery clean")


if __name__ == "__main__":
    main()
