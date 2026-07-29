bl_info = {
    "name": "Achievements",
    "author": "axximus",
    "version": (0, 2, 2),
    "blender": (5, 0, 0),
    "location": "3D Viewport > Header (trophy icon)",
    "description": "Gamification addon: 105 achievements, XP & levels, rewards, tutorials",
    "category": "Interface",
}

import bpy
import os
import time
import hashlib
from contextlib import suppress
import bmesh
import gpu
import blf
from bpy.app.handlers import persistent
from gpu_extras.batch import batch_for_shader

# ============================================================
#  ACHIEVEMENTS ADDON — v0.2.2 (release candidate)
#  Blender 5.0 / 5.1 / 5.2
#
#  v0.2.2:
#  - Blender extension namespace policy compliance
#  - Package-relative runtime imports without sys.path mutation
#  v0.2.1:
#  - 105 achievements across 5 categories
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
def _make_unlock_hash(ach_id):
    """Generate the legacy-compatible local integrity marker."""
    return ach_integrity.make_unlock_hash(ach_id, ach_integrity.current_username())


def _verify_unlock(ach_id, stored_hash):
    """Verify the local marker without repairing persisted state."""
    return ach_integrity.verify_unlock_hash(
        ach_id, stored_hash, ach_integrity.current_username()
    )


# =============================================
#  CATALOG
# =============================================
from .achievements.catalog import (
    ACHIEVEMENTS_DEF,
    ACH_CATEGORIES,
    LESSONS_DEF,
    LESSON_CATEGORIES,
    REWARD_CATEGORIES,
)
from .achievements import engine as ach_engine
from .achievements import events as ach_events
from .achievements import integrity as ach_integrity
from .achievements import lifecycle as ach_lifecycle
from .achievements import levels as ach_levels
from .achievements import metadata as ach_metadata
from .achievements import persistence as ach_persistence
from .achievements import predicates as ach_predicates
from .achievements import rewards as ach_rewards
from .achievements import ui as ach_ui


_REWARD_MANIFEST = ach_rewards.RewardManifest.from_achievements(ACHIEVEMENTS_DEF)
_REWARD_ASSET_CACHE = ach_rewards.AssetCache()
_REWARD_MARKER_ID = "_achievements_reward_id"
_REWARD_MARKER_TYPE = "_achievements_reward_type"
_REWARD_MARKER_NAME = "_achievements_reward_name"

# =============================================
#  XP & LEVEL SYSTEM
# =============================================
# Compatibility aliases keep the root runtime API stable while pure level
# planning and formatting live in the bpy-free support package.
DIFFICULTY_XP = ach_levels.DIFFICULTY_XP
XP_LEVELS = ach_levels.XP_LEVELS
LEVEL_TITLES = ach_levels.LEVEL_TITLES


def _calc_xp():
    """Calculate total XP from unlocked achievements."""
    return ach_levels.calculate_xp(ACHIEVEMENTS_DEF, stats.unlocked)


def _calc_level(xp):
    """Calculate current level and progress within that level."""
    return ach_levels.calculate_level(xp)


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
    _last_activity = 0.0    # monotonic timestamp of last real activity event
    _last_accounted_activity = 0.0  # credited boundary inside the active window
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
# Accepted active tail (seconds) after the latest real activity event.
# Overlapping event windows merge; timer/save_data flushes never extend the tail.
_IDLE_TIMEOUT = 120  # 2 minutes
_activity_clock = time.monotonic


def _on_user_activity():
    """Record a qualifying depsgraph, save_pre, or render_complete event."""
    ach_events.record_user_activity(stats, now=_activity_clock(), idle_timeout=_IDLE_TIMEOUT)


def _flush_session_time():
    """Credit an existing window from progress persistence, UI, or timer paths."""
    ach_events.flush_session_time(stats, now=_activity_clock(), idle_timeout=_IDLE_TIMEOUT)


def _ensure_data_dirs():
    ach_persistence.ensure_data_dirs(DATA_DIR)


