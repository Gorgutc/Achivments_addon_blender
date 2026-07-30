from __future__ import annotations

import importlib
import os
import sys
import tomllib
from pathlib import Path

import addon_utils
import bpy

EXPECTED_MODULE = os.environ.get(
    "ACHIEVEMENTS_EXTENSION_MODULE",
    "bl_ext.user_default.achievements",
)
EXPECTED_EXTENSION_DIR = Path(os.environ["ACHIEVEMENTS_EXPECTED_EXTENSION_DIR"]).resolve()
POLICY_PHASE = os.environ.get("ACHIEVEMENTS_POLICY_PHASE", "installed")


def fail(message: str) -> None:
    print(f"[smoke_extension_policy:FAIL] {message}")
    raise SystemExit(1)


def is_within(path: str | os.PathLike[str], directory: Path) -> bool:
    try:
        Path(path).resolve().relative_to(directory)
    except (OSError, RuntimeError, ValueError):
        return False
    return True


def installed_probe() -> None:
    module = importlib.import_module(EXPECTED_MODULE)
    module_file = Path(module.__file__).resolve()
    if module.__name__ != EXPECTED_MODULE or module.__package__ != EXPECTED_MODULE:
        fail(
            "installed module identity drifted: "
            f"name={module.__name__!r}, package={module.__package__!r}"
        )
    if module_file.parent != EXPECTED_EXTENSION_DIR:
        fail(
            "installed module loaded from unexpected directory: "
            f"{module_file.parent} != {EXPECTED_EXTENSION_DIR}"
        )
    if tuple(module.ach_metadata.ADDON_VERSION) != (0, 2, 3):
        fail(f"installed version drifted: {module.ach_metadata.ADDON_VERSION!r}")

    with (EXPECTED_EXTENSION_DIR / "blender_manifest.toml").open("rb") as handle:
        manifest = tomllib.load(handle)
    permissions = manifest.get("permissions")
    if permissions != {"files": "Store progress and load local reward assets"}:
        fail(f"installed manifest permissions drifted: {permissions!r}")
    if "network" in permissions:
        fail("installed manifest unexpectedly requests network permission")

    foreign_modules: list[str] = []
    for name, loaded_module in tuple(sys.modules.items()):
        loaded_file = getattr(loaded_module, "__file__", None)
        if not loaded_file or not is_within(loaded_file, EXPECTED_EXTENSION_DIR):
            continue
        if name != EXPECTED_MODULE and not name.startswith(f"{EXPECTED_MODULE}."):
            foreign_modules.append(name)
    if foreign_modules:
        fail(
            "extension files escaped the bl_ext namespace: "
            + ", ".join(sorted(foreign_modules))
        )

    extension_sys_paths = [
        path
        for path in sys.path
        if path and is_within(path, EXPECTED_EXTENSION_DIR)
    ]
    if extension_sys_paths:
        fail(
            "extension directory leaked into sys.path: "
            + ", ".join(extension_sys_paths)
        )

    reset_warnings = getattr(addon_utils, "_is_first_reset", None)
    if callable(reset_warnings):
        reset_warnings()
    else:
        addon_utils._extensions_warnings_get._is_first = True
    warning_map = addon_utils._extensions_warnings_get()
    if warning_map:
        fail(f"Blender reported extension policy warnings: {warning_map!r}")

    if not getattr(module, "_addon_registered", False):
        fail("installed extension is not registered before lifecycle probe")
    module.unregister()
    if getattr(module, "_addon_registered", True):
        fail("explicit unregister did not clear registration state")
    module.register()
    if not getattr(module, "_addon_registered", False):
        fail("explicit register did not restore registration state")
    if not hasattr(bpy.ops.ach, "open_extension_manager"):
        fail("registered extension-management operator is unavailable")

    print(
        "[smoke_extension_policy:PASS] installed module is namespaced, "
        "sys.path-clean, warning-free, permission-scoped, and lifecycle-safe"
    )


def removed_probe() -> None:
    enabled_modules = {addon.module for addon in bpy.context.preferences.addons}
    if EXPECTED_MODULE in enabled_modules:
        fail("removed extension remains enabled")
    try:
        importlib.import_module(EXPECTED_MODULE)
    except ModuleNotFoundError:
        pass
    else:
        fail("removed extension remains importable")
    if EXPECTED_EXTENSION_DIR.exists():
        fail(f"removed extension directory remains: {EXPECTED_EXTENSION_DIR}")
    data_directory = Path(os.environ["USERPROFILE"]) / "BlenderAchievements"
    if not data_directory.is_dir():
        fail("disposable progress directory was removed with the extension")
    print(
        "[smoke_extension_policy:REMOVED_PASS] package absent, disabled, "
        "unimportable, and progress directory preserved"
    )


def main() -> None:
    if POLICY_PHASE == "installed":
        installed_probe()
    elif POLICY_PHASE == "removed":
        removed_probe()
    else:
        fail(f"unknown policy phase: {POLICY_PHASE!r}")


if __name__ == "__main__":
    main()
