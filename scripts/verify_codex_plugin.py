from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN_NAME = "achievements-blender-codex"
PLUGIN_ROOT = ROOT / "plugins" / PLUGIN_NAME
SKILL_ROOT = PLUGIN_ROOT / "skills"
REQUIRED_SKILLS = [
    "achievements-bootstrap",
    "achievements-addon-rules",
    "achievements-audit-orchestrator",
    "achievements-context-keeper",
    "achievements-frozen-decisions",
    "achievements-instruction-drift",
    "achievements-quality-tooling",
    "achievements-quality-gate",
    "achievements-blender-runtime",
    "achievements-registration-lifecycle",
    "achievements-data-persistence",
    "achievements-packaging",
    "achievements-ship-review",
]
REQUIRED_AGENTS = [
    "tech_stack_cartographer",
    "addon_runtime_mapper",
    "blender_api_compat_guardian",
    "registration_lifecycle_guardian",
    "data_persistence_guardian",
    "quality_tooling_architect",
    "code_quality_guardian",
    "code_deadwood_auditor",
    "instruction_drift_auditor",
    "verification_reviewer",
    "blender_ui_visual_qa",
]
REQUIRED_DOCS = [
    "docs/agent/architecture.md",
    "docs/agent/frozen-application-contract.md",
    "docs/agent/orchestration.md",
    "docs/agent/verification.md",
    "docs/agent/quality-tooling.md",
    "docs/agent/frozen-decisions.md",
    "docs/agent/code-review.md",
    "docs/agent/packaging-release.md",
    "docs/agent/archive-policy.md",
    "docs/agent/adrs/0001-codex-infra-port.md",
    "docs/agent/adrs/0002-retire-legacy-runtime-duplicate.md",
    "docs/agent/adrs/0003-safe-extension-removal-and-render-events.md",
    "docs/agent/adrs/0004-extension-namespace-and-files-permission.md",
    "docs/agent/adrs/0005-active-time-monotonic-window.md",
    "docs/agent/adrs/0006-xp-level-reachability.md",
    "docs/agent/adrs/0007-reward-claim-atomicity.md",
    "docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md",
    "docs/handoff/iteration-handoff-template.md",
    "docs/handoff/current.md",
]
HISTORICAL_DOCS = {
    "docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md",
}
PREDICATE_COMMAND = "uv run python scripts/verify_predicates.py"
README_FAST_GATE_BLOCK = """```bash
uv run python scripts/verify_frozen.py
uv run python scripts/verify_codex_plugin.py
uv run python scripts/verify_predicates.py
uv run ruff check .
uv run pytest
```"""
CI_PREDICATE_STEP = """      - name: Verify predicate registry
        run: uv run python scripts/verify_predicates.py"""
QUALITY_CI_MIRROR = (
    "mirrors `verify_frozen`, `verify_codex_plugin`, `verify_predicates`, "
    "`ruff`, and `pytest` on Python 3.13"
)
PACKAGING_FAST_GATE = (
    "Run the fast gate: `verify_frozen`, `verify_codex_plugin`, "
    "`verify_predicates`, `ruff`, and `pytest`."
)
REQUIRED_HOOKS = [
    ".codex/hooks/session-start.py",
    ".codex/hooks/user-prompt-nudge.py",
    ".codex/hooks/post-edit-static.py",
]
REQUIRED_WORKFLOWS = [
    ".github/workflows/fast-gate.yml",
    ".github/workflows/blender-smoke.yml",
]
REQUIRED_INFRA_FILES = [
    "AGENTS.md",
    ".agents/plugins/marketplace.json",
    ".codex/config.toml",
    ".codex/hooks.json",
    "LICENSE",
    "achievements/__init__.py",
    "achievements/catalog.py",
    "achievements/engine.py",
    "achievements/events.py",
    "achievements/integrity.py",
    "achievements/lifecycle.py",
    "achievements/levels.py",
    "achievements/metadata.py",
    "achievements/persistence.py",
    "achievements/predicates/__init__.py",
    "achievements/predicates/geometry_nodes.py",
    "achievements/predicates/material.py",
    "achievements/predicates/object_modifier.py",
    "achievements/predicates/registry.py",
    "achievements/predicates/render.py",
    "achievements/predicates/time_state.py",
    "achievements/predicates/types.py",
    "achievements/rewards.py",
    "achievements/sync.py",
    "achievements/ui.py",
    "blender_manifest.toml",
    "pyproject.toml",
    "scripts/build_extension.py",
    "scripts/find_blender.py",
    "scripts/run_blender_smoke.py",
    "scripts/run_installed_extension_policy.py",
    "scripts/verify_codex_plugin.py",
    "scripts/verify_frozen.py",
    "scripts/verify_predicates.py",
    "tests/test_catalog.py",
    "tests/test_infra_scripts.py",
    "tests/test_integrity.py",
    "tests/test_levels.py",
    "tests/test_predicates.py",
    "tests/test_release_packaging.py",
    "tests/test_engine.py",
    "tests/test_events.py",
    "tests/test_persistence.py",
    "tests/test_rewards.py",
    "tests/test_sync.py",
    "tests/test_ui.py",
    "tests/blender/smoke_engine.py",
    "tests/blender/smoke_extension_policy.py",
    "tests/blender/smoke_lifecycle_stress.py",
    "tests/blender/smoke_register.py",
    "tests/blender/smoke_persistence.py",
    "tests/blender/smoke_rewards.py",
    "tests/blender/smoke_ui_visual.py",
    "docs/archive/achievements_100_list.md",
]
FORBIDDEN_ACTIVE_TERMS = [
    "Next.js",
    "React",
    "Blueprint",
    "Tailwind",
    "Lighthouse",
    "Pa11y",
    "Playwright visual",
]