def save_data(*, reward_claim=None):
    """Persist stats, committing an optional reward claim only after a successful write."""
    try:
        _flush_session_time()
        _ensure_data_dirs()
        payload = ach_persistence.payload_from_stats(stats, reward_claim=reward_claim)
        ach_persistence.atomic_write_json(DATA_FILE, payload)
    except Exception as e:
        print(f"[Achievements] Save error: {e}")
        return False
    if reward_claim is not None:
        stats.rewards_claimed.add(str(reward_claim))
    return True


def load_data():
    """Load stats and progress from JSON file."""
    # Loading and migration-triggered saves must not inherit an activity window
    # from the previous file/session.
    ach_events.reset_session_tracking(stats, now=_activity_clock())
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

        ach_events.reset_session_tracking(stats, now=_activity_clock())

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

def _check_complex_step(complex_id, step_check, scene, event=None):
    """Evaluate one complex step through the pure predicate registry."""
    import datetime

    try:
        context = ach_predicates.PredicateContext(
            scene=scene,
            data=bpy.data,
            view_layer=getattr(bpy.context, "view_layer", None),
            stats=ach_predicates.StatsSnapshot.from_runtime(stats),
            clock=ach_predicates.ClockSnapshot(
                now=datetime.datetime.now(),
                timestamp=time.time(),
            ),
            event=event,
        )
        result = ach_predicates.evaluate_predicate(complex_id, step_check, context)
        if result.error:
            print(
                f"[Achievements] complex step check error "
                f"({complex_id}/{step_check}): {result.error}"
            )
        if result.speed_model_reset is not None:
            stats._speed_model_start = result.speed_model_reset.started_at
            stats._speed_model_verts = result.speed_model_reset.vertices_created
        return result.matched
    except Exception as error:
        print(f"[Achievements] complex step check error ({complex_id}/{step_check}): {error}")
        return False


def _check_complex(complex_id, scene, event=None):
    """Check if ALL steps of a complex achievement are complete."""
    ach = next((a for a in ACHIEVEMENTS_DEF if a.get("complex_id") == complex_id), None)
    if not ach:
        return False
    result = ach_engine.evaluate_complex_achievement(
        ach,
        lambda cid, step_check: _check_complex_step(
            cid,
            step_check,
            scene,
            event=event,
        ),
    )
    return result.achieved


def check_complex_achievements(scene=None, event=None):
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
        if _check_complex(ach["complex_id"], scene, event=event):
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
        if name not in stats._prev_mats and obj.data.materials and len(obj.data.materials) > 0:
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

    scene = dummy if hasattr(dummy, "render") else bpy.context.scene

    if "first_render" not in stats.unlocked:
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
    check_complex_achievements(scene, event="render_complete")
    save_data()


