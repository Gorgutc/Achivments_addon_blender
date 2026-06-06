from __future__ import annotations

import contextlib
import importlib.util
import io
import os
import sys
from pathlib import Path

import bpy

ROOT = Path(os.environ["ACHIEVEMENTS_ADDON_ROOT"])
ADDON_PATH = ROOT / "__init__.py"
MODULE_NAME = "achievements_blender_smoke_engine_addon"
ERROR_MARKER = "[Achievements] complex step check error"


def fail(message: str) -> None:
    print(f"[smoke_engine:FAIL] {message}")
    raise SystemExit(1)


def load_addon():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, ADDON_PATH)
    if spec is None or spec.loader is None:
        fail("cannot create module spec")
    module = importlib.util.module_from_spec(spec)
    sys.modules[MODULE_NAME] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    module = load_addon()
    module.register()
    try:
        scene = bpy.context.scene
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            module._check_complex_step(
                "compositing_node_render",
                "has_compositor",
                scene,
            )
            module._check_complex_step(
                "render_passes",
                "has_5_passes",
                scene,
            )
            module.check_complex_achievements(scene)
        output = buffer.getvalue()
        if ERROR_MARKER in output:
            fail(f"complex step checks emitted error marker: {output.strip()}")
    finally:
        module.unregister()

    print("[smoke_engine:PASS] complex rule evaluation emits no error markers")


if __name__ == "__main__":
    main()
