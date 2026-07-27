"""Verify exact catalog-to-predicate coverage without importing Blender."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from achievements.catalog import ACHIEVEMENTS_DEF  # noqa: E402
from achievements.predicates import (  # noqa: E402
    PREDICATE_PAIRS,
    registry_bijection_errors,
)

PREDICATE_ROOT = ROOT / "achievements" / "predicates"


def _bpy_imports() -> list[str]:
    violations = []
    for path in sorted(PREDICATE_ROOT.glob("*.py")):
        module = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(module):
            if isinstance(node, ast.Import) and any(alias.name == "bpy" for alias in node.names):
                violations.append(path.name)
            if isinstance(node, ast.ImportFrom) and node.module == "bpy":
                violations.append(path.name)
    return violations


def main() -> int:
    errors = list(registry_bijection_errors(ACHIEVEMENTS_DEF))
    bpy_imports = _bpy_imports()
    complex_ids = {complex_id for complex_id, _step in PREDICATE_PAIRS}
    if len(PREDICATE_PAIRS) != 85:
        errors.append(f"expected 85 predicate pairs, got {len(PREDICATE_PAIRS)}")
    if len(complex_ids) != 65:
        errors.append(f"expected 65 complex ids, got {len(complex_ids)}")
    if bpy_imports:
        errors.append(f"bpy imports in pure predicate modules: {', '.join(bpy_imports)}")

    if errors:
        for error in errors:
            print(f"[FAIL] {error}")
        return 1
    print("[PASS] predicate registry is an exact 65-id/85-pair catalog bijection")
    print("[PASS] pure predicate modules do not import bpy")
    return 0


if __name__ == "__main__":
    sys.exit(main())
