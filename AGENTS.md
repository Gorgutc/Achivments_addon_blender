# Repository Agent Instructions

This repository is the `Achievements` Blender add-on: a Python-only add-on with a
Russian UI, 105 achievements, and 9 lessons. Root `__init__.py` is the shipped
runtime; the `achievements/` package holds the pure, `bpy`-free logic behind it.
Work here is contract-driven: static verifiers freeze the public catalog, the
release identity, and the runtime map, and they run before any delivery claim.

## FROZEN CONTRACTS

Each item below is owner-level. Changing one needs an explicit owner decision
recorded in `docs/agent/frozen-decisions.md`, plus an ADR for structural change.
If a task conflicts with these contracts, notify the user before proceeding.

1. **Public achievement IDs are append-only.** Existing IDs, Russian wording,
   categories, rewards, and lesson links are never modified or removed. The
   catalog digest `FROZEN_CATALOG_DIGEST` and the frozen counters in
   `achievements/catalog.py` and `scripts/verify_frozen.py` enforce this.
2. **The user-facing UI is Russian.** Achievement titles, descriptions, goals,
   tabs (`Задания`, `Выполнено`, `Уроки`, `Хранилище`), and notifications stay in
   Russian. Agent-facing docs, code, and identifiers stay English.
3. **The Blender matrix 5.0.1 / 5.1.2 / 5.2.0 is blocking.** Target runtime policy
   is Blender 5.0+ through Blender's bundled Python. Every smoke target is
   blocking; no target is skipped, canary, or `continue-on-error`.
4. **Modular `achievements/` package structure.** Complex predicates live in pure
   `achievements/predicates/` and are registered in the registry with an exact
   bijection; root `_check_complex_step` stays the thin Blender adapter and holds
   no predicate logic of its own.
5. **Canonical runtime is root `__init__.py`.** `achievements_v01 (4).py` was
   retired in the approved 0.2.0 technical closeout; ADR 0002 preserves its
   baseline blob, hashes, and recovery procedure. Do not reintroduce a second
   runtime without an explicit owner decision.
6. **Release identity 0.2.3 with Stage A-B-C acceptance.** Current
   source-candidate identity is 0.2.3 and `bl_info["blender"] == (5, 0, 0)`.
   Stage A full validation outputs are ephemeral and authorize no retention,
   canonical artifact, or publication. Stage B needs separate explicit owner
   candidate-retention acceptance for one exact audited local candidate SHA,
   still non-canonical and not publication. Stage C needs separate explicit owner
   publication acceptance for `v0.2.3` and GitHub Release from that exact
   retained candidate; this session grants none.
7. **No edits to real user data.** Do not edit or delete real user progress under
   `~/BlenderAchievements` or any generated `achievements_data.json`. Blender
   smoke checks must use temporary `HOME`, `USERPROFILE`, and
   `BLENDER_USER_RESOURCES`.
8. **Shipped runtime stays inside the Blender extension namespace.** Do not add
   the extension directory to `sys.path` and do not use absolute intra-package
   `achievements.*` imports.
9. **Removal and correctness invariants.** Extension removal is routed through
   Blender's native `Extensions` UI; add-on-owned operators must not
   self-uninstall or delete `~/BlenderAchievements`. `subsurface_skin` checks the
   exact active Subsurface Weight, and `denoiser_render` requires a completed
   Cycles-render event.
10. **Unlock hashes are local integrity markers.** Current-schema missing or
    malformed markers must fail closed and must not be backfilled.

## Verification

Fast gate — run all five, in this order:

```bash
uv run python scripts/verify_frozen.py
uv run python scripts/verify_codex_plugin.py
uv run python scripts/verify_predicates.py
uv run ruff check .
uv run pytest
```

Tier mapping, so "fast" is never ambiguous: these five commands are the
canonical **delivery** gate; `.agent-kit.json` `verify.fast` is the narrower
**pre-commit** tier (the four static commands, without `pytest`), and the
session-start primer advertises only the three verifiers.

Harness parity, after editing any plugin skill, `.codex/agents/*.toml`, or
`.codex/hooks.json`:

```bash
node tools/sync-harness.mjs --write   # regenerate the .claude mirror
node tools/sync-harness.mjs --check   # prove parity
```

Deep Blender gate (when Blender is available), one suite per line:

```bash
uv run python scripts/find_blender.py
uv run python scripts/run_blender_smoke.py --suite register
uv run python scripts/run_blender_smoke.py --suite lifecycle_stress
uv run python scripts/run_blender_smoke.py --suite persistence
uv run python scripts/run_blender_smoke.py --suite engine
uv run python scripts/run_blender_smoke.py --suite rewards
uv run python scripts/run_blender_smoke.py --suite ui_visual
```

