bl_info = {
    "name": "Achievements",
    "author": "axximus",
    "version": (0, 1, 0),
    "blender": (4, 5, 0),
    "location": "3D Viewport > Header (trophy icon)",
    "description": "Gamification addon: 100 achievements, XP & levels, rewards, tutorials",
    "category": "Interface",
}

import bpy
import os
import sys
import time
import math
import bmesh
import gpu
import blf
import hashlib
from bpy.app.handlers import persistent
from gpu_extras.batch import batch_for_shader

# ============================================================
#  ACHIEVEMENTS ADDON — v0.1 (pre-release)
#  Blender 4.5 / 5.0 / 5.1
#
#  v0.1:
#  - 100 achievements across 5 categories
#  - XP & Level system (10 levels)
#  - Difficulty labels (easy/medium/hard) on cards
#  - Multi-step progress for complex achievements
#  - Reward protection (hash-based unlock verification)
#  - Immediate stat-achievement check on depsgraph update
#  - All code comments and developer docs in English
#  - Optimized depsgraph handler (reduced overhead)
#  v9: Categories with accordion UI, 5 complex achievements
#  v8: Steam-style notifications, pin system, material overwrite
# ============================================================


# =============================================
#  PATHS
# =============================================
# Data persists in user's home directory — survives Blender reinstalls.
# Only lost if the directory itself is manually deleted.
DATA_DIR = os.path.join(os.path.expanduser("~"), "BlenderAchievements")
DATA_FILE = os.path.join(DATA_DIR, "achievements_data.json")
ICONS_DIR = os.path.join(DATA_DIR, "textures")
REWARDS_DIR = os.path.join(DATA_DIR, "rewards")


# =============================================
#  GRID LAYOUT SETTINGS
# =============================================
GRID_COLS = 2       # 2 cards per row (~400px each)
GRID_ROWS = 5
PAGE_SIZE = GRID_COLS * GRID_ROWS  # 10 per page

# Card dimensions in UI units (1 unit ~ 20px at default scale)
# Icon 100x100 = 5.0 units
# Card width proportional: 100/128 * 400 ~ 312px ~ 15.6 units
CARD_WIDTH_UNITS = 15.6
CARD_ICON_UNITS = 5.0    # 100px = 5.0 units


# =============================================
#  NOTIFICATION SETTINGS (Steam-style, bottom-left corner)
# =============================================
NOTIFY_DURATION = 8.0
NOTIFY_SLIDE_IN = 0.4     # slide-in animation seconds
NOTIFY_ICON_SIZE = 100    # 100x100
NOTIFY_PADDING = 16       # 16px padding
NOTIFY_TEXT_GAP = 8       # 8px between text lines
NOTIFY_HEIGHT = NOTIFY_ICON_SIZE + NOTIFY_PADDING * 2  # 132
NOTIFY_WIDTH = 500
NOTIFY_MARGIN = 20        # screen edge margin

# Pinned achievement overlay (same size as notifications)
PIN_MARGIN_X = NOTIFY_MARGIN
PIN_MARGIN_Y = NOTIFY_MARGIN


# =============================================
#  REWARD PROTECTION
# =============================================
# Secret salt for hash-based unlock verification.
# Rewards can only be applied if the achievement's unlock hash matches.
# This prevents manual JSON editing to claim rewards without earning them.
# NOTE: For stronger protection, obfuscate this salt or derive it
# from machine-specific data (e.g., os.getlogin() + platform.node()).
_REWARD_SALT = "BlenderAch2026_"


def _make_unlock_hash(ach_id):
    """Generate a verification hash for an unlocked achievement."""
    raw = f"{_REWARD_SALT}{ach_id}{os.getlogin()}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


def _verify_unlock(ach_id, stored_hash):
    """Verify that an achievement was legitimately unlocked."""
    return _make_unlock_hash(ach_id) == stored_hash


# =============================================
#  CATALOG
# =============================================
_ADDON_DIR = os.path.dirname(os.path.abspath(__file__))
if _ADDON_DIR not in sys.path:
    sys.path.insert(0, _ADDON_DIR)

from achievements.catalog import (
    ACHIEVEMENTS_DEF,
    ACH_CATEGORIES,
    LESSONS_DEF,
    LESSON_CATEGORIES,
    REWARD_CATEGORIES,
)
from achievements import engine as ach_engine
from achievements import events as ach_events
from achievements import lifecycle as ach_lifecycle
from achievements import persistence as ach_persistence
from achievements import rewards as ach_rewards
from achievements import ui as ach_ui


_REWARD_MANIFEST = ach_rewards.RewardManifest.from_achievements(ACHIEVEMENTS_DEF)
_REWARD_ASSET_CACHE = ach_rewards.AssetCache()

# =============================================
#  XP & LEVEL SYSTEM
# =============================================
# Difficulty -> XP points mapping
DIFFICULTY_XP = {
    "easy": 5,
    "medium": 10,
    "hard": 20,
}

# Level thresholds: XP needed FROM this level TO the next
# Level 1->2: 20, 2->3: 40, 3->4: 80, ... (doubles each time)
XP_LEVELS = []
_xp_accum = 0
for _lvl in range(1, 11):
    _threshold = 20 * (2 ** (_lvl - 1))  # 20, 40, 80, 160, 320, 640, 1280, 2560, 5120, 10240
    XP_LEVELS.append({"level": _lvl, "xp_start": _xp_accum, "xp_end": _xp_accum + _threshold})
    _xp_accum += _threshold
# Total XP for level 10 cap: 20460

# Level rank titles (Russian)
LEVEL_TITLES = {
    1:  "Новичок",
    2:  "Начинающий",
    3:  "Ньюблинг",
    4:  "Ученик",
    5:  "Умелец",
    6:  "Мастеровой",
    7:  "Эксперт",
    8:  "Виртуоз",
    9:  "Гуру",
    10: "Легенда",
}


def _calc_xp():
    """Calculate total XP from unlocked achievements."""
    total = 0
    for ach in ACHIEVEMENTS_DEF:
        if ach["id"] in stats.unlocked:
            total += DIFFICULTY_XP.get(ach.get("difficulty", "medium"), 10)
    return total


def _calc_level(xp):
    """Calculate current level and progress within that level."""
    for entry in XP_LEVELS:
        if xp < entry["xp_end"]:
            lvl = entry["level"]
            progress = (xp - entry["xp_start"]) / (entry["xp_end"] - entry["xp_start"])
            return lvl, progress, entry["xp_end"] - entry["xp_start"], xp - entry["xp_start"]
    # Max level reached
    return 10, 1.0, 0, 0


def _difficulty_label(diff):
    """Return Russian label + icon for difficulty."""
    return {
        "easy": ("Легко", "SOLO_ON"),
        "medium": ("Средне", "TIME"),
        "hard": ("Сложно", "ERROR"),
    }.get(diff, ("", "NONE"))




# =============================================
#  CATALOG DEFINITIONS
# =============================================
# Achievement and lesson definitions live in achievements/catalog.py.
# The imported legacy names above keep the current Blender runtime code stable.



# =============================================
#  STATS
# =============================================
class Stats:
    vertices_created = 0
    vertices_deleted = 0
    edges_created = 0
    faces_created = 0
    meshes_1000plus = 0
    materials_applied = 0
    time_spent = 0
    renders_completed = 0   # new stat for render tracking
    _session_start = 0.0
    _last_activity = 0.0    # timestamp of last user action (depsgraph update)
    _time_at_session_start = 0  # time_spent snapshot when session started (for weekend_marathon)
    _prev_verts = {}
    _prev_edges = {}
    _prev_faces = {}
    _prev_mats = set()
    unlocked = set()        # set of achievement IDs
    unlock_hashes = {}      # {ach_id: hash} for reward protection
    rewards_claimed = set()
    pinned_ach_id = ""      # pinned achievement ID (or "")
    daily_sessions = []     # list of date strings "YYYY-MM-DD" when Blender was opened
    _session_date = ""      # current date for daily tracking
    _speed_model_start = 0.0   # timestamp when speed modeler tracking started
    _speed_model_verts = 0     # vertex count at speed model start

stats = Stats()


# =============================================
#  SAVE / LOAD
# =============================================
# Maximum idle gap (seconds). If the user hasn't touched anything for
# longer than this, the elapsed time is NOT counted.
_IDLE_TIMEOUT = 120  # 2 minutes


def _on_user_activity():
    """Called from depsgraph handler when real user changes are detected."""
    ach_events.record_user_activity(stats, now=time.time(), idle_timeout=_IDLE_TIMEOUT)


def _flush_session_time():
    """Finalize the current activity window (called on save / timer)."""
    ach_events.flush_session_time(stats, now=time.time(), idle_timeout=_IDLE_TIMEOUT)


def _ensure_data_dirs():
    ach_persistence.ensure_data_dirs(DATA_DIR)


def save_data():
    """Persist all stats, unlocks, and rewards to JSON file."""
    _flush_session_time()
    try:
        _ensure_data_dirs()
        ach_persistence.atomic_write_json(DATA_FILE, ach_persistence.payload_from_stats(stats))
    except Exception as e:
        print(f"[Achievements] Save error: {e}")


