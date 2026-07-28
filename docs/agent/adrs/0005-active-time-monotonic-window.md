# ADR 0005: Active-Time Monotonic Window

Status: accepted for the 2026-07-28 active-time correctness slice.

## Context

`time_spent` is persisted as integer seconds of active work and drives six stat achievements plus the session delta used by `weekend_marathon`. The previous flush path credited the gap since `_last_activity` and then moved `_last_activity` forward. Because the 60-second timer calls flush directly and `save_data()` flushes again, periodic persistence could keep refreshing the window without a real user event. Four idle timer cycles reproduced `time_spent = 240`.

The persistence payload has no activity-event history, so historical active seconds cannot be separated reliably from previously credited idle seconds. Runtime active-time clocks must also stay separate from calendar dates and the wall-clock timestamp used by the speed-model predicate.

## Decision

- Keep `_IDLE_TIMEOUT = 120` seconds. A future timeout change requires a separate decision.
- Keep the current real activity sources: qualifying geometry/material changes in `depsgraph_update`, `save_pre`, and `render_complete`. Timer, persistence, register/load, popup/draw, and flush are not activity sources.
- The first real event opens a non-refreshing 120-second activity window and grants no startup or offline time. Later real events extend the union of overlapping windows.
- Track the last real event and the credited boundary with runtime-only monotonic timestamps. Flush credits only the uncounted whole-second part of the current window and never moves the real-event timestamp.
- Repeated or same-time flushes are idempotent. A forward jump credits at most the remaining window. A monotonic rollback closes the current window without decreasing `time_spent`; the next real event opens a fresh window.
- Register, load, and reset clear active-time anchors. Migration-triggered persistence resets them before saving, so stale runtime state cannot change loaded totals.
- Preserve existing `time_spent`, unlocks, integrity markers, and claimed rewards forward-only. Do not relock or rewrite historical progress.
- Keep `SCHEMA_VERSION = "1.0.0"`, all persistence keys, and the data path unchanged. Activity timestamps remain absent from JSON.
- Keep `daily_sessions` behavior unchanged as an open-day/session tracker updated by the existing flush path. It is intentionally independent from active-time accrual; redefining streaks as real-activity days requires a separate owner decision.
- Keep speed-model timing and calendar/date predicates on their existing wall-clock domain. Do not mix them with active-time monotonic timestamps.

## Verification

- Pure tests cover startup idle, the 120-second cap, overlapping and disconnected windows, same-time/double flush, frequent fractional events, suspend/forward jump, rollback, reset, and open-day tracking.
- Blender lifecycle smoke uses an injected monotonic clock to cover timer-to-progress-persistence double flush, reload/offline gaps, rollback, cap behavior, and unregister tail persistence in a disposable profile.
- Blender persistence smoke proves a legacy `time_spent = 42` migration remains exactly 42 with stale runtime anchors and that no activity timestamp enters JSON.
- Frozen/plugin/predicate verifiers, Ruff, full pytest, all Blender smoke suites, and installed-extension policy remain delivery gates.

## Consequences

Idle timers can no longer create active seconds or false time-based unlock progress. A single real event can credit at most the accepted 120-second tail, while overlapping real events form one continuous active interval without losing sub-second remainder. Existing progress remains compatible and non-destructively forward-only. `daily_sessions` retains its previous open-day meaning and is not evidence of active seconds.
