---
name: achievements-quality-gate
description: Run the required checks before claiming work is complete.
---

# Achievements Quality Gate

Use before completion claims.

Release identity: `0.2.3` source candidate. No tag, GitHub Release, or publication is authorized without explicit owner ship acceptance; a local retained candidate is not publication. The historical `achievements-0.2.2.zip` is immutable pre-PR16 evidence and is not a current install or build artifact.

Release stages: (A) a full validation gate produces only ephemeral outputs and authorizes no retention, canonical artifact, or publication; (B) only separate explicit owner candidate-retention acceptance may preserve one exact audited local candidate SHA, which remains non-canonical and not publication; (C) only separate explicit owner publication acceptance may create `v0.2.3` tag and GitHub Release from that exact retained candidate. This session grants none.

Run relevant commands:
- `uv run python scripts/verify_frozen.py`
- `uv run python scripts/verify_codex_plugin.py`
- `uv run python scripts/verify_predicates.py`
- `uv run ruff check .`
- `uv run pytest`
- all six `scripts/run_blender_smoke.py` suites for deep or ship gates, using
  temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Blender `extension validate`, `extension build`, and
  `extension server-generate` through `build_extension.py --run-blender`, plus
  install/enable and register/unregister smoke on 5.0.1, 5.1.2, and 5.2.0 for a
  release candidate. Require `--factory-startup`, a disposable profile with
  temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`, and a fresh
  never-used per-run output directory with a new `<run-id>` for each server
  gate. Per-version self-built ZIPs are build evidence only; use one exact
  audited validation/retained local-candidate SHA for all three
  install/enable/register-unregister smokes. A retained local candidate is not
  publication.
- Verify the 0.2.3 source-candidate identity, package-relative installed namespace imports,
  absence of shipped runtime `sys.path` mutation, manifest
  `files = "Store progress and load local reward assets"`, and absence of
  manifest `network` permission.
- Treat a validation ZIP as build evidence only; historical 0.2.2 is never a
  current install artifact.

Report any skipped command and why.
