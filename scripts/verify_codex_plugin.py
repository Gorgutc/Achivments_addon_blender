from __future__ import annotations

import json
import subprocess
import sys
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
    "docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md",
    "docs/handoff/iteration-handoff-template.md",
    "docs/handoff/current.md",
]
REQUIRED_HOOKS = [
    ".codex/hooks/session-start.py",
    ".codex/hooks/user-prompt-nudge.py",
    ".codex/hooks/post-edit-static.py",
]
REQUIRED_INFRA_FILES = [
    "AGENTS.md",
    ".agents/plugins/marketplace.json",
    ".codex/config.toml",
    ".codex/hooks.json",
    "achievements/__init__.py",
    "achievements/catalog.py",
    "achievements/events.py",
    "achievements/lifecycle.py",
    "achievements/metadata.py",
    "blender_manifest.toml",
    "pyproject.toml",
    "scripts/find_blender.py",
    "scripts/run_blender_smoke.py",
    "scripts/verify_codex_plugin.py",
    "scripts/verify_frozen.py",
    "tests/test_infra_scripts.py",
    "tests/test_events.py",
    "tests/blender/smoke_lifecycle_stress.py",
    "tests/blender/smoke_register.py",
    "tests/blender/smoke_persistence.py",
    "tests/blender/smoke_rewards.py",
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
    active_docs = [
        ROOT / "AGENTS.md",
        ROOT / ".codex" / "config.toml",
        ROOT / ".codex" / "hooks.json",
        ROOT / ".agents" / "plugins" / "marketplace.json",
        PLUGIN_ROOT / ".codex-plugin" / "plugin.json",
        *[ROOT / doc for doc in REQUIRED_DOCS],
        *[ROOT / hook for hook in REQUIRED_HOOKS],
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


def verify_extension_draft() -> None:
    manifest = ROOT / "blender_manifest.toml"
    package_init = ROOT / "achievements" / "__init__.py"
    catalog = ROOT / "achievements" / "catalog.py"
    events = ROOT / "achievements" / "events.py"
    lifecycle = ROOT / "achievements" / "lifecycle.py"
    package_metadata = ROOT / "achievements" / "metadata.py"
    record("extension draft exists: blender_manifest.toml", manifest.is_file())
    record("package skeleton exists: achievements/__init__.py", package_init.is_file())
    record("catalog module exists: achievements/catalog.py", catalog.is_file())
    record("event helpers exist: achievements/events.py", events.is_file())
    record("lifecycle helpers exist: achievements/lifecycle.py", lifecycle.is_file())
    record("package metadata exists: achievements/metadata.py", package_metadata.is_file())


def verify_tracked_required_files() -> None:
    ok, tracked, error = git_tracked_files()
    record("git tracked file list available", ok, error)
    if not ok:
        return
    required = set(REQUIRED_INFRA_FILES)
    required.update(REQUIRED_DOCS)
    required.update(REQUIRED_HOOKS)
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
    verify_extension_draft()
    verify_tracked_required_files()
    passed = sum(1 for _name, ok, _detail in checks if ok)
    failed = len(checks) - passed
    print(f"\nSUMMARY: {passed}/{len(checks)} PASS, {failed} FAIL")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