def load_data():
    """Load stats and progress from JSON file."""
    if not os.path.exists(DATA_FILE):
        print("[Achievements] Data file not found — new profile")
        return
    try:
        payload, load_report = ach_persistence.load_payload(
            DATA_FILE, make_unlock_hash=_make_unlock_hash)
        apply_report = ach_persistence.apply_payload_to_stats(
            stats, payload, make_unlock_hash=_make_unlock_hash)
        if load_report.recovered_corrupt:
            print(f"[Achievements] Recovered corrupt data: {load_report.corrupt_path}")
        if load_report.migrated or apply_report.migrated:
            print("[Achievements] Migrated persistence schema")
            save_data()

        print(f"[Achievements] Loaded. Achievements: {len(stats.unlocked)}")
    except Exception as e:
        print(f"[Achievements] Load error: {e}")


# =============================================
#  NOTIFICATIONS (GPU draw) — bottom-left Steam-style
# =============================================
_pending_notifications = []
_draw_handler = None
_draw_handler_pin = None
_header_button_registered = False
_addon_registered = False


def _add_notification(ach):
    """Queue a notification popup for a newly unlocked achievement."""
    _pending_notifications.append({"ach": ach, "start_time": time.time()})
    _tag_redraw_all()


def _tag_redraw_all():
    """Force redraw of all 3D viewports."""
    try:
        for w in bpy.context.window_manager.windows:
            for a in w.screen.areas:
                if a.type == 'VIEW_3D':
                    a.tag_redraw()
    except Exception:
        pass


def _draw_rect(x, y, w, h, color):
    """Draw a filled rectangle using GPU module."""
    shader = gpu.shader.from_builtin('UNIFORM_COLOR')
    verts = ((x, y), (x + w, y), (x, y + h), (x + w, y + h))
    idx = ((0, 1, 2), (2, 1, 3))
    batch = batch_for_shader(shader, 'TRIS', {"pos": verts}, indices=idx)
    gpu.state.blend_set('ALPHA')
    shader.uniform_float("color", color)
    batch.draw(shader)


def _reward_type_label(rtype):
    """Return a human-readable Russian label for reward type."""
    return ach_ui.reward_type_label(rtype)


def _ease_out_cubic(t):
    """Cubic ease-out for smooth slide-in animation."""
    return ach_ui.ease_out_cubic(t)


def _draw_notifications():
    """GPU draw callback: render all pending notification popups."""
    if not _pending_notifications:
        return
    now = time.time()
    expired = []
    region = bpy.context.region
    if region is None:
        return

    for i, notif in enumerate(_pending_notifications):
        elapsed = now - notif["start_time"]
        if elapsed > NOTIFY_DURATION:
            expired.append(i)
            continue
        ach = notif["ach"]

        frame = ach_ui.notification_frame(i, elapsed)
        alpha = frame.alpha
        nx = frame.x
        ny = frame.y

        # Background
        _draw_rect(nx, ny, NOTIFY_WIDTH, NOTIFY_HEIGHT, (0.10, 0.12, 0.16, 0.95 * alpha))
        # Accent — left stripe (green for notifications)
        _draw_rect(nx, ny, 4, NOTIFY_HEIGHT, (0.3, 0.8, 0.45, alpha))

        # Icon placeholder 100x100
        icon_x, icon_y, _, _ = frame.icon_rect
        _draw_rect(icon_x, icon_y, NOTIFY_ICON_SIZE, NOTIFY_ICON_SIZE,
                   (0.28, 0.30, 0.34, 0.7 * alpha))

        font_id = 0
        tx = frame.text_x

        # 3 lines, vertically centered
        line_heights = [20, 20, 16]
        total_text_h = sum(line_heights) + NOTIFY_TEXT_GAP * (len(line_heights) - 1)
        text_top = ny + (NOTIFY_HEIGHT + total_text_h) / 2

        blf.color(font_id, 0.3, 0.8, 0.45, alpha)
        blf.size(font_id, 20)
        y1 = text_top - line_heights[0]
        blf.position(font_id, tx, y1, 0)
        blf.draw(font_id, "ДОСТИЖЕНИЕ ПОЛУЧЕНО")

        blf.color(font_id, 0.95, 0.95, 0.95, alpha)
        blf.size(font_id, 20)
        y2 = y1 - NOTIFY_TEXT_GAP - line_heights[1]
        blf.position(font_id, tx, y2, 0)
        blf.draw(font_id, ach_ui.overlay_title_text(ach["title"]))

        blf.color(font_id, 0.6, 0.63, 0.68, alpha)
        blf.size(font_id, 16)
        y3 = y2 - NOTIFY_TEXT_GAP - line_heights[2]
        blf.position(font_id, tx, y3, 0)
        blf.draw(font_id, ach_ui.overlay_description_text(ach["description"]))

    for idx in reversed(expired):
        _pending_notifications.pop(idx)
    gpu.state.blend_set('NONE')


# =============================================
#  PINNED ACHIEVEMENT OVERLAY (GPU)
# =============================================
def _draw_pinned_achievement():
    """GPU draw callback: render pinned achievement card in viewport."""
    if not stats.pinned_ach_id:
        return
    ach = next((a for a in ACHIEVEMENTS_DEF if a["id"] == stats.pinned_ach_id), None)
    if not ach:
        return
    # Auto-unpin when achievement is completed
    if ach["id"] in stats.unlocked:
        stats.pinned_ach_id = ""
        save_data()
        return

    region = bpy.context.region
    if region is None:
        return

    frame = ach_ui.pinned_frame(len(_pending_notifications))
    px = frame.x
    py = frame.y

    # Background — same size as notification
    _draw_rect(px, py, NOTIFY_WIDTH, NOTIFY_HEIGHT, (0.12, 0.14, 0.18, 0.85))
    # Left accent stripe (yellow for pinned)
    _draw_rect(px, py, 4, NOTIFY_HEIGHT, (0.9, 0.75, 0.2, 1.0))

    # Icon 100x100 (same as notifications)
    icon_x, icon_y, _, _ = frame.icon_rect
    _draw_rect(icon_x, icon_y, NOTIFY_ICON_SIZE, NOTIFY_ICON_SIZE,
               (0.28, 0.30, 0.34, 0.7))

    font_id = 0
    tx = frame.text_x

    # Progress calculation — depends on check_type
    if ach.get("check_type") == "complex":
        # Complex: count completed steps
        steps = ach.get("steps", [])
        if steps:
            done_steps = sum(1 for s in steps if _check_complex_step(ach.get("complex_id", ""), s["check"], bpy.context.scene))
            progress = done_steps / len(steps)
        else:
            progress = 0
        pct = int(progress * 100)
    else:
        value = getattr(stats, ach["stat_key"], 0)
        goal = ach["goal"]
        progress = min(value / goal, 1.0) if goal > 0 else 0
        pct = int(progress * 100)

    # Text block: 3 lines — vertically centered relative to icon
    line_heights = [20, 16, 22]  # last = bar + percentage text
    total_text_h = sum(line_heights) + NOTIFY_TEXT_GAP * (len(line_heights) - 1)
    text_top = py + (NOTIFY_HEIGHT + total_text_h) / 2

    # Line 1: Title (20px, white)
    blf.color(font_id, 0.95, 0.95, 0.95, 1.0)
    blf.size(font_id, 20)
    y1 = text_top - line_heights[0]
    blf.position(font_id, tx, y1, 0)
    blf.draw(font_id, ach_ui.overlay_title_text(ach["title"]))

    # Line 2: Description (16px, gray)
    blf.color(font_id, 0.6, 0.63, 0.68, 1.0)
    blf.size(font_id, 16)
    y2 = y1 - NOTIFY_TEXT_GAP - line_heights[1]
    blf.position(font_id, tx, y2, 0)
    blf.draw(font_id, ach_ui.overlay_description_text(ach["description"]))

    # Line 3: Progress bar + percentage
    bar_y = y2 - NOTIFY_TEXT_GAP - 14
    bar_x = tx
    bar_w_max = frame.progress_bar_width  # space for "%"
    bar_h = 8
    _draw_rect(bar_x, bar_y, bar_w_max, bar_h, (0.25, 0.27, 0.30, 1.0))
    _draw_rect(bar_x, bar_y, bar_w_max * progress, bar_h, (0.9, 0.75, 0.2, 1.0))

    # Percentage text right of bar
    blf.color(font_id, 0.7, 0.7, 0.7, 1.0)
    blf.size(font_id, 14)
    blf.position(font_id, bar_x + bar_w_max + 8, bar_y - 2, 0)
    blf.draw(font_id, f"{pct}%")

    gpu.state.blend_set('NONE')


# =============================================
#  ACHIEVEMENT CHECKING — stat-based
# =============================================
def check_achievements():
    """Check all stat-based achievements and unlock any that are met."""
    for result in ach_engine.pending_stat_unlocks(ACHIEVEMENTS_DEF, stats):
        ach = next(a for a in ACHIEVEMENTS_DEF if a["id"] == result.achievement_id)
        _unlock_achievement(result.achievement_id, ach)


def _unlock_achievement(aid, ach):
    """Mark an achievement as unlocked, generate hash, notify, and save."""
    stats.unlocked.add(aid)
    stats.unlock_hashes[aid] = _make_unlock_hash(aid)
    _add_notification(ach)
    print(f"    >>> ACHIEVEMENT: {ach['title']}")
    save_data()


# =============================================
#  COMPLEX ACHIEVEMENT CHECKING (scene state)
# =============================================

def _check_streak(daily_sessions, required_days):
    """Check if there's a consecutive streak of required_days in daily_sessions list."""
    return ach_engine.has_streak(daily_sessions, required_days)