def _timer_tick():
    """Periodic timer (60s): flush time, check achievements, save."""
    _flush_session_time()
    check_achievements()
    with suppress(Exception):
        check_complex_achievements()
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
                with suppress(Exception):
                    pcoll.load(fname, fpath, 'IMAGE')
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
        already_claimed = self.ach_id in stats.rewards_claimed
        recover_existing = result.claim_after_apply and not already_claimed
        try:
            applied = self._apply_action(context, action, obj, recover_existing)
        except Exception as error:
            self.report({'ERROR'}, f"Reward application failed: {error}")
            return {'CANCELLED'}
        if not applied:
            self.report({'WARNING'}, "Reward could not be applied")
            return {'CANCELLED'}

        if (
            result.claim_after_apply
            and not already_claimed
            and not save_data(reward_claim=self.ach_id)
        ):
            self.report(
                {'WARNING'},
                "Reward applied, but the claim was not saved. Retry to finish.",
            )
            return {'FINISHED'}
        if result.report:
            level, message = result.report
            self.report({level}, message)
        return {'FINISHED'}

    def _apply_action(self, context, action, obj, recover_existing):
        if action.kind == "link_asset" and action.asset_path is not None:
            return self._link(
                context,
                action.reward_type,
                str(action.asset_path),
                action.name,
                obj,
                recover_existing,
            )
        if action.kind == "placeholder_material":
            return self._ph_mat(action.name, obj, recover_existing)
        if action.kind == "placeholder_mesh":
            return self._ph_mesh(context, action.name, recover_existing)
        if action.kind == "placeholder_geo_nodes":
            return self._ph_geo(action.name, obj, recover_existing)
        return False

    def _marker_matches(self, datablock, reward_type, name):
        if datablock is None:
            return False
        try:
            return (
                datablock.get(_REWARD_MARKER_ID) == self.ach_id
                and datablock.get(_REWARD_MARKER_TYPE) == reward_type
                and datablock.get(_REWARD_MARKER_NAME) == name
            )
        except (AttributeError, TypeError):
            return False

    def _mark_reward(self, datablock, reward_type, name):
        datablock[_REWARD_MARKER_ID] = self.ach_id
        datablock[_REWARD_MARKER_TYPE] = reward_type
        datablock[_REWARD_MARKER_NAME] = name

    def _data_id_snapshot(self):
        return {datablock.as_pointer() for datablock in bpy.data.user_map()}

    def _remove_new_data_ids(self, before):
        loaded = [
            datablock
            for datablock in bpy.data.user_map()
            if datablock.as_pointer() not in before
        ]
        if loaded:
            bpy.data.batch_remove(ids=loaded)

    def _capture_material_state(self, obj):
        mesh = obj.data
        owners = tuple(
            (
                candidate,
                candidate.active_material_index,
                tuple((slot.link, slot.material) for slot in candidate.material_slots),
            )
            for candidate in bpy.data.objects
            if candidate.type == 'MESH' and candidate.data == mesh
        )
        return mesh, tuple(mesh.materials), owners

    def _restore_material_state(self, state):
        mesh, materials, owners = state
        mesh.materials.clear()
        for material in materials:
            mesh.materials.append(material)
        for owner, active_material_index, slots in owners:
            if owner.data != mesh:
                continue
            for index, (link, material) in enumerate(slots):
                if index >= len(owner.material_slots):
                    break
                slot = owner.material_slots[index]
                slot.link = link
                if link == 'OBJECT':
                    slot.material = material
            owner.active_material_index = active_material_index

    def _apply_material_transaction(self, material, obj, before_load=None):
        if material is None or obj is None or obj.type != 'MESH':
            return False
        previous_state = self._capture_material_state(obj)
        try:
            applied = self._apply_material(material, obj)
        except Exception:
            try:
                self._restore_material_state(previous_state)
            finally:
                if before_load is not None:
                    self._remove_new_data_ids(before_load)
            raise
        if not applied:
            try:
                self._restore_material_state(previous_state)
            finally:
                if before_load is not None:
                    self._remove_new_data_ids(before_load)
        return applied

    def _find_marked_material(self, name):
        return next(
            (
                material
                for material in bpy.data.materials
                if self._marker_matches(material, "material", name)
            ),
            None,
        )

    def _find_material_witness(self, name):
        for candidate in bpy.data.objects:
            if candidate.type != 'MESH' or not candidate.users_collection:
                continue
            for material in candidate.data.materials:
                if self._marker_matches(material, "material", name):
                    return material
        return None

    def _apply_material(self, material, obj):
        if material is None or obj is None or obj.type != 'MESH':
            return False
        obj.data.materials.clear()
        obj.data.materials.append(material)
        return any(slot == material for slot in obj.data.materials)

    def _find_marked_object(self, name):
        return next(
            (
                candidate
                for candidate in bpy.data.objects
                if candidate.type == 'MESH'
                and self._marker_matches(candidate, "mesh", name)
            ),
            None,
        )

    def _ensure_object_linked(self, ctx, obj):
        if obj is None:
            return False
        if not obj.users_collection:
            collection = getattr(ctx, "collection", None) or ctx.scene.collection
            collection.objects.link(obj)
        return bool(obj.users_collection)

    def _find_marked_modifier(self, name):
        for candidate in bpy.data.objects:
            if not candidate.users_collection:
                continue
            for modifier in candidate.modifiers:
                if modifier.type != 'NODES':
                    continue
                node_group = getattr(modifier, "node_group", None)
                if self._is_geometry_node_group(node_group) and self._marker_matches(
                    node_group, "geo_nodes", name
                ):
                    return modifier
        return None

    def _is_geometry_node_group(self, node_group):
        return getattr(node_group, "bl_idname", "") == "GeometryNodeTree"

    def _find_marked_node_group(self, name):
        return next(
            (
                group
                for group in bpy.data.node_groups
                if self._is_geometry_node_group(group)
                and self._marker_matches(group, "geo_nodes", name)
            ),
            None,
        )

    def _link(self, ctx, rtype, bp, name, obj, recover_existing):
        """Load reward asset from .blend file."""
        if rtype == "material":
            if recover_existing and self._find_material_witness(name) is not None:
                return True
            if obj is None or obj.type != 'MESH':
                return False
            material = self._find_marked_material(name) if recover_existing else None
            if material is not None:
                return self._apply_material_transaction(material, obj)
            before_load = self._data_id_snapshot()
            try:
                with bpy.data.libraries.load(bp, link=False) as (df, dt):
                    if name in df.materials:
                        dt.materials = [name]
            except Exception:
                self._remove_new_data_ids(before_load)
                raise
            material = next((item for item in dt.materials if item is not None), None)
            if material is None:
                self._remove_new_data_ids(before_load)
                return False
            try:
                self._mark_reward(material, "material", name)
            except Exception:
                self._remove_new_data_ids(before_load)
                raise
            return self._apply_material_transaction(material, obj, before_load)
        elif rtype == "mesh":
            if recover_existing:
                existing = self._find_marked_object(name)
                if existing is not None:
                    return self._ensure_object_linked(ctx, existing)
            before_load = self._data_id_snapshot()
            try:
                with bpy.data.libraries.load(bp, link=False) as (df, dt):
                    if name in df.objects:
                        dt.objects = [name]
            except Exception:
                self._remove_new_data_ids(before_load)
                raise
            linked_object = next((item for item in dt.objects if item is not None), None)
            if linked_object is None:
                self._remove_new_data_ids(before_load)
                return False
            if linked_object.type != 'MESH':
                self._remove_new_data_ids(before_load)
                return False
            try:
                self._mark_reward(linked_object, "mesh", name)
                applied = self._ensure_object_linked(ctx, linked_object)
            except Exception:
                self._remove_new_data_ids(before_load)
                raise
            if not applied:
                self._remove_new_data_ids(before_load)
            return applied
        elif rtype == "geo_nodes":
            modifier = None
            if recover_existing:
                modifier = self._find_marked_modifier(name)
                if modifier is not None:
                    return True
            target = obj
            if target is None:
                return False
            node_group = self._find_marked_node_group(name) if recover_existing else None
            before_load = None
            if node_group is None:
                before_load = self._data_id_snapshot()
                try:
                    with bpy.data.libraries.load(bp, link=False) as (df, dt):
                        if name in df.node_groups:
                            dt.node_groups = [name]
                except Exception:
                    self._remove_new_data_ids(before_load)
                    raise
                node_group = next((item for item in dt.node_groups if item is not None), None)
                if not self._is_geometry_node_group(node_group):
                    self._remove_new_data_ids(before_load)
                    return False
                try:
                    self._mark_reward(node_group, "geo_nodes", name)
                except Exception:
                    self._remove_new_data_ids(before_load)
                    raise
            created_modifier = False
            try:
                if modifier is None:
                    modifier = target.modifiers.new(name=name, type='NODES')
                    created_modifier = modifier is not None
                if modifier is None:
                    applied = False
                else:
                    modifier.node_group = node_group
                    applied = (
                        modifier.node_group == node_group
                        and self._marker_matches(node_group, "geo_nodes", name)
                    )
            except Exception:
                if created_modifier:
                    target.modifiers.remove(modifier)
                if before_load is not None:
                    self._remove_new_data_ids(before_load)
                raise
            if not applied:
                if created_modifier:
                    target.modifiers.remove(modifier)
                if before_load is not None:
                    self._remove_new_data_ids(before_load)
            return applied
        return False

    def _ph_mat(self, name, obj, recover_existing):
        """Create placeholder material when .blend file is missing."""
        if recover_existing and self._find_material_witness(name) is not None:
            return True
        if obj is None or obj.type != 'MESH':
            return False
        material = self._find_marked_material(name) if recover_existing else None
        if material is None:
            before_load = self._data_id_snapshot()
            try:
                h = int(hashlib.md5(name.encode()).hexdigest()[:6], 16)
                r, g, b = (
                    ((h >> 16) & 0xFF) / 255,
                    ((h >> 8) & 0xFF) / 255,
                    (h & 0xFF) / 255,
                )
                material = bpy.data.materials.new(name=name)
                material.use_nodes = True
                bsdf = material.node_tree.nodes.get("Principled BSDF")
                if bsdf:
                    bsdf.inputs["Base Color"].default_value = (r, g, b, 1)
                    bsdf.inputs["Metallic"].default_value = 0.5
                    bsdf.inputs["Roughness"].default_value = 0.3
                self._mark_reward(material, "material", name)
            except Exception:
                self._remove_new_data_ids(before_load)
                raise
            return self._apply_material_transaction(material, obj, before_load)
        return self._apply_material_transaction(material, obj)

    def _ph_mesh(self, ctx, name, recover_existing):
        """Create placeholder mesh when .blend file is missing."""
        if recover_existing:
            existing = self._find_marked_object(name)
            if existing is not None:
                return self._ensure_object_linked(ctx, existing)
        before_load = self._data_id_snapshot()
        try:
            mesh = bpy.data.meshes.new(name=f"{name}_Mesh")
            edit_mesh = bmesh.new()
            try:
                bmesh.ops.create_icosphere(edit_mesh, subdivisions=2, radius=0.5)
                edit_mesh.to_mesh(mesh)
            finally:
                edit_mesh.free()
            created = bpy.data.objects.new(name=name, object_data=mesh)
            self._mark_reward(created, "mesh", name)
            applied = self._ensure_object_linked(ctx, created)
        except Exception:
            self._remove_new_data_ids(before_load)
            raise
        if not applied:
            self._remove_new_data_ids(before_load)
        return applied

    def _ph_geo(self, name, obj, recover_existing):
        """Create placeholder geo nodes modifier when .blend file is missing."""
        if recover_existing:
            existing = self._find_marked_modifier(name)
            if existing is not None:
                return True
        if obj is None:
            return False
        node_group = self._find_marked_node_group(name) if recover_existing else None
        before_load = self._data_id_snapshot()
        if node_group is None:
            try:
                node_group = bpy.data.node_groups.new(
                    name=f"{name}_Reward",
                    type="GeometryNodeTree",
                )
                node_group.interface.new_socket(
                    name="Geometry",
                    in_out='INPUT',
                    socket_type="NodeSocketGeometry",
                )
                node_group.interface.new_socket(
                    name="Geometry",
                    in_out='OUTPUT',
                    socket_type="NodeSocketGeometry",
                )
                group_input = node_group.nodes.new("NodeGroupInput")
                group_output = node_group.nodes.new("NodeGroupOutput")
                node_group.links.new(
                    group_input.outputs["Geometry"],
                    group_output.inputs["Geometry"],
                )
                self._mark_reward(node_group, "geo_nodes", name)
            except Exception:
                self._remove_new_data_ids(before_load)
                raise
        modifier = None
        try:
            modifier = obj.modifiers.new(name=name, type='NODES')
            if modifier is None:
                applied = False
            else:
                modifier.node_group = node_group
                applied = (
                    any(item == modifier for item in obj.modifiers)
                    and modifier.node_group == node_group
                    and self._marker_matches(node_group, "geo_nodes", name)
                )
        except Exception:
            if modifier is not None:
                obj.modifiers.remove(modifier)
            self._remove_new_data_ids(before_load)
            raise
        if not applied:
            if modifier is not None:
                obj.modifiers.remove(modifier)
            self._remove_new_data_ids(before_load)
        return applied


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
        ach_events.reset_progress(
            stats,
            activity_now=_activity_clock(),
            speed_model_now=time.time(),
        )
        _pending_notifications.clear()
        save_data()
        _tag_redraw_all()
        self.report({'INFO'}, "Прогресс достижений сброшен")
        return {'FINISHED'}


