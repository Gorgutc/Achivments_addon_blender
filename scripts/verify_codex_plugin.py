from __future__ import annotations

import ast
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
    "docs/agent/adrs/0008-release-identity-and-ship-acceptance.md",
    "docs/research/lesson-result-verification.md",
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
CURRENT_RELEASE_IDENTITY = "0.2.3"
RELEASE_STAGE_POLICY = (
    "Release stages: (A) a full validation gate produces only ephemeral outputs and authorizes no retention, canonical artifact, or publication; "
    "(B) only separate explicit owner candidate-retention acceptance may preserve one exact audited local candidate SHA, which remains non-canonical and not publication; "
    "(C) only separate explicit owner publication acceptance may create `v0.2.3` tag and GitHub Release from that exact retained candidate. This session grants none."
)
RELEASE_POLICY_MARKERS = (
    "Release identity: `0.2.3` source candidate.",
    "No tag, GitHub Release, or publication is authorized without explicit owner ship acceptance; a local retained candidate is not publication.",
    "The historical `achievements-0.2.2.zip` is immutable pre-PR16 evidence and is not a current install or build artifact.",
    RELEASE_STAGE_POLICY,
)
RELEASE_GUIDANCE_PATHS = (
    "README.md",
    "docs/agent/packaging-release.md",
    "docs/agent/quality-tooling.md",
    "docs/agent/verification.md",
    "plugins/achievements-blender-codex/skills/achievements-packaging/SKILL.md",
    "plugins/achievements-blender-codex/skills/achievements-quality-gate/SKILL.md",
)
LESSON_RESEARCH_PATH = "docs/research/lesson-result-verification.md"
LESSON_RESEARCH_FRONTMATTER = """---
status: research-draft
implementation_authorized: false
owner_approved: false
threshold_policy: calibration-required
reward_bridge: disabled
---
"""
LESSON_RESEARCH_HEADINGS = (
    "Status And Non-Authorization",
    "Current Frozen Boundaries",
    "Glossary",
    "Assessed Unit",
    "Rubric Schema",
    "Feature Normalization",
    "Mandatory Gates And Scoring",
    "Tolerances And Equivalences",
    "Explainable Result",
    "Fixture And Calibration Protocol",
    "FP/FN Acceptance",
    "Retry And Anti-Farming",
    "Versioning And Migration",
    "Reward Bridge Boundary",
    "Nine-Lesson Readiness Matrix",
    "Owner Decisions",
    "Implementation Entry Gate",
)
LESSON_RESEARCH_IDS = (
    "lesson_vertices_basics",
    "lesson_edit_basics",
    "lesson_edges",
    "lesson_faces",
    "lesson_modeling",
    "lesson_materials",
    "lesson_time_management",
    "lesson_geo_nodes_intro",
    "lesson_render_basics",
)
LESSON_RESEARCH_ALLOWED_STATES = {
    "calibration_required",
    "unsupported_pending_owner_contract",
}
LESSON_RESEARCH_RUBRIC_FIELDS = (
    "rule_id",
    "feature_kind",
    "selector",
    "normalizer",
    "comparator",
    "expected",
    "tolerance_or_exact",
    "allowed_equivalences",
    "mandatory",
    "weight_points",
    "user_explanation",
    "fixture_refs",
)
LESSON_RESEARCH_OWNER_DECISIONS = (
    "OD-01: Approve or reject assessed outcomes, lesson URLs, and canonical reference outcomes for each lesson.",
    "OD-02: Approve the extra-content policy for objects, collections, and external references.",
    "OD-03: Approve each scope and its closure rules.",
    "OD-04: Approve selector identity semantics for names, IDs, ordering, and relationships.",
    "OD-05: Approve any event-only proof contract and its privacy limits.",
    "OD-06: Approve rule-local tolerances and Blender equivalences.",
    "OD-07: Approve canonical fixtures, binary `.blend` assets, and license/provenance evidence.",
    "OD-08: Approve the authoring/review workflow and learner-visible diff detail.",
    "OD-09: Approve calibration, adversarial fixture coverage, and a nonzero-gap threshold.",
    "OD-10: Approve independent holdout size, acceptable false-negative rate, and equivalence disposition.",
    "OD-11: Approve the cross-version Blender support policy.",
    "OD-12: Approve evidence retention, deletion, privacy policy, and acceptance of the local-tampering limitation.",
    "OD-13: Approve persistence location and any schema/migration contract.",
    "OD-14: Approve old-pass behavior, latest/best/current-version presentation, and stale/not_attempted policy.",
    "OD-15: Approve whether a lesson pass gives XP; the current answer is no.",
    "OD-16: Approve reward-bridge evidence/claim scope, lesson-to-reward mapping, prospective payload, confirmed Blender action, atomic commit, retry, and anti-abuse policy.",
)
RELEASE_AUTHORITY_PATHS = (
    "AGENTS.md",
    "README.md",
    "docs/agent/adrs/0008-release-identity-and-ship-acceptance.md",
    "docs/agent/architecture.md",
    "docs/agent/frozen-application-contract.md",
    "docs/agent/frozen-decisions.md",
    "docs/agent/packaging-release.md",
    "docs/agent/quality-tooling.md",
    "docs/agent/verification.md",
    "docs/handoff/current.md",
    "plugins/achievements-blender-codex/skills/achievements-frozen-decisions/SKILL.md",
    "plugins/achievements-blender-codex/skills/achievements-instruction-drift/SKILL.md",
    "plugins/achievements-blender-codex/skills/achievements-packaging/SKILL.md",
    "plugins/achievements-blender-codex/skills/achievements-quality-gate/SKILL.md",
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


def semantic_clauses(text: str) -> tuple[str, ...]:
    """Split policy prose at lines, sentences, and semicolons without conflating clauses."""
    paragraphs: list[str] = []
    wrapped_lines: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            if wrapped_lines:
                paragraphs.append(" ".join(wrapped_lines))
                wrapped_lines = []
            continue
        if re.match(r"^(?:[-*+]\s+|\d+[.)]\s+|#{1,6}\s|\|)", line):
            if wrapped_lines:
                paragraphs.append(" ".join(wrapped_lines))
            wrapped_lines = [line]
        else:
            wrapped_lines.append(line)
    if wrapped_lines:
        paragraphs.append(" ".join(wrapped_lines))

    return tuple(
        clause.strip(" \t,:")
        for paragraph in paragraphs
        for clause in re.split(
            r"[;]+|(?<=[.!?])(?=\s)|\b(?:but|however|therefore|so)\b|"
            r"(?:,\s*|\band\s+)(?=(?:publish|push|create|install|start|begin|"
            r"implementation may begin|rewardmanager|passing|(?:a )?lesson url|"
            r"(?:use|set|apply)\s+\d+(?:\.\d+)?%\s+as\b|threshold\b))",
            paragraph,
            flags=re.IGNORECASE,
        )
        if clause.strip(" \t,:")
    )


def clause_is_explicitly_safe(clause: str, action: re.Match[str]) -> bool:
    """A dangerous action needs an in-clause negation or explicit owner gate."""
    normalized = re.sub(r"\s+", " ", clause).strip()
    if re.search(
        r"(?i)\b(?:no longer|not only|not unauthorized|not closed|no publication is prohibited|"
        r"no owner approval is needed|authorized without owner acceptance|without owner acceptance)\b",
        normalized,
    ):
        return False
    if re.search(
        r"(?i)^\s*if stage c is separately approved\b.*\bfuture task may\b.*\b"
        r"(?:publish|push|create)\b.*\bexact retained candidate\b",
        normalized,
    ):
        return True
    if re.search(
        r"(?i)\bonly after\b|\bseparate explicit owner\b|\bfuture owner\b.*\bonly\b|"
        r"\b(?:requires|pending)\s+(?:separate\s+explicit\s+)?owner acceptance\b",
        normalized,
    ):
        return True

    before = normalized[: action.start()]
    matched = action.group(0)
    after = normalized[action.end() :]
    negation = r"(?:no|never|cannot|can't|must not|do not|does not|is not|are not|prohibited|forbidden|не|нельзя|запрещено)"
    if re.search(r"(?i)\b(?:no|not|never|cannot|can't|must not|do not|does not|is not|are not|prohibited|forbidden|не|нельзя|запрещено)\b", matched):
        return True
    if re.search(r"(?i)\bdid not (?:run|perform|execute)\b", normalized):
        return True
    if re.search(rf"(?i)\b{negation}\b(?:\s+\w+){{0,3}}\s*$", before):
        return True
    if re.search(r"(?i)\bwithout\b(?:\s+\w+){0,3}\s*$", before):
        return True
    if re.search(rf"(?i)^\s*(?:\w+\s+){{0,3}}\b{negation}\b", after):
        return True
    negation_tail = re.search(r"(?i)\b(?:no|not|never|cannot|can't|must not|do not|does not|is not|are not|prohibited|forbidden)\b(.*)$", before)
    if negation_tail and " and " not in negation_tail.group(1).lower():
        return True
    return bool(
        re.search(r"(?i)\b(?:rejected|unvalidated|calibration-only)\b", normalized)
        and re.search(r"(?i)\bthreshold\b", normalized)
    )


def unsafe_policy_clauses(text: str, dangerous_patterns: tuple[str, ...]) -> list[str]:
    """Return dangerous policy clauses not independently negated or owner-gated."""
    return [
        clause
        for clause in semantic_clauses(text)
        if any(
            not clause_is_explicitly_safe(clause, action)
            for pattern in dangerous_patterns
            for action in re.finditer(pattern, clause, re.IGNORECASE)
        )
    ]


RELEASE_DANGEROUS_PATTERNS = (
    r"\bstage a\b(?:(?!\bstage b\b).)*\b(?:retain(?:s|ed|ing)?|preserv(?:e|es|ed|ing)|cop(?:y|ies|ied|ying)|canonicali[sz](?:e|es|ed|ing))\b",
    r"\bfull validation gate\b.*\b(?:retain(?:s|ed|ing)?|preserv(?:e|es|ed|ing)|cop(?:y|ies|ied|ying)|canonicali[sz](?:e|es|ed|ing))\b",
    r"\b(?:push|publish)(?:es|ed|ing)?\b(?!\s+to\s+`?main`?)",
    r"\b(?:create|make)\b.*\b(?:v?0\.2\.3\s+)?tag\b",
    r"\b(?:create|make)\b.*\bgithub release\b",
    r"\b(?:tag|github release|publication|stage c)\b.*\bauthorized\b",
    r"\bowner approved publication\b",
    r"\bowner has approved publication\b",
    r"\bpublication was approved by the owner\b",
    r"\bpublication is not unauthorized\b",
    r"\bno publication is prohibited\b",
    r"\btag creation\b",
    r"\b(?:install|use|release)\b.*\bachievements-0\.2\.2\.zip\b",
    r"\bachievements-0\.2\.2\.zip\b.*\b(?:current|release|artifact)\b",
    r"\b0\.2\.3\s+zip\b.*\b(?:current|canonical)\b",
)


RESEARCH_DANGEROUS_PATTERNS = (
    r"\bowner approved (?:this )?implementation\b",
    r"\bthe owner has approved implementation\b",
    r"\bthis implementation was approved by the owner\b",
    r"\bno owner approval is needed\b",
    r"\bowner approval (?:is )?(?:complete|granted)\b",
    r"\b(?:start|begin) implementation(?: now)?\b",
    r"\bimplementation\b.*\b(?:authorized|ready|may begin)\b",
    r"\bimplementation is not unauthorized\b",
    r"\bentry gate\b.*\b(?:open|no longer closed|not closed)\b",
    r"\b(?:use|set|apply)\s+\d+(?:\.\d+)?%\s+as (?:the )?threshold\b",
    r"\bthreshold(?:_basis_points)?\s*(?:is|=|:)\s*(?!null\b)\d+(?:\.\d+)?%?\b",
    r"\b(?:an )?approved threshold(?: of)?\s+\d+(?:\.\d+)?%\s+applies\b",
    r"\b(?:approved|default)\s+threshold\b.*\d+(?:\.\d+)?%\b",
    r"\brewardmanager\b.*\binvoked\b",
    r"\breward bridge\b.*\benabled\b",
    r"\blesson persistence\b.*\b(?:authorized|enabled)\b",
    r"\b(?:xp|reward) writes?\b.*\b(?:enabled|authorized)\b",
    r"\b(?:may|can|will|is authorized to) write `?rewards_claimed`?\b",
    r"\b(?:passing|pass(?:ing)? assessment|passing (?:the )?lesson|a pass)\b.*\b(?:grants?|awards?|writes?|persists?|creates?)\b.*\b(?:xp|reward|claim|persistence)\b",
    r"\blesson url proves completion\b",
)


def release_guidance_errors(guidance: dict[str, str]) -> list[str]:
    """Reject stale current-artifact wording and missing ship-acceptance guards."""
    errors: list[str] = []
    for relative_path in RELEASE_GUIDANCE_PATHS:
        text = guidance.get(relative_path, "")
        normalized = re.sub(r"\s+", " ", text)
        missing = [marker for marker in RELEASE_POLICY_MARKERS if marker not in normalized]
        if missing:
            errors.append(f"{relative_path} missing release-policy marker")
        if "reports/extension/achievements-0.2.2.zip" in text:
            errors.append(f"{relative_path} presents the historical 0.2.2 ZIP as current")
        if re.search(r"\b(?:frozen|current)\s+canonical\s+(?:SHA|ZIP)\b", text, re.IGNORECASE):
            errors.append(f"{relative_path} presents a canonical artifact as the current candidate")
        if re.search(
            r"\bfull\s+(?:validation\s+)?gate\b(?![^.\n]{0,100}\bowner\b)"
            r"[^.\n]{0,100}\b(?:may|can|will)\s+(?:retain|preserve)\b",
            text,
            re.IGNORECASE,
        ):
            errors.append(f"{relative_path} lets a full gate retain a candidate without owner acceptance")
    return errors


def active_release_guidance() -> dict[str, str]:
    return {
        relative_path: (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in RELEASE_GUIDANCE_PATHS
        if (ROOT / relative_path).is_file()
    }


def release_authority_errors(authorities: dict[str, str]) -> list[str]:
    """Reject additive publication authority across every active release surface."""
    errors: list[str] = []
    for relative_path in RELEASE_AUTHORITY_PATHS:
        text = authorities.get(relative_path, "")
        if not text:
            errors.append(f"{relative_path} is missing release authority guidance")
            continue
        if unsafe_policy_clauses(text, RELEASE_DANGEROUS_PATTERNS):
            errors.append(f"{relative_path} contains an additive release action without an in-clause denial or owner gate")
    return errors


def active_release_authorities() -> dict[str, str]:
    return {
        relative_path: (ROOT / relative_path).read_text(encoding="utf-8")
        for relative_path in RELEASE_AUTHORITY_PATHS
        if (ROOT / relative_path).is_file()
    }


def release_version_parity_errors() -> list[str]:
    """Fail closed unless every active version surface names the source candidate."""
    errors: list[str] = []
    expected_tuple = tuple(int(part) for part in CURRENT_RELEASE_IDENTITY.split("."))

    try:
        root_tree = ast.parse((ROOT / "__init__.py").read_text(encoding="utf-8"))
        root_infos = [
            ast.literal_eval(node.value)
            for node in root_tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "bl_info" for target in node.targets)
        ]
        if len(root_infos) != 1 or root_infos[0].get("version") != expected_tuple:
            errors.append("root bl_info version differs from the release identity")
    except (OSError, SyntaxError, ValueError):
        errors.append("root bl_info version differs from the release identity")

    try:
        metadata_tree = ast.parse((ROOT / "achievements" / "metadata.py").read_text(encoding="utf-8"))
        metadata_versions = [
            ast.literal_eval(node.value)
            for node in metadata_tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "ADDON_VERSION" for target in node.targets)
        ]
        if metadata_versions != [expected_tuple]:
            errors.append("achievements metadata version differs from the release identity")
    except (OSError, SyntaxError, ValueError):
        errors.append("achievements metadata version differs from the release identity")

    try:
        manifest = tomllib.loads((ROOT / "blender_manifest.toml").read_text(encoding="utf-8"))
        if manifest.get("version") != CURRENT_RELEASE_IDENTITY:
            errors.append("extension manifest version differs from the release identity")
    except (OSError, tomllib.TOMLDecodeError):
        errors.append("extension manifest version differs from the release identity")

    try:
        project = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        if project.get("project", {}).get("version") != CURRENT_RELEASE_IDENTITY:
            errors.append("pyproject version differs from the release identity")
    except (OSError, tomllib.TOMLDecodeError):
        errors.append("pyproject version differs from the release identity")

    try:
        lock_data = tomllib.loads((ROOT / "uv.lock").read_text(encoding="utf-8"))
        packages = lock_data.get("package", [])
        if not isinstance(packages, list) or not all(isinstance(package, dict) for package in packages):
            raise TypeError("uv.lock package entries must be tables")
        root_packages = [
            package for package in packages if package.get("name") == "achievements-blender-codex-infra"
        ]
        if len(root_packages) != 1 or root_packages[0].get("version") != CURRENT_RELEASE_IDENTITY:
            errors.append("uv.lock root package version differs from the release identity")
    except (OSError, tomllib.TOMLDecodeError, TypeError, AttributeError):
        errors.append("uv.lock root package version differs from the release identity")

    try:
        smoke_tree = ast.parse(
            (ROOT / "tests" / "blender" / "smoke_extension_policy.py").read_text(encoding="utf-8")
        )
        smoke_versions = [
            ast.literal_eval(node.comparators[0])
            for node in ast.walk(smoke_tree)
            if isinstance(node, ast.Compare)
            and len(node.ops) == 1
            and isinstance(node.ops[0], ast.NotEq)
            and len(node.comparators) == 1
            and isinstance(node.left, ast.Call)
            and isinstance(node.left.func, ast.Name)
            and node.left.func.id == "tuple"
            and len(node.left.args) == 1
            and isinstance(node.left.args[0], ast.Attribute)
            and node.left.args[0].attr == "ADDON_VERSION"
        ]
        if smoke_versions != [expected_tuple]:
            errors.append("Blender smoke extension-policy version differs from the release identity")
    except (OSError, SyntaxError, ValueError):
        errors.append("Blender smoke extension-policy version differs from the release identity")
    return errors


