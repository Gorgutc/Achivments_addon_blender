"""Pure reward planning helpers for the Achievements add-on.

The module decides whether a reward can be applied and which Blender-side
operation is needed. Actual ``bpy`` asset linking and fallback creation stay in
the root runtime operator.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ASSET_REWARD_TYPES = {"material", "mesh", "geo_nodes"}
PLANNED_REWARD_TYPES = ASSET_REWARD_TYPES | {"tutorial"}


@dataclass(frozen=True)
class RewardSpec:
    achievement_id: str
    reward_type: str
    name: str = ""
    description: str = ""
    blend_file: str = ""
    url: str = ""


@dataclass(frozen=True)
class RewardAction:
    kind: str
    reward_type: str = ""
    name: str = ""
    description: str = ""
    blend_file: str = ""
    asset_path: Path | None = None
    url: str = ""


@dataclass(frozen=True)
class RewardResult:
    status: str
    action: RewardAction
    report: tuple[str, str] | None = None
    claim_after_apply: bool = False

    @property
    def mark_claimed(self) -> bool:
        """Compatibility alias; claims are committed only after confirmed apply."""
        return self.claim_after_apply


@dataclass(frozen=True)
class RewardManifest:
    specs: dict[str, RewardSpec]
    none_ids: set[str] = field(default_factory=set)

    @classmethod
    def from_achievements(cls, achievements: list[dict[str, Any]]) -> RewardManifest:
        specs: dict[str, RewardSpec] = {}
        none_ids: set[str] = set()
        for achievement in achievements:
            achievement_id = achievement["id"]
            reward_type = achievement.get("reward_type", "none")
            reward_data = achievement.get("reward_data", {})
            if reward_type == "none":
                none_ids.add(achievement_id)
                continue
            if reward_type not in PLANNED_REWARD_TYPES:
                continue
            specs[achievement_id] = RewardSpec(
                achievement_id=achievement_id,
                reward_type=reward_type,
                name=str(reward_data.get("name", "")),
                description=str(reward_data.get("description", "")),
                blend_file=str(reward_data.get("blend_file", "")),
                url=str(reward_data.get("url", "")),
            )
        return cls(specs=specs, none_ids=none_ids)

    def spec_for(self, achievement_id: str) -> RewardSpec | None:
        return self.specs.get(achievement_id)

    def asset_specs_by_type(self, reward_type: str) -> list[RewardSpec]:
        return [
            spec for spec in self.specs.values()
            if spec.reward_type == reward_type and reward_type in ASSET_REWARD_TYPES
        ]

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        for spec in self.specs.values():
            if spec.reward_type == "tutorial":
                if not spec.url:
                    errors.append(f"{spec.achievement_id}: missing url")
                continue
            if spec.reward_type in ASSET_REWARD_TYPES:
                for key in ("name", "description", "blend_file"):
                    if not getattr(spec, key):
                        errors.append(f"{spec.achievement_id}: missing {key}")
        return errors


class RewardVerifier:
    def __init__(self, verify_unlock: Callable[[str, str], bool]) -> None:
        self._verify_unlock = verify_unlock

    def can_apply(self, achievement_id: str, stats: Any) -> tuple[bool, tuple[str, str] | None]:
        if achievement_id not in getattr(stats, "unlocked", set()):
            return False, ("WARNING", "Achievement not earned")
        stored_hash = getattr(stats, "unlock_hashes", {}).get(achievement_id, "")
        if not self._verify_unlock(achievement_id, stored_hash):
            return False, ("ERROR", "Unlock verification failed")
        return True, None


class AssetCache:
    def __init__(self, *, exists: Callable[[Path], bool] | None = None) -> None:
        self._exists = exists or Path.exists
        self._cache: dict[Path, bool] = {}

    def exists(self, path: Path) -> bool:
        if path in self._cache:
            return True
        exists = bool(self._exists(path))
        if exists:
            self._cache[path] = True
        return exists


class RewardManager:
    def __init__(
        self,
        manifest: RewardManifest,
        *,
        data_dir: str | Path,
        asset_cache: AssetCache | None = None,
    ) -> None:
        self.manifest = manifest
        self.data_dir = Path(data_dir)
        self.asset_cache = asset_cache or AssetCache()

    def asset_path(self, spec: RewardSpec) -> Path:
        return self.data_dir / spec.blend_file

    def resolve(
        self,
        achievement_id: str,
        stats: Any,
        verifier: RewardVerifier,
    ) -> RewardResult:
        spec = self.manifest.spec_for(achievement_id)
        is_none_reward = achievement_id in self.manifest.none_ids
        if spec is None and not is_none_reward:
            return RewardResult(
                status="cancelled",
                action=RewardAction("cancelled"),
                report=("WARNING", "Achievement not found"),
            )

        can_apply, report = verifier.can_apply(achievement_id, stats)
        if not can_apply:
            return RewardResult(
                status="cancelled",
                action=RewardAction("cancelled"),
                report=report,
            )

        if is_none_reward:
            return RewardResult(
                status="finished",
                action=RewardAction("none"),
                report=("INFO", "No reward"),
            )

        if spec is None:
            return RewardResult(
                status="cancelled",
                action=RewardAction("cancelled"),
                report=("WARNING", "Achievement not found"),
            )

        if spec.reward_type == "tutorial":
            return RewardResult(
                status="finished",
                action=RewardAction("open_tutorial", url=spec.url),
            )

        asset_path = self.asset_path(spec)
        action_kind = "link_asset" if self.asset_cache.exists(asset_path) else _fallback_action(
            spec.reward_type
        )
        return RewardResult(
            status="finished",
            action=RewardAction(
                kind=action_kind,
                reward_type=spec.reward_type,
                name=spec.name,
                description=spec.description,
                blend_file=spec.blend_file,
                asset_path=asset_path,
            ),
            report=("INFO", f"Reward: {spec.description}"),
            claim_after_apply=True,
        )


def _fallback_action(reward_type: str) -> str:
    if reward_type == "material":
        return "placeholder_material"
    if reward_type == "mesh":
        return "placeholder_mesh"
    if reward_type == "geo_nodes":
        return "placeholder_geo_nodes"
    return "none"