def _check_complex_step(complex_id, step_check, scene):
    """Check a single step of a complex achievement. Returns True/False.
    Used both for progress display and for completion check.

    HOW TO ADD A NEW COMPLEX CHECK:
    1. Add a new elif clause for the complex_id
    2. Inside, handle each step_check string used in the achievement's 'steps' list
    3. Use scene.objects, bpy.data, etc. to inspect current Blender state
    4. Return True if the condition is met, False otherwise
    """
    try:
        # -------------------------------------------------------
        # HELPER: scan all GeoNodes trees across the scene
        # -------------------------------------------------------
        def _gn_trees():
            """Yield all Geometry Nodes node_groups in the scene."""
            for obj in scene.objects:
                if obj.type != 'MESH':
                    continue
                for mod in obj.modifiers:
                    if mod.type == 'NODES' and mod.node_group:
                        yield mod.node_group

        def _gn_has_node(bl_idname):
            """Check if any GN tree contains a node with given bl_idname."""
            for ng in _gn_trees():
                for node in ng.nodes:
                    if node.bl_idname == bl_idname:
                        return True
            return False

        def _gn_has_node_type(type_name):
            """Check if any GN tree contains a node whose type == type_name."""
            for ng in _gn_trees():
                for node in ng.nodes:
                    if node.type == type_name:
                        return True
            return False

        def _gn_has_node_label_or_name(partial_name):
            """Check by partial name match (case-insensitive)."""
            partial = partial_name.lower()
            for ng in _gn_trees():
                for node in ng.nodes:
                    if partial in node.name.lower() or partial in node.label.lower() or partial in node.bl_idname.lower():
                        return True
            return False

        def _mat_has_node(bl_idname):
            """Check if any material in the scene has a node with given bl_idname."""
            for mat in bpy.data.materials:
                if mat.use_nodes and mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.bl_idname == bl_idname:
                            return True
            return False

        def _mat_has_node_type(type_name):
            """Check if any material has a node whose type matches."""
            for mat in bpy.data.materials:
                if mat.use_nodes and mat.node_tree:
                    for node in mat.node_tree.nodes:
                        if node.type == type_name:
                            return True
            return False

        # -------------------------------------------------------
        # ORIGINAL COMPLEX ACHIEVEMENTS (V0.1 base)
        # -------------------------------------------------------
        if complex_id == "smooth_cube":
            if step_check == "has_mesh":
                return any(o.type == 'MESH' for o in scene.objects)
            if step_check == "has_subsurf":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'SUBSURF' for m in obj.modifiers):
                        return True
                return False

        elif complex_id == "sphere_from_cube":
            if step_check == "has_mesh":
                return any(o.type == 'MESH' for o in scene.objects)
            if step_check == "has_subsurf":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'SUBSURF' for m in obj.modifiers):
                        return True
                return False
            if step_check == "has_smooth":
                for obj in scene.objects:
                    if obj.type != 'MESH':
                        continue
                    for m in obj.modifiers:
                        if m.type == 'SMOOTH':
                            return True
                        # Blender 5.0: Smooth by Angle is a Geometry Nodes modifier
                        if m.type == 'NODES' and m.node_group and 'smooth' in m.node_group.name.lower():
                            return True
                return False

        elif complex_id == "first_render":
            if step_check == "has_mesh":
                return any(o.type == 'MESH' for o in scene.objects)
            if step_check == "has_material_on_mesh":
                for obj in scene.objects:
                    if obj.type == 'MESH' and obj.data.materials and obj.data.materials[0]:
                        return True
                return False
            if step_check == "has_light":
                return any(o.type == 'LIGHT' for o in scene.objects)
            if step_check == "render_done":
                return stats.renders_completed > 0

        elif complex_id == "architect":
            if step_check == "has_collection":
                return len(bpy.data.collections) > 0
            if step_check == "has_3_meshes":
                for coll in bpy.data.collections:
                    mesh_objs = [o for o in coll.objects if o.type == 'MESH']
                    if len(mesh_objs) >= 3:
                        return True
                return False
            if step_check == "has_unique_mats":
                for coll in bpy.data.collections:
                    mesh_objs = [o for o in coll.objects if o.type == 'MESH']
                    mats = set()
                    for obj in mesh_objs:
                        if obj.data.materials and obj.data.materials[0]:
                            mats.add(obj.data.materials[0].name)
                    if len(mats) >= 3:
                        return True
                return False
            if step_check == "has_array":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'ARRAY' for m in obj.modifiers):
                        return True
                return False

        elif complex_id == "procedural_master":
            if step_check == "has_mesh_with_mat":
                for obj in scene.objects:
                    if obj.type == 'MESH' and obj.data.materials and obj.data.materials[0]:
                        return True
                return False
            if step_check == "has_geonodes_mod":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for mod in obj.modifiers:
                            if mod.type == 'NODES' and mod.node_group:
                                return True
                return False
            if step_check == "has_3_nodes":
                for obj in scene.objects:
                    if obj.type != 'MESH':
                        continue
                    for mod in obj.modifiers:
                        if mod.type == 'NODES' and mod.node_group:
                            ng = mod.node_group
                            real_nodes = [n for n in ng.nodes
                                          if n.type not in ('GROUP_INPUT', 'GROUP_OUTPUT',
                                                            'FRAME', 'REROUTE')]
                            if len(real_nodes) >= 3:
                                return True
                return False
            if step_check == "has_links":
                for obj in scene.objects:
                    if obj.type != 'MESH':
                        continue
                    for mod in obj.modifiers:
                        if mod.type == 'NODES' and mod.node_group:
                            if len(mod.node_group.links) > 0:
                                return True
                return False

        # -------------------------------------------------------
        # MODIFIER-BASED COMPLEX ACHIEVEMENTS
        # -------------------------------------------------------
        elif complex_id == "five_modifier_stack":
            if step_check == "has_mesh":
                return any(o.type == 'MESH' for o in scene.objects)
            if step_check == "five_modifier_stack":
                for obj in scene.objects:
                    if obj.type == 'MESH' and len(obj.modifiers) >= 5:
                        return True
                return False

        elif complex_id == "mirror_subdivision":
            if step_check == "has_mirror":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'MIRROR' for m in obj.modifiers):
                        return True
                return False
            if step_check == "has_subsurf":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'SUBSURF' for m in obj.modifiers):
                        return True
                return False

        elif complex_id == "boolean_master":
            if step_check == "has_boolean":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for m in obj.modifiers:
                            if m.type == 'BOOLEAN':
                                return True
                return False

        elif complex_id == "solidify_bevel_combo":
            if step_check == "has_solidify":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'SOLIDIFY' for m in obj.modifiers):
                        return True
                return False
            if step_check == "has_bevel":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'BEVEL' for m in obj.modifiers):
                        return True
                return False

        elif complex_id == "screw_modifier":
            if step_check == "has_screw":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'SCREW' for m in obj.modifiers):
                        return True
                return False

        elif complex_id == "ten_modifier_stack":
            if step_check == "ten_modifier_stack":
                for obj in scene.objects:
                    if obj.type == 'MESH' and len(obj.modifiers) >= 10:
                        return True
                return False

        elif complex_id == "shrinkwrap_use":
            if step_check == "has_shrinkwrap":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for m in obj.modifiers:
                            if m.type == 'SHRINKWRAP' and m.target is not None:
                                return True
                return False

        elif complex_id == "armature_modifier":
            if step_check == "has_armature":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for m in obj.modifiers:
                            if m.type == 'ARMATURE' and m.object is not None:
                                return True
                return False

        elif complex_id == "curve_deform":
            if step_check == "has_curve_mod":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for m in obj.modifiers:
                            if m.type == 'CURVE' and m.object is not None:
                                return True
                return False

        elif complex_id == "skin_modifier":
            if step_check == "has_skin":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'SKIN' for m in obj.modifiers):
                        return True
                return False

        elif complex_id == "weighted_normals":
            if step_check == "has_weighted_normal":
                for obj in scene.objects:
                    if obj.type == 'MESH' and any(m.type == 'WEIGHTED_NORMAL' for m in obj.modifiers):
                        return True
                return False

        elif complex_id == "array_circle":
            if step_check == "has_array_with_empty":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for m in obj.modifiers:
                            if m.type == 'ARRAY' and m.use_object_offset and m.offset_object is not None:
                                return True
                return False

        elif complex_id == "multiresolution_sculpt":
            if step_check == "has_multires":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for m in obj.modifiers:
                            if m.type == 'MULTIRES' and m.levels > 1:
                                return True
                return False

        elif complex_id == "shape_key_animation":
            if step_check == "has_shape_keys":
                for obj in scene.objects:
                    if obj.type == 'MESH' and obj.data.shape_keys and len(obj.data.shape_keys.key_blocks) >= 2:
                        return True
                return False
            if step_check == "has_shape_key_anim":
                for obj in scene.objects:
                    if obj.type == 'MESH' and obj.data.shape_keys:
                        sk = obj.data.shape_keys
                        if sk.animation_data and sk.animation_data.action:
                            return True
                return False

        elif complex_id == "retopology_work":
            if step_check == "has_snap_face":
                ts = scene.tool_settings
                # Blender 4.x/5.x: snap_elements is a set
                try:
                    if ts.use_snap and 'FACE' in ts.snap_elements:
                        return True
                except:
                    pass
                return False

        elif complex_id == "particle_system":
            if step_check == "has_particles":
                for obj in scene.objects:
                    if obj.type == 'MESH' and len(obj.particle_systems) > 0:
                        return True
                # Also check if there's a FORCE_WIND object
                return False

        elif complex_id == "collection_organizer":
            if step_check == "has_5_collections":
                filled = sum(1 for c in bpy.data.collections if len(c.objects) > 0)
                return filled >= 5

        elif complex_id == "custom_origin":
            if step_check == "custom_origin_set":
                # Can only detect indirectly: if any mesh origin is not at world center
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        if obj.location.length > 0.001:
                            # Check if origin differs from mesh centroid (approximation)
                            return True
                return False

        elif complex_id == "linked_duplicate":
            if step_check == "has_20_linked":
                # Count objects sharing the same mesh data-block
                from collections import Counter
                mesh_users = Counter()
                for obj in scene.objects:
                    if obj.type == 'MESH' and obj.data:
                        mesh_users[obj.data.name] += 1
                return any(count >= 20 for count in mesh_users.values())

        # -------------------------------------------------------
        # RENDERING COMPLEX ACHIEVEMENTS
        # -------------------------------------------------------
        elif complex_id == "ten_lights_scene":
            if step_check == "has_10_lights":
                lights = [o for o in scene.objects if o.type == 'LIGHT']
                return len(lights) >= 10

        elif complex_id == "three_light_setup":
            if step_check == "has_3_light_types":
                light_types = set()
                for obj in scene.objects:
                    if obj.type == 'LIGHT':
                        light_types.add(obj.data.type)
                return len(light_types) >= 3

        elif complex_id == "hdri_lighting":
            if step_check == "has_hdri":
                world = scene.world
                if world and world.use_nodes and world.node_tree:
                    for node in world.node_tree.nodes:
                        if node.bl_idname == 'ShaderNodeTexEnvironment':
                            if node.image is not None:
                                return True
                return False

        elif complex_id == "depth_of_field":
            if step_check == "has_dof":
                cam = scene.camera
                if cam and cam.data.dof.use_dof:
                    if cam.data.dof.focus_object is not None or cam.data.dof.focus_distance > 0:
                        return True
                return False

        elif complex_id == "motion_blur_render":
            if step_check == "has_motion_blur":
                return scene.render.use_motion_blur

        elif complex_id == "denoiser_render":
            if step_check == "has_denoiser":
                if hasattr(scene, 'cycles') and scene.cycles.use_denoising:
                    return True
                # EEVEE Next may have its own denoiser setting
                return False

        elif complex_id == "cycles_caustics":
            if step_check == "has_caustics":
                if not hasattr(scene, 'cycles'):
                    return False
                cyc = scene.cycles
                if cyc.caustics_reflective or cyc.caustics_refractive:
                    # Also check for glass/transmission material
                    for mat in bpy.data.materials:
                        if mat.use_nodes and mat.node_tree:
                            for node in mat.node_tree.nodes:
                                if node.bl_idname == 'ShaderNodeBsdfGlass':
                                    return True
                                if node.bl_idname == 'ShaderNodeBsdfPrincipled':
                                    # Check if Transmission > 0
                                    for inp in node.inputs:
                                        if inp.name in ('Transmission', 'Transmission Weight') and inp.default_value > 0:
                                            return True
                return False

        elif complex_id == "volumetric_render":
            if step_check == "has_volume":
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.bl_idname in ('ShaderNodeVolumeScatter', 'ShaderNodeVolumeAbsorption',
                                                   'ShaderNodeVolumePrincipled'):
                                return True
                # Also check world volume
                world = scene.world
                if world and world.use_nodes and world.node_tree:
                    for node in world.node_tree.nodes:
                        if node.bl_idname in ('ShaderNodeVolumeScatter', 'ShaderNodeVolumeAbsorption',
                                               'ShaderNodeVolumePrincipled'):
                            return True
                return False

        elif complex_id == "compositing_node_render":
            if step_check == "has_compositor":
                node_tree = getattr(scene, "node_tree", None)
                if getattr(scene, "use_nodes", False) and node_tree:
                    # Check for nodes beyond default Render Layers + Composite
                    real_nodes = [n for n in node_tree.nodes
                                  if n.type not in ('R_LAYERS', 'COMPOSITE', 'VIEWER', 'OUTPUT_FILE')]
                    return len(real_nodes) > 0
                return False

        elif complex_id == "render_passes":
            if step_check == "has_5_passes":
                vl = getattr(bpy.context, "view_layer", None)
                if not vl or vl.name not in scene.view_layers:
                    vl = scene.view_layers[0] if len(scene.view_layers) else None
                if vl:
                    pass_count = 0
                    pass_attrs = [
                        'use_pass_diffuse_direct', 'use_pass_diffuse_indirect', 'use_pass_diffuse_color',
                        'use_pass_glossy_direct', 'use_pass_glossy_indirect', 'use_pass_glossy_color',
                        'use_pass_transmission_direct', 'use_pass_transmission_indirect', 'use_pass_transmission_color',
                        'use_pass_emit', 'use_pass_environment', 'use_pass_shadow',
                        'use_pass_ambient_occlusion', 'use_pass_normal', 'use_pass_vector',
                        'use_pass_uv', 'use_pass_mist', 'use_pass_object_index',
                        'use_pass_material_index', 'use_pass_z',
                    ]
                    for attr in pass_attrs:
                        if hasattr(vl, attr) and getattr(vl, attr):
                            pass_count += 1
                    return pass_count >= 5
                return False

        # -------------------------------------------------------
        # MATERIAL COMPLEX ACHIEVEMENTS
        # -------------------------------------------------------
        elif complex_id == "texture_paint":
            if step_check == "has_texture_paint":
                # Check if any image has been modified (painted on)
                for img in bpy.data.images:
                    if img.is_dirty:
                        return True
                return False

        elif complex_id == "uv_unwrap_material":
            if step_check == "has_uv":
                for obj in scene.objects:
                    if obj.type == 'MESH' and obj.data.uv_layers:
                        return True
                return False
            if step_check == "has_image_texture":
                return _mat_has_node('ShaderNodeTexImage')

        elif complex_id == "emission_material":
            if step_check == "has_emission":
                return _mat_has_node('ShaderNodeEmission')

        elif complex_id == "glass_ior":
            if step_check == "has_glass_ior":
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.bl_idname == 'ShaderNodeBsdfGlass':
                                ior_input = node.inputs.get('IOR')
                                if ior_input and 1.40 <= ior_input.default_value <= 1.60:
                                    return True
                return False

        elif complex_id == "mix_shader":
            if step_check == "has_mix_shader":
                return _mat_has_node('ShaderNodeMixShader')

        elif complex_id == "principled_bsdf_full":
            if step_check == "has_base_color":
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.bl_idname == 'ShaderNodeBsdfPrincipled':
                                bc = node.inputs.get('Base Color')
                                if bc and bc.is_linked:
                                    return True
                return False
            if step_check == "has_normal_input":
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.bl_idname == 'ShaderNodeBsdfPrincipled':
                                nm = node.inputs.get('Normal')
                                if nm and nm.is_linked:
                                    return True
                return False

        elif complex_id == "normal_map_material":
            if step_check == "has_normal_map":
                return _mat_has_node('ShaderNodeNormalMap')

        elif complex_id == "subsurface_skin":
            if step_check == "has_subsurface":
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.bl_idname == 'ShaderNodeBsdfPrincipled':
                                # Blender 4.x+: "Subsurface Weight" or "Subsurface"
                                for inp in node.inputs:
                                    if 'subsurface' in inp.name.lower() and 'color' not in inp.name.lower() and 'radius' not in inp.name.lower():
                                        if inp.default_value > 0.0 or inp.is_linked:
                                            return True
                return False

        elif complex_id == "procedural_texture":
            if step_check == "has_procedural":
                procedural_types = {
                    'ShaderNodeTexNoise', 'ShaderNodeTexVoronoi',
                    'ShaderNodeTexWave', 'ShaderNodeTexMusgrave',
                    'ShaderNodeTexChecker', 'ShaderNodeTexBrick',
                    'ShaderNodeTexGradient', 'ShaderNodeTexMagic',
                }
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.bl_idname in procedural_types:
                                return True
                return False
            if step_check == "no_image_texture":
                # The same material that has procedural nodes must NOT have Image Texture
                procedural_types = {
                    'ShaderNodeTexNoise', 'ShaderNodeTexVoronoi',
                    'ShaderNodeTexWave', 'ShaderNodeTexMusgrave',
                    'ShaderNodeTexChecker', 'ShaderNodeTexBrick',
                    'ShaderNodeTexGradient', 'ShaderNodeTexMagic',
                }
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        has_proc = any(n.bl_idname in procedural_types for n in mat.node_tree.nodes)
                        has_img = any(n.bl_idname == 'ShaderNodeTexImage' for n in mat.node_tree.nodes)
                        if has_proc and not has_img:
                            return True
                return False

        elif complex_id == "vertex_color_material":
            if step_check == "has_vertex_color":
                # Blender 4.x+: ShaderNodeVertexColor is replaced by ShaderNodeAttribute or Color Attribute
                return (_mat_has_node('ShaderNodeVertexColor')
                        or _mat_has_node('ShaderNodeAttribute'))

        elif complex_id == "displacement_material":
            if step_check == "has_displacement":
                for mat in bpy.data.materials:
                    if mat.use_nodes and mat.node_tree:
                        for node in mat.node_tree.nodes:
                            if node.bl_idname == 'ShaderNodeOutputMaterial':
                                disp = node.inputs.get('Displacement')
                                if disp and disp.is_linked:
                                    return True
                return False

        # -------------------------------------------------------
        # GEOMETRY NODES COMPLEX ACHIEVEMENTS
        # -------------------------------------------------------
        elif complex_id == "first_geonode":
            if step_check == "has_geonodes_mod":
                for obj in scene.objects:
                    if obj.type == 'MESH':
                        for mod in obj.modifiers:
                            if mod.type == 'NODES' and mod.node_group:
                                return True
                return False

        elif complex_id == "geonode_instance":
            if step_check == "has_gn_instance":
                return _gn_has_node('GeometryNodeInstanceOnPoints')

        elif complex_id == "geonode_scatter":
            if step_check == "has_gn_scatter":
                return _gn_has_node('GeometryNodeDistributePointsOnFaces')

        elif complex_id == "geonode_attribute":
            if step_check == "has_gn_attribute":
                return (_gn_has_node('GeometryNodeStoreNamedAttribute')
                        or _gn_has_node('GeometryNodeInputNamedAttribute'))

        elif complex_id == "geonode_curve_to_mesh":
            if step_check == "has_gn_curve_to_mesh":
                return _gn_has_node('GeometryNodeCurveToMesh')

        elif complex_id == "geonode_noise_deform":
            if step_check == "has_gn_noise":
                return _gn_has_node('ShaderNodeTexNoise')
            if step_check == "has_gn_set_position":
                return _gn_has_node('GeometryNodeSetPosition')

        elif complex_id == "geonode_group_input":
            if step_check == "has_gn_group_input":
                for ng in _gn_trees():
                    for node in ng.nodes:
                        if node.type == 'GROUP_INPUT':
                            # Check if it has more than the default geometry socket
                            if len(node.outputs) > 2:  # geometry + blank
                                return True
                return False

        elif complex_id == "geonode_convex_hull":
            if step_check == "has_gn_convex_hull":
                return _gn_has_node('GeometryNodeConvexHull')

        elif complex_id == "geonode_boolean_node":
            if step_check == "has_gn_boolean":
                return _gn_has_node('GeometryNodeMeshBoolean')

        elif complex_id == "geonode_realize_instances":
            if step_check == "has_gn_realize":
                return _gn_has_node('GeometryNodeRealizeInstances')

        elif complex_id == "geonode_field_math":
            if step_check == "has_gn_field_math":
                return (_gn_has_node('GeometryNodeFieldAtIndex')
                        or _gn_has_node('GeometryNodeSampleIndex')
                        or _gn_has_node_label_or_name('evaluate'))

        elif complex_id == "geonode_domain_switch":
            if step_check == "has_gn_domain_switch":
                return (_gn_has_node('GeometryNodeSampleIndex')
                        or _gn_has_node_label_or_name('transfer attribute')
                        or _gn_has_node_label_or_name('interpolate domain'))

        elif complex_id == "geonode_simulation":
            if step_check == "has_gn_simulation":
                return (_gn_has_node('GeometryNodeSimulationInput')
                        or _gn_has_node('GeometryNodeSimulationOutput'))

        # -------------------------------------------------------
        # TIME-BASED COMPLEX ACHIEVEMENTS
        # -------------------------------------------------------
        elif complex_id == "night_session":
            if step_check == "is_night_session":
                import datetime
                now = datetime.datetime.now()
                hour = now.hour
                # Night session: 22:00 - 02:00
                return hour >= 22 or hour < 2

        elif complex_id == "early_bird":
            if step_check == "is_early_bird":
                import datetime
                now = datetime.datetime.now()
                return 5 <= now.hour < 8

        elif complex_id == "weekend_marathon":
            if step_check == "is_weekend_marathon":
                import datetime
                now = datetime.datetime.now()
                # Check if today is weekend (5=Saturday, 6=Sunday)
                if now.weekday() >= 5:
                    # Active time this session = current time_spent minus snapshot at start
                    active_session = stats.time_spent - stats._time_at_session_start
                    return active_session >= 6 * 3600
                return False

        elif complex_id == "daily_streak_7":
            if step_check == "has_7_day_streak":
                return _check_streak(stats.daily_sessions, 7)

        elif complex_id == "daily_streak_30":
            if step_check == "has_30_day_streak":
                return _check_streak(stats.daily_sessions, 30)

        elif complex_id == "speed_modeler":
            if step_check == "is_speed_modeler":
                # Check if user created 500+ vertices in under 5 minutes
                if stats._speed_model_start > 0:
                    elapsed = time.time() - stats._speed_model_start
                    gained = stats.vertices_created - stats._speed_model_verts
                    if elapsed <= 300 and gained >= 500:
                        return True
                    # Reset tracker if more than 5 minutes elapsed
                    if elapsed > 300:
                        stats._speed_model_start = time.time()
                        stats._speed_model_verts = stats.vertices_created
                return False

        elif complex_id == "blender_legend":
            if step_check == "has_50_unlocked":
                return len(stats.unlocked) >= 50

    except Exception as e:
        print(f"[Achievements] complex step check error ({complex_id}/{step_check}): {e}")
    return False