Packaging: `uv run python scripts/build_extension.py --run-blender` (also wired
as `/package`) runs Stage A validate/build only; without `--run-blender` it is a
dry-run that builds nothing. It never retains a candidate, never tags, and
never publishes; see `docs/agent/packaging-release.md` for the full procedure.

Required delivery gate:

1. Run the relevant static verifier commands.
2. Run fast Python checks where the task touches infra or scripts.
3. Run Blender smoke for ship/deep gates when Blender is available.
4. Spawn or reuse review agents where available.
5. Run `/review` before final delivery; if the slash command is unavailable,
   complete an explicit review fallback covering requirements, diff, checks,
   blockers, and residual risks.

## Repo Map

| Path | What it is |
| --- | --- |
| `__init__.py` | Canonical Blender runtime: operators, handlers, timers, GPU draw UI |
| `achievements/` | Pure package: `catalog`, `engine`, `events`, `levels`, `lifecycle`, `persistence`, `integrity`, `rewards`, `sync`, `ui`, `metadata` |
| `achievements/predicates/` | Pure complex-step predicates plus the registry |
| `blender_manifest.toml` | Blender extension manifest (files-only permission, no network) |
| `scripts/` | Verifiers, Blender discovery, smoke runners, `build_extension.py` |
| `tests/` | Headless pytest suite; `tests/blender/` holds Blender smoke probes |
| `docs/agent/` | Architecture, verification, frozen contracts, ADRs |
| `docs/handoff/current.md` | Operational handoff for the active slice |
| `.codex/` | Codex canon: `config.toml`, `hooks.json`, `hooks/*.py`, `agents/*.toml` |
| `plugins/achievements-blender-codex/skills/` | Codex canon: plugin skills |
| `.claude/skills`, `.claude/agents` | **Generated mirror** of the Codex canon — never edit by hand |
| `tools/*.mjs` | Zero-dependency harness: mirror sync, frozen guard, git gate, hook install |
| `.agent-kit.json` | Verify tiers, frozen paths, and mirror configuration |

## Working Rules

Authority order:

1. System and developer instructions.
2. Task-specific user instructions.
3. This repository `AGENTS.md`.
4. `.codex/config.toml`, `.codex/hooks.json`, and repo-local plugin skills.
5. Historical docs and archived notes.

`CLAUDE.md` is a stub that imports this file; the two harnesses share one canon.

- Scope: this is a Python-only Blender add-on, not a web project. Do not import
  web-stack rules from sibling repositories. Patterns from `Gorgutc/PL_RU` and
  `Gorgutc/codex` are reused only as Codex orchestration patterns.
- Do not modify add-on code in preparation-only tasks unless the user explicitly
  asks for add-on behavior changes.
- Prefer `uv run python ...`, `uv run ruff check .`, and `uv run pytest` for repo
  tooling. The repo is uv/Python-only.
- Use explicit spawned subagents for independent review, audit, and verification
  tasks when the environment exposes them. If no spawn tool is available,
  document the fallback review path instead of treating the absence itself as an
  add-on blocker.
- Hooks may run fast static checks. They must not run heavy Blender smoke checks
  after every edit.
- `.claude/skills` and `.claude/agents` are generated output. Edit the canonical
  skill or agent contract, then run `node tools/sync-harness.mjs --write`.
- `tools/frozen-guard.mjs` blocks a commit that stages a path listed in
  `frozenPaths`. `OWNER_OVERRIDE=1` is a one-shot owner escape hatch and requires
  a recorded decision in `docs/agent/frozen-decisions.md`.

## Memory

Cross-session memory for this project lives in the owner's Second-brain Obsidian
vault, not in this repository. Project home: `1-Projects/Achivments_addon_blender/`.

- `_INDEX.md` — the only place that carries project status (with an as-of date)
  and the "continue here" pointer.
- `Sessions/` — one note per session, written at session end.
- `Decisions/` — durable decisions; frozen notes are law and are not edited
  without an explicit owner decision.
- `Improvements.md` — backlog of harness and repo improvements.
- `Tests.md` — accumulated verification knowledge and matrix results.

Session protocol: read `_INDEX.md` and the project conventions before starting;
at session end write the session note, add its row to `Sessions/_INDEX.md`, and
refresh the status line in `_INDEX.md`.

Machine-absolute paths never appear in this repository or in vault notes; they
live only in the vault's Machines note. Refer to the vault by name, not by path.