checks: list[tuple[str, bool, str]] = []


def record(name: str, passed: bool, detail: str = "") -> None:
    checks.append((name, passed, detail))
    tag = "PASS" if passed else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{tag}] {name}{suffix}")


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def has_frontmatter(path: Path, name: str) -> bool:
    text = path.read_text(encoding="utf-8")
    return text.startswith("---\n") and f"name: {name}" in text and "description:" in text


def markdown_section(text: str, heading: str) -> str:
    marker = f"## {heading}\n"
    if marker not in text:
        return ""
    return text.split(marker, maxsplit=1)[1].split("\n## ", maxsplit=1)[0].strip()


def current_handoff_atomicity_errors(text: str) -> list[str]:
    errors: list[str] = []
    expected_headings = [
        "Goal",
        "Changed Files",
        "Done",
        "Remaining",
        "Verification",
        "Agents And Review",
        "Blockers",
        "Residual Risks",
        "Next Start Prompt",
    ]
    actual_headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    if actual_headings != expected_headings:
        errors.append("operational handoff headings must be exact, unique, and ordered")
    required_markers = (
        "codex/reward-claim-atomicity",
        "9cd26bd616c861578bc026a627c1796dddcac655",
        "ADR 0007",
        "prospective claim",
        "idempotent",
        PREDICATE_COMMAND,
    )
    missing = [marker for marker in required_markers if marker not in text]
    if missing:
        errors.append(f"missing markers: {', '.join(missing)}")

    blockers = markdown_section(text, "Blockers")
    expected_blockers = (
        "None for local implementation and verification. No push, PR, tag, "
        "GitHub Release, version bump, production asset addition, or real "
        "`~/BlenderAchievements` access is authorized."
    )
    if blockers != expected_blockers:
        errors.append("Blockers must preserve the exact no-publication/no-real-data boundary")

    next_start = markdown_section(text, "Next Start Prompt")
    expected_next_start = (
        "Verify the exact local branch/commit and current `origin/main` before "
        "continuing. Do not redo reward claim atomicity. Take one separate task "
        "at a time; the recommended next task is a research-only specification "
        "for tutorial result verification and a defensible 90% threshold. Keep "
        "real `~/BlenderAchievements` untouched and do not publish or release "
        "without explicit owner authorization."
    )
    if next_start != expected_next_start:
        errors.append("Next Start Prompt must preserve the exact continuation boundary")

    authorization_scan = text
    for allowed_statement in (
        "No install/ZIP/release gate is authorized for this slice.",
        (
            "No push, PR, tag, GitHub Release, version bump, production asset "
            "addition, or real `~/BlenderAchievements` access is authorized."
        ),
        "do not publish or release without explicit owner authorization.",
        (
            "- Predicate semantics, deeper fixtures, UI/GPU/handler decomposition, "
            "production cloud, release versioning, tag, and GitHub Release remain "
            "separate decisions."
        ),
    ):
        authorization_scan = authorization_scan.replace(allowed_statement, "")
    if re.search(
        r"\b(?:push|publish|publication|release|tag)\b",
        authorization_scan,
        flags=re.IGNORECASE,
    ):
        errors.append("unexpected publication directive or statement detected")
    if "Active-Time and XP Integration" in text:
        errors.append("stale integration handoff title remains")
    return errors