def _check_complex(complex_id, scene):
    """Check if ALL steps of a complex achievement are complete."""
    ach = next((a for a in ACHIEVEMENTS_DEF if a.get("complex_id") == complex_id), None)
    if not ach:
        return False
    result = ach_engine.evaluate_complex_achievement(
        ach,
        lambda cid, step_check: _check_complex_step(cid, step_check, scene),
    )
    return result.achieved


def check_complex_achievements(scene=None):
    """Check all complex achievements for completion."""
    if scene is None:
        scene = bpy.context.scene
    for ach in ACHIEVEMENTS_DEF:
        if ach.get("check_type") != "complex":
            continue
        aid = ach["id"]
        if aid in stats.unlocked:
            continue
        # first_render is checked separately in render_complete handler
        if ach.get("complex_id") == "first_render":
            # Still check — it will pass once renders_completed > 0
            pass
        if _check_complex(ach["complex_id"], scene):
            _unlock_achievement(aid, ach)


# =============================================
#  GEOMETRY TRACKING (depsgraph handler)
# =============================================
def _get_mesh_counts(obj):
    """Get vertex/edge/face counts, handling Edit Mode via bmesh."""
    if obj.mode == "EDIT":
        bm = bmesh.from_edit_mesh(obj.data)
        return len(bm.verts), len(bm.edges), len(bm.faces)
    return len(obj.data.vertices), len(obj.data.edges), len(obj.data.polygons)


