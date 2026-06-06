from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def make_stats(**overrides):
    values = {
        "unlocked": set(),
        "unlock_hashes": {},
        "rewards_claimed": set(),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def sample_achievements():
    return [
        {
            "id": "no_reward",
            "reward_type": "none",
            "reward_data": {},
        },
        {
            "id": "tutorial_reward",
            "reward_type": "tutorial",
            "reward_data": {"url": "https://example.com/tutorial"},
        },
        {
            "id": "material_reward",
            "reward_type": "material",
            "reward_data": {
                "name": "ACH_TestMat",
                "description": "Test material",
                "blend_file": "rewards/test_mat.blend",
            },
        },
        {
            "id": "mesh_reward",
            "reward_type": "mesh",
            "reward_data": {
                "name": "ACH_TestMesh",
                "description": "Test mesh",
                "blend_file": "rewards/test_mesh.blend",
            },
        },
        {
            "id": "geo_reward",
            "reward_type": "geo_nodes",
            "reward_data": {
                "name": "ACH_TestGeo",
                "description": "Test geo",
                "blend_file": "rewards/test_geo.blend",
            },
        },
    ]


def test_rewards_module_is_safe_to_import_and_exposes_layer_types():
    rewards_path = ROOT / "achievements" / "rewards.py"
    assert rewards_path.is_file(), "missing Iteration 8 rewards module"

    text = rewards_path.read_text(encoding="utf-8")
    assert "import bpy" not in text
    assert "BlenderAchievements" not in text
    assert "Path.home()" not in text

    from achievements import rewards

    assert rewards.RewardSpec
    assert rewards.RewardAction
    assert rewards.RewardResult
    assert rewards.RewardManifest
    assert rewards.RewardVerifier
    assert rewards.AssetCache
    assert rewards.RewardManager


def test_reward_manifest_preserves_catalog_reward_fields_and_validates_assets():
    from achievements import rewards

    manifest = rewards.RewardManifest.from_achievements(sample_achievements())

    assert set(manifest.specs) == {
        "tutorial_reward",
        "material_reward",
        "mesh_reward",
        "geo_reward",
    }
    assert manifest.specs["material_reward"] == rewards.RewardSpec(
        achievement_id="material_reward",
        reward_type="material",
        name="ACH_TestMat",
        description="Test material",
        blend_file="rewards/test_mat.blend",
        url="",
    )
    assert manifest.asset_specs_by_type("material")[0].achievement_id == "material_reward"
    assert manifest.asset_specs_by_type("mesh")[0].achievement_id == "mesh_reward"
    assert manifest.asset_specs_by_type("geo_nodes")[0].achievement_id == "geo_reward"

    broken = rewards.RewardManifest.from_achievements(
        [{"id": "broken", "reward_type": "material", "reward_data": {"name": "OnlyName"}}]
    )
    assert broken.validation_errors() == [
        "broken: missing description",
        "broken: missing blend_file",
    ]


def test_reward_manager_plans_access_checks_and_non_claim_rewards(tmp_path):
    from achievements import rewards

    manifest = rewards.RewardManifest.from_achievements(sample_achievements())
    manager = rewards.RewardManager(manifest, data_dir=tmp_path)
    good_stats = make_stats(
        unlocked={"tutorial_reward", "no_reward"},
        unlock_hashes={"tutorial_reward": "ok", "no_reward": "ok"},
    )
    verifier = rewards.RewardVerifier(lambda ach_id, stored_hash: stored_hash == "ok")

    missing = manager.resolve("missing", good_stats, verifier)
    unearned = manager.resolve("material_reward", good_stats, verifier)
    bad_hash = manager.resolve(
        "tutorial_reward",
        make_stats(unlocked={"tutorial_reward"}, unlock_hashes={"tutorial_reward": "bad"}),
        verifier,
    )
    tutorial = manager.resolve("tutorial_reward", good_stats, verifier)
    none_reward = manager.resolve("no_reward", good_stats, verifier)

    assert missing.status == "cancelled"
    assert missing.report == ("WARNING", "Achievement not found")
    assert unearned.status == "cancelled"
    assert unearned.report == ("WARNING", "Achievement not earned")
    assert bad_hash.status == "cancelled"
    assert bad_hash.report == ("ERROR", "Unlock verification failed")
    assert tutorial.status == "finished"
    assert tutorial.action == rewards.RewardAction("open_tutorial", url="https://example.com/tutorial")
    assert not tutorial.mark_claimed
    assert none_reward.status == "finished"
    assert none_reward.action == rewards.RewardAction("none")
    assert not none_reward.mark_claimed


def test_reward_manager_plans_asset_link_or_fallback_with_cached_existence(tmp_path):
    from achievements import rewards

    calls = []

    def exists(path: Path) -> bool:
        calls.append(path)
        return path.name == "test_mesh.blend"

    manifest = rewards.RewardManifest.from_achievements(sample_achievements())
    cache = rewards.AssetCache(exists=exists)
    manager = rewards.RewardManager(manifest, data_dir=tmp_path, asset_cache=cache)
    stats = make_stats(
        unlocked={"material_reward", "mesh_reward", "geo_reward"},
        unlock_hashes={"material_reward": "ok", "mesh_reward": "ok", "geo_reward": "ok"},
    )
    verifier = rewards.RewardVerifier(lambda _ach_id, stored_hash: stored_hash == "ok")

    material = manager.resolve("material_reward", stats, verifier)
    mesh = manager.resolve("mesh_reward", stats, verifier)
    mesh_again = manager.resolve("mesh_reward", stats, verifier)
    geo = manager.resolve("geo_reward", stats, verifier)

    assert material.status == "finished"
    assert material.mark_claimed
    assert material.action.kind == "placeholder_material"
    assert material.action.asset_path == tmp_path / "rewards" / "test_mat.blend"
    assert material.action.name == "ACH_TestMat"

    assert mesh.action.kind == "link_asset"
    assert mesh.action.reward_type == "mesh"
    assert mesh.action.asset_path == tmp_path / "rewards" / "test_mesh.blend"
    assert mesh_again.action == mesh.action

    assert geo.action.kind == "placeholder_geo_nodes"
    assert geo.mark_claimed
    assert calls.count(tmp_path / "rewards" / "test_mesh.blend") == 1


def test_asset_cache_rechecks_missing_assets_so_late_files_can_link(tmp_path):
    from achievements import rewards

    calls = []
    available_assets = set()
    asset_path = tmp_path / "rewards" / "test_mat.blend"

    def exists(path: Path) -> bool:
        calls.append(path)
        return path in available_assets

    manifest = rewards.RewardManifest.from_achievements(sample_achievements())
    cache = rewards.AssetCache(exists=exists)
    manager = rewards.RewardManager(manifest, data_dir=tmp_path, asset_cache=cache)
    stats = make_stats(
        unlocked={"material_reward"},
        unlock_hashes={"material_reward": "ok"},
    )
    verifier = rewards.RewardVerifier(lambda _ach_id, stored_hash: stored_hash == "ok")

    missing = manager.resolve("material_reward", stats, verifier)
    available_assets.add(asset_path)
    linked = manager.resolve("material_reward", stats, verifier)

    assert missing.action.kind == "placeholder_material"
    assert linked.action.kind == "link_asset"
    assert calls.count(asset_path) == 2