def git_tracked_files() -> tuple[bool, set[str], str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    if result.returncode != 0:
        return False, set(), result.stdout.strip() or f"git ls-files returned {result.returncode}"
    return True, set(result.stdout.splitlines()), ""


def verify_marketplace() -> None:
    path = ROOT / ".agents" / "plugins" / "marketplace.json"
    record("marketplace exists", path.is_file())
    if not path.is_file():
        return
    data = read_json(path)
    plugin = next((item for item in data.get("plugins", []) if item.get("name") == PLUGIN_NAME), None)
    record("marketplace lists plugin", plugin is not None)
    if plugin:
        record("marketplace path is local plugin", plugin.get("source", {}).get("path") == f"./plugins/{PLUGIN_NAME}")
        record("marketplace policy complete", plugin.get("policy", {}).get("installation") == "AVAILABLE")


def verify_plugin() -> None:
    manifest = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
    record("plugin manifest exists", manifest.is_file())
    if not manifest.is_file():
        return
    data = read_json(manifest)
    record("plugin name matches folder", data.get("name") == PLUGIN_NAME)
    record("plugin manifest points at skills", data.get("skills") == "./skills/")
    prompts = "\n".join(data.get("interface", {}).get("defaultPrompt", []))
    record("plugin default prompts mention bootstrap", "achievements-bootstrap" in prompts)


def verify_skills() -> None:
    for skill in REQUIRED_SKILLS:
        skill_file = SKILL_ROOT / skill / "SKILL.md"
        agent_file = SKILL_ROOT / skill / "agents" / "openai.yaml"
        record(f"skill exists: {skill}", skill_file.is_file())
        if skill_file.is_file():
            record(f"skill frontmatter valid: {skill}", has_frontmatter(skill_file, skill))
        record(f"skill agent metadata exists: {skill}", agent_file.is_file())


def verify_codex_mirror() -> None:
    record("codex config exists", (ROOT / ".codex" / "config.toml").is_file())
    hooks_path = ROOT / ".codex" / "hooks.json"
    record("codex hooks.json exists", hooks_path.is_file())
    if hooks_path.is_file():
        hooks = read_json(hooks_path)
        post_tool = hooks.get("hooks", {}).get("PostToolUse", [])
        matchers = [item.get("matcher", "") for item in post_tool]
        record("post-edit hook covers apply_patch", any("apply_patch" in matcher for matcher in matchers))
    for hook in REQUIRED_HOOKS:
        record(f"hook script exists: {hook}", (ROOT / hook).is_file())
    for agent in REQUIRED_AGENTS:
        path = ROOT / ".codex" / "agents" / f"{agent}.toml"
        record(f"codex agent exists: {agent}", path.is_file())


def verify_docs() -> None:
    for doc in REQUIRED_DOCS:
        record(f"agent doc exists: {doc}", (ROOT / doc).is_file())
    for workflow in REQUIRED_WORKFLOWS:
        record(f"workflow exists: {workflow}", (ROOT / workflow).is_file())
    active_docs = [
        ROOT / "AGENTS.md",
        ROOT / ".codex" / "config.toml",
        ROOT / ".codex" / "hooks.json",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
        *[ROOT / doc for doc in REQUIRED_DOCS if doc not in HISTORICAL_DOCS],
        *[ROOT / hook for hook in REQUIRED_HOOKS],
        *[ROOT / workflow for workflow in REQUIRED_WORKFLOWS],
        *[ROOT / ".codex" / "agents" / f"{agent}.toml" for agent in REQUIRED_AGENTS],
        *[SKILL_ROOT / skill / "SKILL.md" for skill in REQUIRED_SKILLS],
        *[SKILL_ROOT / skill / "agents" / "openai.yaml" for skill in REQUIRED_SKILLS],
    ]
    stale: list[str] = []
    for path in active_docs:
        if not path.is_file():
            continue
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            for term in FORBIDDEN_ACTIVE_TERMS:
                if term in line and "not copied" not in line and "not portable" not in line:
                    stale.append(f"{path.relative_to(ROOT)}:{lineno}:{term}")
    record("active instructions avoid stale web-stack rules", not stale, ", ".join(stale[:8]))

    roadmap = ROOT / next(iter(HISTORICAL_DOCS))
    roadmap_text = roadmap.read_text(encoding="utf-8") if roadmap.is_file() else ""
    roadmap_nonempty = [line for line in roadmap_text.splitlines() if line.strip()]
    record(
        "historical roadmap is explicitly superseded",
        len(roadmap_nonempty) >= 2
        and roadmap_nonempty[0] == "# Achievements Iterative Roadmap Implementation Plan"
        and roadmap_nonempty[1].startswith(
            "> **SUPERSEDED — HISTORICAL PLAN ONLY.**"
        )
        and "ADRs 0002–0007 for current policy" in roadmap_nonempty[1]
        and "ADR 0002 retired `achievements_v01 (4).py`" in roadmap_nonempty[1],
    )

    context_keeper = SKILL_ROOT / "achievements-context-keeper" / "SKILL.md"
    context_text = (
        context_keeper.read_text(encoding="utf-8") if context_keeper.is_file() else ""
    )
    record(
        "context keeper records the sole runtime and retired duplicate",
        "Root `__init__.py` is the sole runtime" in context_text
        and "ADR 0002 retired `achievements_v01 (4).py`" in context_text
        and "Duplicate add-on file exists" not in context_text,
    )

    frozen_skill = SKILL_ROOT / "achievements-frozen-decisions" / "SKILL.md"
    frozen_skill_text = (
        frozen_skill.read_text(encoding="utf-8") if frozen_skill.is_file() else ""
    )
    record(
        "frozen decisions skill includes current correctness ADRs",
        "ADR 0005" in frozen_skill_text
        and "non-refreshing 120-second monotonic activity window" in frozen_skill_text
        and "runtime anchors stay out of JSON" in frozen_skill_text
        and "ADR 0006" in frozen_skill_text
        and "cap `1550`" in frozen_skill_text
        and "ADR 0007" in frozen_skill_text
        and "prospective claim" in frozen_skill_text
        and "idempotent marked-witness recovery" in frozen_skill_text,
    )

    readme = ROOT / "README.md"
    readme_text = readme.read_text(encoding="utf-8") if readme.is_file() else ""
    development_section = (
        readme_text.split("## Проверка разработки", maxsplit=1)[1].split(
            "\n## ", maxsplit=1
        )[0]
        if "## Проверка разработки" in readme_text
        else ""
    )
    record(
        "README fast gate includes predicate verifier",
        README_FAST_GATE_BLOCK in development_section,
    )

    fast_gate = ROOT / ".github" / "workflows" / "fast-gate.yml"
    fast_gate_text = fast_gate.read_text(encoding="utf-8") if fast_gate.is_file() else ""
    plugin_index = fast_gate_text.find(
        "run: uv run python scripts/verify_codex_plugin.py"
    )
    predicate_index = fast_gate_text.find(CI_PREDICATE_STEP)
    ruff_index = fast_gate_text.find("run: uv run ruff check .")
    record(
        "CI fast gate includes active predicate verifier step",
        plugin_index >= 0
        and predicate_index > plugin_index
        and ruff_index > predicate_index,
    )

    quality = ROOT / "docs" / "agent" / "quality-tooling.md"
    quality_text = quality.read_text(encoding="utf-8") if quality.is_file() else ""
    record(
        "quality tooling CI mirror includes predicate verifier",
        QUALITY_CI_MIRROR in quality_text,
    )

    session_start = ROOT / ".codex" / "hooks" / "session-start.py"
    session_text = (
        session_start.read_text(encoding="utf-8") if session_start.is_file() else ""
    )
    record(
        "session-start pointer includes predicate verifier",
        PREDICATE_COMMAND in session_text,
    )

    packaging = ROOT / "docs" / "agent" / "packaging-release.md"
    packaging_text = packaging.read_text(encoding="utf-8") if packaging.is_file() else ""
    record(
        "release guidance includes predicate verifier",
        PACKAGING_FAST_GATE in packaging_text,
    )

    current_handoff = ROOT / "docs" / "handoff" / "current.md"
    current_text = (
        current_handoff.read_text(encoding="utf-8")
        if current_handoff.is_file()
        else ""
    )
    handoff_errors = current_handoff_atomicity_errors(current_text)
    record(
        "current handoff tracks reward claim atomicity",
        not handoff_errors,
        "; ".join(handoff_errors),
    )


def verify_extension_contract() -> None:
    manifest = ROOT / "blender_manifest.toml"
    release_builder = ROOT / "scripts" / "build_extension.py"
    package_init = ROOT / "achievements" / "__init__.py"
    catalog = ROOT / "achievements" / "catalog.py"
    engine = ROOT / "achievements" / "engine.py"
    events = ROOT / "achievements" / "events.py"
    lifecycle = ROOT / "achievements" / "lifecycle.py"
    levels = ROOT / "achievements" / "levels.py"
    persistence = ROOT / "achievements" / "persistence.py"
    integrity = ROOT / "achievements" / "integrity.py"
    predicates = ROOT / "achievements" / "predicates"
    rewards = ROOT / "achievements" / "rewards.py"
    sync = ROOT / "achievements" / "sync.py"
    ui = ROOT / "achievements" / "ui.py"
    package_metadata = ROOT / "achievements" / "metadata.py"
    record("extension manifest exists: blender_manifest.toml", manifest.is_file())
    record("release builder exists: scripts/build_extension.py", release_builder.is_file())
    record("package skeleton exists: achievements/__init__.py", package_init.is_file())
    record("catalog module exists: achievements/catalog.py", catalog.is_file())
    record("engine helpers exist: achievements/engine.py", engine.is_file())
    record("event helpers exist: achievements/events.py", events.is_file())
    record("lifecycle helpers exist: achievements/lifecycle.py", lifecycle.is_file())
    record("level helpers exist: achievements/levels.py", levels.is_file())
    record("persistence helpers exist: achievements/persistence.py", persistence.is_file())
    record("integrity helpers exist: achievements/integrity.py", integrity.is_file())
    record("predicate registry exists: achievements/predicates", predicates.is_dir())
    record("rewards helpers exist: achievements/rewards.py", rewards.is_file())
    record("sync helpers exist: achievements/sync.py", sync.is_file())
    record("ui helpers exist: achievements/ui.py", ui.is_file())
    record("package metadata exists: achievements/metadata.py", package_metadata.is_file())
    license_file = ROOT / "LICENSE"
    record("GPL-3.0-or-later license exists: LICENSE", license_file.is_file())
    if manifest.is_file():
        manifest_data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        record("extension version is 0.2.2", manifest_data.get("version") == "0.2.2")
        record("extension minimum Blender is 5.0.0", manifest_data.get("blender_version_min") == "5.0.0")
        record(
            "extension manifest declares GPL-3.0-or-later",
            manifest_data.get("license") == ["SPDX:GPL-3.0-or-later"],
        )
        permissions = manifest_data.get("permissions")
        record(
            "extension files permission is exact and scoped",
            permissions
            == {"files": "Store progress and load local reward assets"},
        )
        record(
            "extension manifest declares no network permission",
            isinstance(permissions, dict) and "network" not in permissions,
        )
    if release_builder.is_file():
        builder_text = release_builder.read_text(encoding="utf-8")
        record("release builder supports committed revision mode", "--revision" in builder_text)
        record("release builder includes LICENSE", 'Path("LICENSE")' in builder_text)


def verify_tracked_required_files() -> None:
    ok, tracked, error = git_tracked_files()
    record("git tracked file list available", ok, error)
    if not ok:
        return
    required = set(REQUIRED_INFRA_FILES)
    required.update(REQUIRED_DOCS)
    required.update(REQUIRED_HOOKS)
    required.update(REQUIRED_WORKFLOWS)
    required.update(f".codex/agents/{agent}.toml" for agent in REQUIRED_AGENTS)
    for skill in REQUIRED_SKILLS:
        required.add(f"plugins/{PLUGIN_NAME}/skills/{skill}/SKILL.md")
        required.add(f"plugins/{PLUGIN_NAME}/skills/{skill}/agents/openai.yaml")
    required.add(f"plugins/{PLUGIN_NAME}/.codex-plugin/plugin.json")
    missing = sorted(path for path in required if path not in tracked)
    record("required Codex infra files are tracked", not missing, ", ".join(missing[:8]))


def main() -> int:
    verify_marketplace()
    verify_plugin()
    verify_skills()
    verify_codex_mirror()
    verify_docs()
    verify_extension_contract()
    verify_tracked_required_files()
    passed = sum(1 for _name, ok, _detail in checks if ok)
    failed = len(checks) - passed
    print(f"\nSUMMARY: {passed}/{len(checks)} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
