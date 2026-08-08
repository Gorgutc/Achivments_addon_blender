---
name: achievements-authoring
description: Add one achievement to the append-only catalog and update the whole frozen chain with it.
---

# Achievements Authoring

Use when a task asks to add, extend, or author an achievement.

## 1. An addition is an owner-level frozen change

- The catalog is append-only. Existing IDs, Russian wording, categories,
  difficulties, rewards, and lesson links are never modified or removed.
- Adding an entry changes the public contract: counts, digest, XP cap, and the
  advertised achievement total. Do not start without an explicit owner decision.
- Record the decision in `docs/agent/frozen-decisions.md` before editing.

## 2. Files that carry the new entry

- `achievements/catalog.py`: append one dict to `ACHIEVEMENTS_DEF`.
  - `id` must match `^[a-z][a-z0-9_]*$` and be unique.
  - Russian `title` and `description` are mandatory; complex step `label` values
    are user-visible and stay Russian too. `goal` is a positive integer.
  - Required fields: `id`, `title`, `description`, `goal`, `stat_key`,
    `category`, `check_type`, `difficulty`, `reward_type`, `reward_data`,
    `reward_category`, `lesson_id`, `icon_gray`, `icon_color`. A `complex` entry
    adds exactly `complex_id` and `steps` and uses `stat_key = "_complex"`.
- `achievements/predicates/`: a complex achievement's step logic goes here as a
  pure, `bpy`-free predicate registered in the registry. The registry bijection
  is exact — one registered step check per catalog step, no extras.
- Root `_check_complex_step` stays the Blender adapter: it resolves runtime state
  and delegates. Never put predicate logic in it.

## 3. The frozen chain that must move together

- `achievements/catalog.py`: `FROZEN_ACHIEVEMENT_COUNT`, `FROZEN_CHECK_TYPES`,
  `FROZEN_CATEGORY_COUNTS`, `FROZEN_DIFFICULTY_COUNTS`,
  `FROZEN_REWARD_TYPE_COUNTS`, `FROZEN_REWARD_CATEGORY_COUNTS`,
  `FROZEN_STAT_KEY_COUNTS`, `FROZEN_COMPLEX_STEP_TOTAL`,
  `FROZEN_COMPLEX_STEP_RANGE`, and `FROZEN_CATALOG_DIGEST` (recompute with
  `catalog_digest()`; never hand-edit the hash).
- `scripts/verify_frozen.py`: the parallel `FROZEN_*` constants and the
  achievement-count and stat/complex-split checks.
- Two hardcoded prose literals are asserted by `scripts/verify_frozen.py` and
  fail the gate if the total moves without them:
  - `__init__.py`: the `bl_info` description must contain the substring
    `105 achievements` — check `bl_info advertises 105 achievements`.
  - `docs/agent/frozen-application-contract.md`: must contain the marker
    `105 total` — check `frozen application contract covers design and
    functions` (frozen path; needs its own owner decision).
- `tests/test_catalog.py`: counts plus the `first_achievement_id` /
  `last_achievement_id` anchors.
- `tests/test_infra_scripts.py`: `CATALOG_DIGEST` and the expected
  `catalog_counts()` payload.
- XP and levels: summed catalog XP must equal the level cap. A new entry moves
  that sum, so `FROZEN_LEVEL_CAP`, the ten bands/starts/ends in
  `achievements/levels.py`, and the reachability checks change with it. That is
  ADR 0006 territory and needs its own owner decision.
- Prose surfaces that state the total: `README.md`,
  `docs/agent/frozen-application-contract.md`, `AGENTS.md`, the
  `__init__.py` registration `print(...)` banner (and its header comment), and
  the sibling skills `achievements-context-keeper/SKILL.md` (`105 achievements
  and 9 lessons`) and `achievements-frozen-decisions/SKILL.md` (`105/105`).
- `docs/archive/achievements_100_list.md` is **byte-frozen** and must NOT be
  touched. `scripts/verify_frozen.py` pins its exact Git blob hash — check
  `archived 100-achievement list preserves baseline Git blob` — so any edit,
  including a re-render or a line-ending change, fails the gate. It is the
  historical 100-entry baseline, not a surface to update.

## 4. Verification

- Full fast gate: `uv run python scripts/verify_frozen.py`,
  `uv run python scripts/verify_codex_plugin.py`,
  `uv run python scripts/verify_predicates.py`, `uv run ruff check .`,
  `uv run pytest`.
- Blender smoke matrix on 5.0.1, 5.1.2, and 5.2.0 — every suite, no target
  skipped or non-blocking.

## 5. Commit gate

- `tools/frozen-guard.mjs` blocks the commit because `achievements/catalog.py`
  is a frozen path. That block is expected, not a bug.
- `OWNER_OVERRIDE=1` is a one-shot escape hatch for that single commit, valid
  only with an explicit owner decision already recorded in
  `docs/agent/frozen-decisions.md`. Never export it for a whole shell session.