@persistent
def on_depsgraph_update(scene, depsgraph):
    """Track geometry changes on every depsgraph update.
    This fires frequently — optimized to minimize overhead."""
    changed = False
    for obj in scene.objects:
        if obj.type != "MESH" or obj.data is None:
            continue
        try:
            cv, ce, cf = _get_mesh_counts(obj)
        except Exception:
            continue
        name = obj.name

        # --- Vertices ---
        pv = stats._prev_verts.get(name)
        if pv is None:
            stats._prev_verts[name] = cv
        else:
            d = cv - pv
            if d > 0:
                stats.vertices_created += d
                changed = True
            elif d < 0:
                stats.vertices_deleted += abs(d)
                changed = True
            if cv >= 1000 and pv < 1000:
                stats.meshes_1000plus += 1
                changed = True
            stats._prev_verts[name] = cv

        # --- Edges ---
        pe = stats._prev_edges.get(name)
        if pe is None:
            stats._prev_edges[name] = ce
        else:
            d = ce - pe
            if d > 0:
                stats.edges_created += d
                changed = True
            stats._prev_edges[name] = ce

        # --- Faces ---
        pf = stats._prev_faces.get(name)
        if pf is None:
            stats._prev_faces[name] = cf
        else:
            d = cf - pf
            if d > 0:
                stats.faces_created += d
                changed = True
            stats._prev_faces[name] = cf

        # --- Materials ---
        if name not in stats._prev_mats:
            if obj.data.materials and len(obj.data.materials) > 0:
                mat = obj.data.materials[0]
                if mat is not None and mat.use_nodes:
                    stats.materials_applied += 1
                    stats._prev_mats.add(name)
                    changed = True

    if changed:
        # Record user activity for active-time tracking
        _on_user_activity()
        # Check stat-based achievements immediately (no 60s delay!)
        check_achievements()
        check_complex_achievements(scene)


# =============================================
#  HANDLERS & TIMERS
# =============================================
@persistent
def on_load_post(dummy=None):
    """Re-load data when a new .blend file is opened."""
    load_data()
    now = time.time()
    ach_events.reset_session_tracking(stats, now=now)
    ach_events.reset_scene_snapshots(stats)


@persistent
def on_save_pre(dummy=None):
    """Save data before Blender saves the .blend file."""
    _on_user_activity()  # saving is active work
    save_data()


@persistent
def on_render_complete(dummy=None):
    """Handle render completion — increment counter and check first_render achievement."""
    stats.renders_completed += 1
    _on_user_activity()  # render is active work

    if "first_render" not in stats.unlocked:
        scene = bpy.context.scene
        has_mesh_with_mat = False
        has_light = False
        for obj in scene.objects:
            if obj.type == 'MESH' and obj.data.materials and obj.data.materials[0]:
                has_mesh_with_mat = True
            if obj.type == 'LIGHT':
                has_light = True
        if has_mesh_with_mat and has_light:
            ach = next((a for a in ACHIEVEMENTS_DEF if a["id"] == "first_render"), None)
            if ach:
                _unlock_achievement("first_render", ach)

    # Also check other complex achievements after render
    check_complex_achievements()
    save_data()


def _timer_tick():
    """Periodic timer (60s): flush time, check achievements, save."""
    _flush_session_time()
    check_achievements()
    try:
        check_complex_achievements()
    except Exception:
        pass
    save_data()
    if _pending_notifications:
        _tag_redraw_all()
    return 60.0


