# ADR 0006: XP Level Reachability

Status: accepted by the owner for the 2026-07-28 balance slice.

Numbering note: ADR 0005 is reserved by the independent active-time branch, so this decision intentionally uses ADR 0006.

## Context

The frozen catalog contains 10 easy, 40 medium, and 55 hard achievements. With awards `5/10/20`, all `105/105` achievements produce exactly `1550 XP`. The previous exponential widths placed level 8 at `2540` and level 10 at `10220`, so a complete profile remained level 7. XP and level are derived from unlocked catalog IDs rather than persisted fields; there is no historical XP ledger to migrate.

## Decision

- Keep difficulty awards `easy = 5`, `medium = 10`, and `hard = 20`.
- Use exact level bands `20, 40, 80, 120, 140, 170, 200, 230, 260, 290`.
- Use exact starts `0, 20, 60, 140, 260, 400, 570, 770, 1000, 1260`; the matching ends are `20, 60, 140, 260, 400, 570, 770, 1000, 1260, 1550`.
- Keep level 10 in normal progress from `1260` through `1549`; display `MAX` only at the exact cap `1550`, which requires all `105/105` achievements.
- Keep pure progression constants, calculation, and formatting in `achievements/levels.py`. Preserve root `DIFFICULTY_XP`, `XP_LEVELS`, and `LEVEL_TITLES` as compatibility aliases.
- Keep XP and level derived from the current unlocked catalog IDs. Do not add persistence fields, change `SCHEMA_VERSION = "1.0.0"`, or migrate existing payloads.
- Across every reachable XP total, never lower the legacy level and allow promotion by no more than three levels.
- Preserve catalog IDs/difficulties, rewards, operators, Scene properties, handlers, data paths, extension permissions, and release identity.

## Verification

- Pure unit tests cover all starts/ends, level-10 `0/290` and `289/290`, exact-cap `MAX`, the complete reachable five-point XP state space, full-catalog-only cap, persistence absence, and the `0..+3` delta bound.
- `verify_frozen.py` recomputes catalog maximum XP, freezes awards/bands/starts/ends/titles/root aliases, proves all starts reachable, and requires cap `1550`.
- Blender UI smoke verifies the root compatibility aliases and pre-cap versus exact-cap presentation under a disposable profile.
- Normal frozen/plugin/predicate verifiers, Ruff, pytest, Blender smoke, installed-extension policy, and independent review remain delivery gates.

## Consequences

Existing profiles retain the same unlocked achievements and derived XP but may display a higher level immediately. No reachable profile moves down, and the maximum increase is three levels. Level 10 now has visible progress instead of becoming `MAX` at entry, and complete catalog progress reaches the exact cap without changing persisted data.
