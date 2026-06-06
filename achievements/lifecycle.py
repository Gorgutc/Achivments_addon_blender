"""Blender registration lifecycle helpers.

The module accepts ``bpy`` as an argument instead of importing it, which keeps
the package importable in normal Python tests while root ``__init__.py`` stays
the Blender runtime entrypoint.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any


def is_class_registered(cls: type) -> bool:
    return bool(getattr(cls, "is_registered", False))


def register_classes(bpy: Any, classes: Iterable[type]) -> None:
    for cls in classes:
        if is_class_registered(cls):
            continue
        try:
            bpy.utils.register_class(cls)
        except RuntimeError as exc:
            if "already registered" not in str(exc):
                raise


def unregister_classes(bpy: Any, classes: Iterable[type]) -> None:
    for cls in reversed(tuple(classes)):
        if not is_class_registered(cls):
            continue
        try:
            bpy.utils.unregister_class(cls)
        except RuntimeError as exc:
            if "missing bl_rna" not in str(exc):
                raise


def set_scene_property_once(bpy: Any, name: str, prop: Any) -> None:
    if not hasattr(bpy.types.Scene, name):
        setattr(bpy.types.Scene, name, prop)


def delete_scene_property_if_present(bpy: Any, name: str) -> None:
    if hasattr(bpy.types.Scene, name):
        delattr(bpy.types.Scene, name)


def append_handler_once(collection: list, callback: Callable[..., Any]) -> None:
    if callback not in collection:
        collection.append(callback)
    while collection.count(callback) > 1:
        collection.remove(callback)


def remove_handler_all(collection: list, callback: Callable[..., Any]) -> None:
    while callback in collection:
        collection.remove(callback)


def append_header_once(header_type: Any, callback: Callable[..., Any]) -> None:
    callbacks = _header_callbacks(header_type)
    if callback not in callbacks:
        header_type.append(callback)
        callbacks = _header_callbacks(header_type)
    while callbacks.count(callback) > 1:
        header_type.remove(callback)
        callbacks = _header_callbacks(header_type)


def remove_header_all(header_type: Any, callback: Callable[..., Any]) -> None:
    callbacks = _header_callbacks(header_type)
    while callback in callbacks:
        header_type.remove(callback)
        callbacks = _header_callbacks(header_type)


def _header_callbacks(header_type: Any) -> list:
    callbacks = getattr(header_type, "_dyn_ui_initialize", [])
    if not isinstance(callbacks, (list, tuple)):
        return []
    return list(callbacks)


def register_timer_once(
    bpy: Any,
    callback: Callable[..., float | None],
    *,
    first_interval: float,
    persistent: bool,
) -> None:
    if not bpy.app.timers.is_registered(callback):
        bpy.app.timers.register(callback, first_interval=first_interval, persistent=persistent)


def unregister_timer_if_registered(bpy: Any, callback: Callable[..., float | None]) -> None:
    if bpy.app.timers.is_registered(callback):
        bpy.app.timers.unregister(callback)


def add_draw_handler_once(
    bpy: Any,
    current_handle: Any,
    callback: Callable[..., Any],
) -> Any:
    if current_handle is not None:
        return current_handle
    return bpy.types.SpaceView3D.draw_handler_add(callback, (), "WINDOW", "POST_PIXEL")


def remove_draw_handler_if_present(bpy: Any, current_handle: Any) -> None:
    if current_handle is not None:
        bpy.types.SpaceView3D.draw_handler_remove(current_handle, "WINDOW")


def clear_preview_collections(bpy: Any, preview_collections: dict[str, Any]) -> None:
    for pcoll in list(preview_collections.values()):
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