def _notification_redraw_tick():
    """Fast redraw timer for smooth notification animations."""
    if _pending_notifications:
        _tag_redraw_all()
        return 0.05
    # If there's a pinned achievement, redraw less frequently (progress changes slowly)
    if stats.pinned_ach_id:
        _tag_redraw_all()
        return 2.0
    return 1.0


# =============================================
#  ICONS (preview collections)
# =============================================
preview_collections = {}


def _ensure_icons():
    """Lazy-load icon previews from textures directory."""
    if "ach_icons" in preview_collections:
        return preview_collections["ach_icons"]
    import bpy.utils.previews
    pcoll = bpy.utils.previews.new()
    for ach in ACHIEVEMENTS_DEF:
        for key in ("icon_gray", "icon_color"):
            fname = ach[key]
            fpath = os.path.join(ICONS_DIR, fname)
            if os.path.exists(fpath):
                try:
                    pcoll.load(fname, fpath, 'IMAGE')
                except Exception:
                    pass
    preview_collections["ach_icons"] = pcoll
    return pcoll


def _get_icon_id(ach, unlocked):
    """Get icon preview ID for an achievement card."""
    pcoll = _ensure_icons()
    key = ach["icon_color"] if unlocked else ach["icon_gray"]
    return pcoll[key].icon_id if key in pcoll else 0


# =============================================
#  OPERATORS
# =============================================
class ACH_OT_OpenWindow(bpy.types.Operator):
    bl_idname = "ach.open_window"
    bl_label = "Achievements"
    bl_description = "Open achievements panel"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        bpy.ops.ach.achievements_dialog('INVOKE_DEFAULT')
        return {'FINISHED'}


class ACH_OT_OpenTutorial(bpy.types.Operator):
    bl_idname = "ach.open_tutorial"
    bl_label = "Open Tutorial"
    bl_options = {'INTERNAL'}
    url: bpy.props.StringProperty(default="")

    def execute(self, context):
        if self.url:
            bpy.ops.wm.url_open(url=self.url)
        return {'FINISHED'}


class ACH_OT_ApplyReward(bpy.types.Operator):
    bl_idname = "ach.apply_reward"
    bl_label = "Apply Reward"
    bl_options = {'INTERNAL', 'UNDO'}
    ach_id: bpy.props.StringProperty(default="")

    def execute(self, context):
        manager = ach_rewards.RewardManager(
            _REWARD_MANIFEST,
            data_dir=DATA_DIR,
            asset_cache=_REWARD_ASSET_CACHE,
        )
        result = manager.resolve(
            self.ach_id,
            stats,
            ach_rewards.RewardVerifier(_verify_unlock),
        )
        if result.status == "cancelled" and result.report:
            level, message = result.report
            self.report({level}, message)
            return {'CANCELLED'}

        action = result.action
        if action.kind == "open_tutorial":
            if action.url:
                bpy.ops.wm.url_open(url=action.url)
            return {'FINISHED'}
        if action.kind == "none":
            if result.report:
                level, message = result.report
                self.report({level}, message)
            return {'FINISHED'}

        obj = context.active_object
        if action.kind == "link_asset" and action.asset_path is not None:
            self._link(context, action.reward_type, str(action.asset_path), action.name, obj)
        elif action.kind == "placeholder_material":
            self._ph_mat(action.name, obj)
        elif action.kind == "placeholder_mesh":
            self._ph_mesh(context, action.name)
        elif action.kind == "placeholder_geo_nodes":
            self._ph_geo(action.name, obj)

        if result.mark_claimed:
            stats.rewards_claimed.add(self.ach_id)
            save_data()
        if result.report:
            level, message = result.report
            self.report({level}, message)
        return {'FINISHED'}

    def _link(self, ctx, rtype, bp, name, obj):
        """Load reward asset from .blend file."""
        if rtype == "material":
            with bpy.data.libraries.load(bp, link=False) as (df, dt):
                if name in df.materials:
                    dt.materials = [name]
            if dt.materials and dt.materials[0] and obj and obj.type == 'MESH':
                # Overwrite all material slots (clear + append)
                obj.data.materials.clear()
                obj.data.materials.append(dt.materials[0])
        elif rtype == "mesh":
            with bpy.data.libraries.load(bp, link=False) as (df, dt):
                if name in df.objects:
                    dt.objects = [name]
            for o in dt.objects:
                if o:
                    ctx.collection.objects.link(o)
        elif rtype == "geo_nodes":
            with bpy.data.libraries.load(bp, link=False) as (df, dt):
                if name in df.node_groups:
                    dt.node_groups = [name]
            if obj and dt.node_groups and dt.node_groups[0]:
                mod = obj.modifiers.new(name=name, type='NODES')
                mod.node_group = dt.node_groups[0]

    def _ph_mat(self, name, obj):
        """Create placeholder material when .blend file is missing."""
        h = int(hashlib.md5(name.encode()).hexdigest()[:6], 16)
        r, g, b = ((h >> 16) & 0xFF) / 255, ((h >> 8) & 0xFF) / 255, (h & 0xFF) / 255
        mat = bpy.data.materials.new(name=name)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
            bsdf.inputs["Metallic"].default_value = 0.5
            bsdf.inputs["Roughness"].default_value = 0.3
        if obj and obj.type == 'MESH':
            obj.data.materials.clear()
            obj.data.materials.append(mat)

    def _ph_mesh(self, ctx, name):
        """Create placeholder mesh when .blend file is missing."""
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.5)
        ctx.active_object.name = name

    def _ph_geo(self, name, obj):
        """Create placeholder geo nodes modifier when .blend file is missing."""
        if obj:
            obj.modifiers.new(name=name, type='NODES')


class ACH_OT_PinAchievement(bpy.types.Operator):
    bl_idname = "ach.pin_achievement"
    bl_label = "Pin"
    bl_description = "Pin/unpin achievement to viewport"
    bl_options = {'INTERNAL'}
    ach_id: bpy.props.StringProperty(default="")

    def execute(self, context):
        if stats.pinned_ach_id == self.ach_id:
            stats.pinned_ach_id = ""
            self.report({'INFO'}, "Unpinned")
        else:
            stats.pinned_ach_id = self.ach_id
            ach = next((a for a in ACHIEVEMENTS_DEF if a["id"] == self.ach_id), None)
            if ach:
                self.report({'INFO'}, f"Pinned: {ach['title']}")
        save_data()
        _tag_redraw_all()
        return {'FINISHED'}


class ACH_OT_PagePrev(bpy.types.Operator):
    bl_idname = "ach.page_prev"
    bl_label = "Prev"
    bl_options = {'INTERNAL'}
    tab: bpy.props.StringProperty(default="TASKS")

    def execute(self, context):
        p = _tab_prop(self.tab)
        setattr(context.scene, p, max(0, getattr(context.scene, p, 0) - 1))
        return {'FINISHED'}


class ACH_OT_PageNext(bpy.types.Operator):
    bl_idname = "ach.page_next"
    bl_label = "Next"
    bl_options = {'INTERNAL'}
    tab: bpy.props.StringProperty(default="TASKS")
    max_pages: bpy.props.IntProperty(default=1)

    def execute(self, context):
        p = _tab_prop(self.tab)
        setattr(context.scene, p, min(self.max_pages - 1, getattr(context.scene, p, 0) + 1))
        return {'FINISHED'}


def _tab_prop(tab):
    """Map tab key to Scene property name for pagination.
    Supports category-specific keys like TASKS_EDITING -> ach_page_tasks_editing."""
    return ach_ui.tab_page_property(tab)


# =============================================
#  UNIFIED CARD — horizontal layout, icon LEFT
#  Fixed dimensions via ui_units
# =============================================
# 1 UI unit ~ 20px at default scale
# Icon 100x100 = 5.0 units
# Card width: 312px ~ 15.6 units (100/128 * 400)
# 16px = 0.8 units padding

_UNIT = 20.0  # pixels per ui_unit (approx)
_CARD_W = 15.6   # 312px
_CARD_H = 5.0    # 100px (icon height)
_ICON_U = 5.0    # 100px
_GAP = 0.8       # 16px