def _extension_management_target(context):
    """Resolve this installed extension against Blender's enabled user repos."""
    try:
        repositories = tuple(
            ach_ui.ExtensionRepositorySpec(
                module=repository.module,
                directory=repository.directory,
                source=repository.source,
                enabled=repository.enabled,
            )
            for repository in context.preferences.extensions.repos
        )
        return ach_ui.resolve_extension_management_target(
            __package__,
            __file__,
            repositories,
        )
    except (AttributeError, OSError, RuntimeError, TypeError, ValueError):
        return None


class ACH_OT_OpenExtensionManager(bpy.types.Operator):
    """Open Blender's native extension card for safe removal."""

    bl_idname = "ach.open_extension_manager"
    bl_label = "Удалить аддон…"
    bl_description = (
        "Открыть штатный раздел Extensions; удаление выполняется кнопкой "
        "Uninstall в Blender"
    )
    bl_options = {'INTERNAL'}

    @classmethod
    def poll(cls, context):
        return _extension_management_target(context) is not None

    def execute(self, context):
        if _extension_management_target(context) is None:
            self.report({'ERROR'}, "Аддон не установлен как Blender Extension")
            return {'CANCELLED'}

        preferences = context.preferences
        window_manager = context.window_manager
        if not bpy.ops.screen.userpref_show.poll():
            self.report({'ERROR'}, "Blender Preferences недоступны в текущем контексте")
            return {'CANCELLED'}
        preferences.active_section = 'EXTENSIONS'
        window_manager.extension_type = 'ADDON'
        window_manager.extension_show_panel_installed = True
        window_manager.extension_show_panel_available = False
        if hasattr(window_manager, "extension_use_filter"):
            window_manager.extension_use_filter = False
        if hasattr(window_manager, "extension_tags"):
            window_manager.extension_tags.clear()
        window_manager.extension_search = ach_metadata.ADDON_NAME
        bpy.ops.screen.userpref_show('INVOKE_DEFAULT', section='EXTENSIONS')
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
        xp_box.label(
            text=ach_levels.format_level_progress(lvl_progress, lvl_range, lvl_current)
        )

        # Reset progress (testing/dev) — confirmation handled by the operator
        reset_row = sbox.row(align=True)
        reset_row.operator("ach.reset_achievements", text="Сбросить прогресс", icon="TRASH")

        # Extension removal is completed by Blender after this add-on returns.
        manage_row = sbox.row(align=True)
        manage_row.enabled = _extension_management_target(context) is not None
        manage_row.operator(
            "ach.open_extension_manager",
            text="Удалить аддон…",
            icon="PREFERENCES",
        )
        if manage_row.enabled:
            manage_row.label(text="Завершите Uninstall в Extensions; прогресс сохранится")
        else:
            manage_row.label(text="Доступно после установки ZIP-расширения")

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
    ACH_OT_OpenExtensionManager,
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
    ach_events.reset_speed_model_tracking(stats, now=time.time())

    _register_handlers()
    _register_timers()
    _register_draw_handlers()
    _addon_registered = True

    print("[Achievements] v0.2.2 — registered! (105 achievements + XP)")
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
    print("[Achievements] v0.2.2 — unregistered")


if __name__ == "__main__":
    register()