def lesson_result_verification_errors(text: str) -> list[str]:
    """Keep the lesson-result document a closed research draft until owner approval."""
    errors: list[str] = []
    if not text.startswith(LESSON_RESEARCH_FRONTMATTER):
        errors.append("research draft frontmatter must be exact and closed")

    headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)
    if tuple(headings) != LESSON_RESEARCH_HEADINGS:
        errors.append("research draft H2 headings must be exact, unique, and ordered")

    matrix = markdown_section(text, "Nine-Lesson Readiness Matrix")
    rows = re.findall(r"^\|\s*`(lesson_[a-z_]+)`\s*\|\s*`([a-z_]+)`\s*\|", matrix, re.MULTILINE)
    row_ids = [lesson_id for lesson_id, _state in rows]
    row_states = [state for _lesson_id, state in rows]
    if row_ids != list(LESSON_RESEARCH_IDS):
        errors.append("research matrix must contain each current lesson id exactly once and in catalog order")
    if len(row_states) != len(LESSON_RESEARCH_IDS) or set(row_states) - LESSON_RESEARCH_ALLOWED_STATES:
        errors.append("research matrix may use only closed readiness states")

    required_markers = (
        "Submit result",
        "URL, elapsed time, or viewing history is not proof",
        "immutable local `attempt_id`",
        "extractor_version",
        "candidate_digest",
        "It is not an attempt id and does not include `extractor_version`.",
        "lesson_id + assessment_version + rubric_digest + extractor_version + candidate_digest",
        "identifies deterministic evaluation reuse, not a submitted attempt",
        "reuses the deterministic evaluation and never grants a new claim, XP, or reward",
        "active_object`, `selected_objects`, `assessment_collection`, and `scene`",
        "explicit closure",
        "Outcome",
        "Process",
        "deterministic JSON",
        "canonical Blender units",
        "normalized quaternion",
        "finite floats",
        "unsupported Blender-version semantics produce `indeterminate`",
        "explicit Blender equivalence",
        "Mandatory gates have weight 0.",
        "sum is exactly 1000",
        "no N/A, and no dynamic denominator",
        "passed_weight",
        "denominator = 1000",
        "passed_weight * 10000 >= threshold_basis_points * 1000",
        "half-up rounding to `0.1%`",
        "A missing feature fails",
        "threshold_basis_points: null",
        "rejected/unvalidated hypothesis, never a default or approved threshold",
        "max_negative_score < min_positive_score",
        "nonzero integer gap",
        "tests/fixtures/lesson_assessment/<lesson_id>/<assessment_version>/",
        "No silent edit, recalculation, migration, or backfill",
        "conceptual immutable attempt results keyed by `attempt_id`",
        "last completed current-version result",
        "maximum exact ratio among mandatory-pass results",
        "indeterminate result does not replace best",
        "historical and leaves current status stale/not_attempted",
        "Passing assessment yields evidence only",
        "No lesson persistence is authorized.",
        "entry gate is closed",
        "0.2.3",
        "schema `1.0.0`",
        "XP awards `5/10/20`",
        "cap `1550`",
        "files-only permission",
        "disabled production networking",
    )
    missing = [marker for marker in required_markers if marker not in text]
    if missing:
        errors.append(f"research draft missing boundary markers: {', '.join(missing)}")

    rubric_section = markdown_section(text, "Rubric Schema")
    rubric_fences = re.findall(r"```text\n(.*?)\n```", rubric_section, flags=re.DOTALL)
    rubric_fields = tuple(rubric_fences[0].splitlines()) if len(rubric_fences) == 1 else ()
    if rubric_fields != LESSON_RESEARCH_RUBRIC_FIELDS:
        errors.append("research rubric fields must be the exact ordered unique schema")

    threshold_values = re.findall(r"(?m)^threshold_basis_points:[ \t]*([^\r\n]+?)[ \t]*\r?$", text)
    if threshold_values != ["null"]:
        errors.append("research threshold must remain null until calibration")
    if unsafe_policy_clauses(text, RESEARCH_DANGEROUS_PATTERNS) or re.search(
        r"(?im)^owner_approved:\s*true\b", text
    ):
        errors.append("research draft contains an additive implementation, threshold, or reward authorization")

    deny_markers = (
        "must not write `rewards_claimed`",
        "bypass unlock hashes",
        "change XP `5/10/20` or cap `1550`",
        "treat a URL as completion",
        "invoke `RewardManager`",
        "no telemetry, authentication, network, account",
    )
    denied = [marker for marker in deny_markers if marker not in text]
    if denied:
        errors.append(f"research draft must retain deny boundaries: {', '.join(denied)}")

    owner_decisions = markdown_section(text, "Owner Decisions")
    owner_lines = tuple(re.findall(r"^- (OD-\d{2}: .+)$", owner_decisions, flags=re.MULTILINE))
    if owner_lines != LESSON_RESEARCH_OWNER_DECISIONS:
        errors.append("research draft must preserve the exact ordered owner decisions")
    if re.search(r"(?im)^\s*(?:status|readiness_state)\s*:\s*(?:complete|ready)\b", text):
        errors.append("research draft must not declare an actual complete or ready state")
    if re.search(r"(?m)^\|\s*`lesson_[a-z_]+`\s*\|\s*`ready`\s*\|", matrix):
        errors.append("research matrix must not declare a ready state")
    return errors


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
        "213babb6e29e023617a66600e4b9d8375ea466d9",
        "396dda957908b26c94d73387bcddf14712a4c23c",
        "PR #17",
        (
            "CI created and removed disposable per-job ZIP/install state; no "
            "canonical, retained, or published extension artifact was produced."
        ),
        "ADR 0007",
        "ADR 0008",
        "0.2.3",
        "explicit owner ship acceptance",
        "historical `achievements-0.2.2.zip`",
        "prospective claim",
        "idempotent",
        PREDICATE_COMMAND,
    )
    missing = [marker for marker in required_markers if marker not in text]
    if missing:
        errors.append(f"missing markers: {', '.join(missing)}")

    blockers = markdown_section(text, "Blockers")
    for marker in (
        "No technical blocker prevents source-candidate work.",
        "separate explicit owner publication acceptance",
        "No production asset addition",
        "`~/BlenderAchievements` access is authorized",
    ):
        if marker not in blockers:
            errors.append("Blockers must preserve the source-candidate and no-ship boundary")
            break

    next_start = markdown_section(text, "Next Start Prompt")
    for marker in (
        "lesson-assessment specification remains a separate research-only slice",
        "explicit owner authorization",
        "canonical artifact",
    ):
        if marker not in next_start:
            errors.append("Next Start Prompt must preserve the exact continuation boundary")
            break

    if re.search(
        r"(?:push|publish|tag|GitHub Release)(?![^.\n]{0,80}\b(?:are|is) authorized\s+without\b)"
        r"[^.\n]{0,80}\b(?:are|is) authorized\b|"
        r"Publish this branch|Create a tag and GitHub Release|You may push this branch",
        text,
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
    release_errors = release_guidance_errors(active_release_guidance())
    record(
        "active release guidance is identity-safe and ship-acceptance-gated",
        not release_errors,
        "; ".join(release_errors),
    )
    authority_errors = release_authority_errors(active_release_authorities())
    record(
        "active release authorities reject additive release permission",
        not authority_errors,
        "; ".join(authority_errors),
    )

    research_path = ROOT / LESSON_RESEARCH_PATH
    research_text = research_path.read_text(encoding="utf-8") if research_path.is_file() else ""
    research_errors = lesson_result_verification_errors(research_text)
    record(
        "lesson-result verification remains a closed research draft",
        research_path.is_file() and not research_errors,
        "; ".join(research_errors),
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
        record(
            "extension version is 0.2.3 source candidate",
            manifest_data.get("version") == CURRENT_RELEASE_IDENTITY,
        )
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
    version_parity_errors = release_version_parity_errors()
    record(
        "active release version surfaces are exact and synchronized",
        not version_parity_errors,
        ", ".join(version_parity_errors),
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