def _draw_unified_card(parent, ach=None, lesson=None, unlocked=False,
                       show_progress=False, show_reward_btn=False, show_lesson_btn=False,
                       show_pin=False):
    """Draw a unified achievement/lesson card.
    Horizontal layout: icon 100x100 on LEFT, text on RIGHT.
    Text block is vertically centered relative to icon.
    Fixed size via ui_units_x / ui_units_y."""
    box = parent.box()
    box.ui_units_x = _CARD_W

    # Horizontal split: icon | text
    # factor = icon_width / total_width = 5.0 / 15.6 ~ 0.32
    main_split = box.split(factor=0.32, align=False)

    # === LEFT: icon ===
    icon_col = main_split.column(align=True)
    icon_col.ui_units_x = _ICON_U

    icon_id = 0
    if ach:
        icon_id = _get_icon_id(ach, unlocked)

    icon_box = icon_col.box()
    icon_inner = icon_box.column(align=True)
    icon_inner.ui_units_x = _ICON_U
    icon_inner.ui_units_y = _ICON_U  # square 100x100
    icon_inner.alignment = 'CENTER'

    if icon_id:
        icon_inner.label(text="", icon_value=icon_id)
    else:
        # Gray placeholder square with centered icon
        icon_inner.label(text="")
        center_row = icon_inner.row()
        center_row.alignment = 'CENTER'
        if ach and unlocked:
            center_row.label(text="", icon="CHECKMARK")
        elif ach:
            center_row.label(text="", icon="MESH_CIRCLE")
        else:
            center_row.label(text="", icon="IMAGE_DATA")
        icon_inner.label(text="")

    # === RIGHT: text, vertically centered ===
    text_outer = main_split.column(align=True)
    text_outer.separator(factor=0.4)
    text_col = text_outer.column(align=True)

    # Title row + difficulty badge + pin button
    title = ach["title"] if ach else (lesson["title"] if lesson else "")
    title_row = text_col.row(align=True)
    title_row.scale_y = 1.2
    title_label = title_row.row()
    if ach and not unlocked:
        title_label.enabled = False
    # Add difficulty tag next to title
    if ach:
        diff = ach.get("difficulty", "medium")
        diff_text, diff_icon = _difficulty_label(diff)
        xp_pts = DIFFICULTY_XP.get(diff, 10)
        title_label.label(text=f"{ach_ui.card_title_text(title)}  [{diff_text} +{xp_pts}XP]")
    else:
        title_label.label(text=ach_ui.card_title_text(title))
    # Pin button — always active (separate from disabled row)
    if show_pin and ach:
        is_pinned = (stats.pinned_ach_id == ach["id"])
        pin_icon = "PINNED" if is_pinned else "UNPINNED"
        op = title_row.operator("ach.pin_achievement", text="", icon=pin_icon)
        op.ach_id = ach["id"]

    text_col.separator(factor=_GAP)

    # Description
    desc = ach["description"] if ach else (lesson["description"] if lesson else "")
    desc_row = text_col.row()
    desc_row.scale_y = 0.9
    if ach and not unlocked:
        desc_row.enabled = False
    desc_row.label(text=ach_ui.card_description_text(desc))

    # Progress (only for task cards)
    if show_progress and ach:
        text_col.separator(factor=_GAP)
        if ach.get("check_type") == "complex":
            # Complex: show step-by-step progress
            steps = ach.get("steps", [])
            if steps:
                scene = bpy.context.scene
                for step in steps:
                    step_done = _check_complex_step(ach.get("complex_id", ""), step["check"], scene)
                    step_icon = "CHECKMARK" if step_done else "BLANK1"
                    step_row = text_col.row()
                    step_row.scale_y = 0.7
                    step_row.label(text=f"  {step['label']}", icon=step_icon)
                # Overall percentage
                done_count = sum(1 for s in steps if _check_complex_step(ach.get("complex_id", ""), s["check"], scene))
                pct = int(done_count / len(steps) * 100)
                pct_row = text_col.row()
                pct_row.scale_y = 0.8
                pct_row.label(text=f"  {done_count}/{len(steps)}  ({pct}%)")
        else:
            # Stat-based: show bar
            value = getattr(stats, ach["stat_key"], 0)
            goal = ach["goal"]
            progress = min(value / goal, 1.0) if goal > 0 else 0
            bar_len = 10
            filled = int(progress * bar_len)
            bar = "\u2588" * filled + "\u2591" * (bar_len - filled)
            pct = int(progress * 100)

            prog_row = text_col.row()
            prog_row.scale_y = 0.8
            prog_row.label(text=f"{bar}  {value}/{goal}  ({pct}%)")

    # Reward label
    if ach:
        reward_label = _reward_type_label(ach.get("reward_type", "none"))
        if reward_label:
            text_col.separator(factor=_GAP)
            rew_row = text_col.row()
            rew_row.scale_y = 1.2
            if not unlocked:
                rew_row.enabled = False
            rew_row.label(text=reward_label)

    # Linked achievements (for lesson cards)
    if lesson:
        linked = [a for a in ACHIEVEMENTS_DEF if a.get("lesson_id") == lesson["id"]]
        done_c = sum(1 for a in linked if a["id"] in stats.unlocked)
        if linked:
            text_col.separator(factor=_GAP)
            link_row = text_col.row()
            link_row.scale_y = 0.8
            link_row.label(text=f"Ачивок: {done_c}/{len(linked)}")

    # Action buttons
    if show_reward_btn and ach and unlocked:
        text_col.separator(factor=_GAP)
        rtype = ach.get("reward_type", "none")
        if rtype == "tutorial":
            url = ach.get("reward_data", {}).get("url", "")
            if url:
                op = text_col.operator("ach.open_tutorial", text="Урок", icon="URL")
                op.url = url
        elif rtype in ("material", "mesh", "geo_nodes"):
            op = text_col.operator("ach.apply_reward", text="Получить", icon="IMPORT")
            op.ach_id = ach["id"]

    if show_lesson_btn and lesson:
        text_col.separator(factor=_GAP)
        url = lesson.get("url", "")
        if url:
            op = text_col.operator("ach.open_tutorial", text="Открыть урок", icon="URL")
            op.url = url


# =============================================
#  GRID + PAGINATION
# =============================================
def _draw_grid_page(layout, items, scn, tab_key, draw_func):
    """Draw a paginated grid of cards."""
    page_prop = _tab_prop(tab_key)
    page_plan = ach_ui.grid_page_plan(len(items), getattr(scn, page_prop, 0))
    total_pages = page_plan.total_pages
    page = page_plan.page
    page_items = items[page_plan.start:page_plan.end]

    for row_start in range(0, len(page_items), GRID_COLS):
        row_items = page_items[row_start:row_start + GRID_COLS]
        grid_row = layout.row(align=False)
        for item in row_items:
            card_col = grid_row.column()
            draw_func(card_col, item)
        # Fill empty cells
        for _ in range(GRID_COLS - len(row_items)):
            empty = grid_row.column()
            empty_box = empty.box()
            empty_box.ui_units_x = _CARD_W
            empty_box.label(text="")

    if total_pages > 1:
        layout.separator(factor=0.5)
        pag = layout.row(align=True)
        pag.alignment = 'CENTER'
        prev_op = pag.operator("ach.page_prev", text="", icon="TRIA_LEFT")
        prev_op.tab = tab_key
        pag.label(text=f"  {page + 1} / {total_pages}  ")
        next_op = pag.operator("ach.page_next", text="", icon="TRIA_RIGHT")
        next_op.tab = tab_key
        next_op.max_pages = total_pages


# =============================================
#  RESET PROGRESS (testing/dev)
# =============================================
class ACH_OT_ResetAchievements(bpy.types.Operator):
    """Полный сброс прогресса достижений (для тестирования)."""
    bl_idname = "ach.reset_achievements"
    bl_label = "Сбросить прогресс"
    bl_description = "Полный сброс: достижения, награды, статистика, XP, стрики"
    bl_options = {'INTERNAL'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=360)

    def draw(self, context):
        col = self.layout.column()
        col.label(text="Сбросить весь прогресс?", icon='ERROR')
        col.label(text="Обнулятся достижения, награды, статистика и XP.")
        col.label(text="Действие необратимо.")

    def execute(self, context):
        ach_events.reset_progress(stats, now=time.time())
        _pending_notifications.clear()
        save_data()
        _tag_redraw_all()
        self.report({'INFO'}, "Прогресс достижений сброшен")
        return {'FINISHED'}


