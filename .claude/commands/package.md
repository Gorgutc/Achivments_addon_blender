---
description: Stage A extension packaging - ephemeral validate/build only, no retention, no tag, no publication.
---

# /package

Build and validate the Achievements Blender extension as a **Stage A** run.

## Run

```bash
uv run python scripts/build_extension.py --run-blender
```

`--run-blender` is what actually executes `extension validate` and
`extension build` in an isolated temporary Blender profile. Without it the
script is a **dry run**: it prepares the release source and prints the
would-be commands, then exits 0 with
`Commands were not executed.` — no ZIP is produced and no
`[extension-cli:PASS]` marker is emitted. A bare invocation is useful only to
inspect the staged source and the exact commands.

For a per-version validation run against a real Blender, use a fresh, never-used
per-run output directory and a new `<run-id>` on every rerun:

```bash
uv run python scripts/build_extension.py --revision HEAD \
  --source-dir reports/extension-validation/<run-id>/<version>/source \
  --output-dir reports/extension-validation/<run-id>/<version> \
  --server-generate --run-blender --blender "<path-to-that-blender>"
```

## Boundary (ADR 0008)

- This is Stage A: validate and build only. Its outputs are ephemeral and
  authorize no retention, canonical artifact, or publication.
- Do not retain, copy, or relabel the result as a candidate. Stage B needs
  separate explicit owner candidate-retention acceptance for one exact audited
  local candidate SHA, still non-canonical and not publication.
- No tag and no GitHub Release. Stage C needs separate explicit owner
  publication acceptance; this command grants none.
- `[extension-cli:WARN]` invalidates release acceptance even when the helper
  exits zero. Resolve the residue and rerun with a new `<run-id>`.

## Report

Applies **only** to a `--run-blender` invocation — a dry run has no ZIP and no
markers to report. After such a run, report:

1. The ZIP SHA-256, byte size, member list, and per-member digests.
2. Which `[extension-cli:PASS]` markers were required and observed.
3. An explicit reminder that Stage B and Stage C each need their own separate
   explicit owner acceptance, and that this run provided neither.

Never present a pre-existing ZIP found in `reports/extension` as evidence of
this run — historical artifacts are immutable evidence of the run that made
them, per `docs/agent/frozen-decisions.md`.