# =============================================
#  MAIN DIALOG
# =============================================
class ACH_OT_AchievementsDialog(bpy.types.Operator):
    bl_idname = "ach.achievements_dialog"
    bl_label = "Achievements"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        _flush_session_time()
        wm = context.window_manager
        dialog_w = ach_ui.popup_dialog_width()
        return wm.invoke_popup(self, width=dialog_w)

    def draw(self, context):
        layout = self.layout
        scn = context.scene
        _flush_session_time()

        # Stats summary
        sbox = layout.box()
        sr = sbox.row(align=True)
        unlocked_c = len(stats.unlocked)
        total_c = len(ACHIEVEMENTS_DEF)
        hrs = stats.time_spent // 3600
        mins = (stats.time_spent % 3600) // 60
        sr.label(text=f"Достижений: {unlocked_c}/{total_c}", icon="FUND")
        sr.label(text=f"Время: {hrs}ч {mins}м")
        sr.label(text=f"Верш: {stats.vertices_created}")

        # XP & Level bar
        xp = _calc_xp()
        lvl, lvl_progress, lvl_range, lvl_current = _calc_level(xp)
        xp_box = sbox.row(align=True)
        rank = LEVEL_TITLES.get(lvl, "")
        xp_box.label(text=f"Ур. {lvl} — {rank}", icon="SOLO_ON")
        xp_box.label(text=f"XP: {xp}")
        if lvl < 10:
            bar_len = 12
            filled = int(lvl_progress * bar_len)
            bar_str = "\u2588" * filled + "\u2591" * (bar_len - filled)
            xp_box.label(text=f"{bar_str} {lvl_current}/{lvl_range}")
        else:
            xp_box.label(text="MAX")

        # Reset progress (testing/dev) — confirmation handled by the operator
        reset_row = sbox.row(align=True)
        reset_row.operator("ach.reset_achievements", text="Сбросить прогресс", icon="TRASH")

        # Tab buttons
        row = layout.row(align=True)
        for tab_spec in ach_ui.TABS:
            row.prop_enum(scn, "ach_tab", tab_spec.key, text=tab_spec.label)
        layout.separator(factor=0.3)

        tab = scn.ach_tab
        if tab == "TASKS":
            self._tab_tasks(layout, scn)
        elif tab == "DONE":
            self._tab_done(layout, scn)
        elif tab == "LESSONS":
            self._tab_lessons(layout, scn)
        elif tab == "STORAGE":
            self._tab_storage(layout, scn)

    def _tab_tasks(self, layout, scn):
        items = ach_ui.task_items(ACHIEVEMENTS_DEF, stats.unlocked)
        if not items:
            layout.label(text="Все достижения получены!", icon="CHECKMARK")
            return

        def draw_card(parent, ach):
            _draw_unified_card(parent, ach=ach, unlocked=False, show_progress=True, show_pin=True)

        for cat_id, cat_name in ACH_CATEGORIES:
            cat_items = ach_ui.items_for_category(items, cat_id, key="category")
            if not cat_items:
                continue
            box = layout.box()
            row = box.row()
            row.prop(scn, f"ach_acc_tasks_{cat_id}",
                     icon="TRIA_DOWN" if getattr(scn, f"ach_acc_tasks_{cat_id}", False) else "TRIA_RIGHT",
                     text=f"{cat_name} ({len(cat_items)})", emboss=False)
            if getattr(scn, f"ach_acc_tasks_{cat_id}", False):
                col = box.column()
                _draw_grid_page(col, cat_items, scn, f"TASKS_{cat_id}", draw_card)

    def _tab_done(self, layout, scn):
        items = ach_ui.done_items(ACHIEVEMENTS_DEF, stats.unlocked)
        if not items:
            layout.label(text="Пока нет выполненных", icon="INFO")
            return

        def draw_card(parent, ach):
            _draw_unified_card(parent, ach=ach, unlocked=True, show_reward_btn=True)

        for cat_id, cat_name in ACH_CATEGORIES:
            cat_items = ach_ui.items_for_category(items, cat_id, key="category")
            if not cat_items:
                continue
            box = layout.box()
            row = box.row()
            row.prop(scn, f"ach_acc_done_{cat_id}",
                     icon="TRIA_DOWN" if getattr(scn, f"ach_acc_done_{cat_id}", False) else "TRIA_RIGHT",
                     text=f"{cat_name} ({len(cat_items)})", emboss=False)
            if getattr(scn, f"ach_acc_done_{cat_id}", False):
                col = box.column()
                _draw_grid_page(col, cat_items, scn, f"DONE_{cat_id}", draw_card)

    def _tab_lessons(self, layout, scn):
        if not LESSONS_DEF:
            layout.label(text="Нет уроков", icon="INFO")
            return

        def draw_card(parent, lesson):
            _draw_unified_card(parent, lesson=lesson, unlocked=True, show_lesson_btn=True)

        for cat_id, cat_name in LESSON_CATEGORIES:
            cat_items = ach_ui.items_for_category(LESSONS_DEF, cat_id, key="category")
            if not cat_items:
                continue
            box = layout.box()
            row = box.row()
            row.prop(scn, f"ach_acc_lessons_{cat_id}",
                     icon="TRIA_DOWN" if getattr(scn, f"ach_acc_lessons_{cat_id}", False) else "TRIA_RIGHT",
                     text=f"{cat_name} ({len(cat_items)})", emboss=False)
            if getattr(scn, f"ach_acc_lessons_{cat_id}", False):
                col = box.column()
                _draw_grid_page(col, cat_items, scn, f"LESSONS_{cat_id}", draw_card)

    def _tab_storage(self, layout, scn):
        items = ach_ui.storage_items(ACHIEVEMENTS_DEF, stats.unlocked)
        if not items:
            layout.label(text="Нет полученных наград", icon="INFO")
            return

        def draw_card(parent, ach):
            _draw_unified_card(parent, ach=ach, unlocked=True, show_reward_btn=True)

        for cat_id, cat_name in REWARD_CATEGORIES:
            cat_items = ach_ui.items_for_category(items, cat_id, key="reward_category")
            if not cat_items:
                continue
            box = layout.box()
            row = box.row()
            row.prop(scn, f"ach_acc_storage_{cat_id}",
                     icon="TRIA_DOWN" if getattr(scn, f"ach_acc_storage_{cat_id}", False) else "TRIA_RIGHT",
                     text=f"{cat_name} ({len(cat_items)})", emboss=False)
            if getattr(scn, f"ach_acc_storage_{cat_id}", False):
                col = box.column()
                _draw_grid_page(col, cat_items, scn, f"STORAGE_{cat_id}", draw_card)


# =============================================
#  HEADER BUTTON
# =============================================
def _draw_header_button(self, context):
    """Draw the Achievements button in the 3D Viewport header."""
    if context.area.type != 'VIEW_3D':
        return
    row = self.layout.row(align=True)
    row.separator(factor=2.0)
    uc = len(stats.unlocked)
    tc = len(ACHIEVEMENTS_DEF)
    row.operator("ach.open_window", text=f"Achievements ({uc}/{tc})", icon="FUND")


# =============================================
#  REGISTRATION
# =============================================
_classes = (
    ACH_OT_OpenWindow,
    ACH_OT_OpenTutorial,
    ACH_OT_ApplyReward,
    ACH_OT_PinAchievement,
    ACH_OT_PagePrev,
    ACH_OT_PageNext,
    ACH_OT_ResetAchievements,
    ACH_OT_AchievementsDialog,
)


def _base_scene_properties():
    props = {}
    for spec in ach_ui.base_scene_property_specs():
        if spec.kind == "enum":
            props[spec.name] = bpy.props.EnumProperty(items=spec.items, default=spec.default)
        elif spec.kind == "int":
            props[spec.name] = bpy.props.IntProperty(default=spec.default, min=spec.min_value or 0)
        elif spec.kind == "bool":
            props[spec.name] = bpy.props.BoolProperty(default=spec.default)
    return props


def _category_scene_properties():
    props = {}
    for spec in ach_ui.category_scene_property_specs(ACH_CATEGORIES, REWARD_CATEGORIES):
        if spec.kind == "int":
            props[spec.name] = bpy.props.IntProperty(default=spec.default, min=spec.min_value or 0)
        elif spec.kind == "bool":
            props[spec.name] = bpy.props.BoolProperty(default=spec.default)
    return props


def _scene_property_names():
    return ach_ui.scene_property_names(ACH_CATEGORIES, REWARD_CATEGORIES)


def _register_scene_properties():
    for name, prop in {**_base_scene_properties(), **_category_scene_properties()}.items():
        ach_lifecycle.set_scene_property_once(bpy, name, prop)


def _unregister_scene_properties():
    for name in _scene_property_names():
        ach_lifecycle.delete_scene_property_if_present(bpy, name)


def _handler_pairs():
    return (
        (bpy.app.handlers.depsgraph_update_post, on_depsgraph_update),
        (bpy.app.handlers.load_post, on_load_post),
        (bpy.app.handlers.save_pre, on_save_pre),
        (bpy.app.handlers.render_complete, on_render_complete),
    )


def _register_handlers():
    for collection, callback in _handler_pairs():
        ach_lifecycle.append_handler_once(collection, callback)


def _unregister_handlers():
    for collection, callback in _handler_pairs():
        ach_lifecycle.remove_handler_all(collection, callback)


def _register_timers():
    ach_lifecycle.register_timer_once(
        bpy, _timer_tick, first_interval=60.0, persistent=True)
    ach_lifecycle.register_timer_once(
        bpy, _notification_redraw_tick, first_interval=1.0, persistent=True)


def _unregister_timers():
    ach_lifecycle.unregister_timer_if_registered(bpy, _timer_tick)
    ach_lifecycle.unregister_timer_if_registered(bpy, _notification_redraw_tick)


def _register_draw_handlers():
    global _draw_handler, _draw_handler_pin, _header_button_registered
    if not _header_button_registered:
        ach_lifecycle.append_header_once(bpy.types.VIEW3D_HT_header, _draw_header_button)
        _header_button_registered = True
    _draw_handler = ach_lifecycle.add_draw_handler_once(
        bpy, _draw_handler, _draw_notifications)
    _draw_handler_pin = ach_lifecycle.add_draw_handler_once(
        bpy, _draw_handler_pin, _draw_pinned_achievement)


def _unregister_draw_handlers():
    global _draw_handler, _draw_handler_pin, _header_button_registered
    ach_lifecycle.remove_draw_handler_if_present(bpy, _draw_handler)
    _draw_handler = None
    ach_lifecycle.remove_draw_handler_if_present(bpy, _draw_handler_pin)
    _draw_handler_pin = None
    ach_lifecycle.remove_header_all(bpy.types.VIEW3D_HT_header, _draw_header_button)
    _header_button_registered = False


def register():
    global _addon_registered
    ach_lifecycle.register_classes(bpy, _classes)
    _register_scene_properties()

    _ensure_data_dirs()
    load_data()
    now = time.time()
    ach_events.reset_session_tracking(stats, now=now)
    ach_events.reset_speed_model_tracking(stats, now=now)

    _register_handlers()
    _register_timers()
    _register_draw_handlers()
    _addon_registered = True

    print("[Achievements] v0.1 — registered! (100 achievements + XP)")
    print(f"[Achievements] Data: {DATA_FILE}")


def unregister():
    global _addon_registered
    if _addon_registered:
        save_data()
    _unregister_draw_handlers()
    _unregister_timers()
    _unregister_handlers()
    ach_lifecycle.clear_preview_collections(bpy, preview_collections)
    ach_lifecycle.unregister_classes(bpy, _classes)
    _unregister_scene_properties()
    _addon_registered = False
    print("[Achievements] v0.1 — unregistered")


if __name__ == "__main__":
    register()
