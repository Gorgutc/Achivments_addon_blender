# Packaging And Release

Release packaging validates the Achievements 0.2.3 source candidate from one canonical runtime.

## Release Identity And Ship Authorization

Release identity: `0.2.3` source candidate.
No tag, GitHub Release, or publication is authorized without explicit owner ship acceptance; a local retained candidate is not publication.
The historical `achievements-0.2.2.zip` is immutable pre-PR16 evidence and is not a current install or build artifact.
Release stages: (A) a full validation gate produces only ephemeral outputs and authorizes no retention, canonical artifact, or publication; (B) only separate explicit owner candidate-retention acceptance may preserve one exact audited local candidate SHA, which remains non-canonical and not publication; (C) only separate explicit owner publication acceptance may create `v0.2.3` tag and GitHub Release from that exact retained candidate. This session grants none.

The extension manifest is `blender_manifest.toml`. Blender registration lives in root `__init__.py`; `achievements/` contains runtime support modules. Root imports those modules through package-relative paths inside Blender's installed extension namespace and never mutates `sys.path`. ADR 0002 retired `achievements_v01 (4).py`, and verification rejects any second runtime copy. ADR 0004 freezes the namespace and manifest permission policy.

## Release Payload

`scripts/build_extension.py` prepares a clean staging tree and can execute the
Blender extension commands through its isolated `--run-blender` wrapper. The
helper refuses to clean or write outside the generated `reports/` tree.

Working-tree mode LF-normalizes known UTF-8 runtime files and copies any approved binary payload byte-for-byte. Release mode `--revision HEAD` reads committed Git blobs and fails closed if tracked or untracked runtime payload differs from the selected revision.

The release package excludes docs/tests/plugins/scripts, GitHub workflow files, repository instructions, generated reports, historical files, symlinks, and unexpected paths. The shipped payload is intentionally lean:

- `blender_manifest.toml`
- `LICENSE`
- root `__init__.py`
- `achievements/`

`reports/` is ignored generated local output. A full validation gate leaves
0.2.3 ZIPs ephemeral in fresh per-run outputs. Only separate explicit owner
candidate-retention acceptance may preserve one exact audited local-candidate
SHA; that local candidate is not publication. The
historical 0.2.2, 0.2.1, and 0.2.0 ZIPs are immutable evidence and must not be
overwritten, relabeled, or used as current artifacts.

The packaged manifest must contain exactly
`files = "Store progress and load local reward assets"` under `[permissions]`.
It must not request `network` permission while production networking is disabled.
This declaration covers the existing progress and local reward-asset paths; it
does not add content assets or expand the payload allowlist.

## Commands

For each Blender version, prepare the staged source and execute the complete
release gate in a fresh per-run repository directory:

```bash
uv run python scripts/build_extension.py --revision HEAD --source-dir reports/extension-validation/<run-id>/blender-5.1.2/source --output-dir reports/extension-validation/<run-id>/blender-5.1.2 --server-generate --run-blender --blender "<path-to-blender-5.1.2>"
```

Pass `--blender <path>` to repeat this command for each supported Blender
version. Replace `<run-id>` on every rerun; the output path must be fresh and
never-used. The wrapper runs all requested subcommands in one disposable profile,
sets temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`, and removes
the profile afterward. Every Blender command includes `--background` and
`--factory-startup`.

Without `--run-blender`, the helper remains print-only and emits the exact
commands for audit. Their shape is:

```bash
blender --background --factory-startup --command extension validate reports/extension-validation/<run-id>/blender-5.1.2/source
blender --background --factory-startup --command extension build --source-dir reports/extension-validation/<run-id>/blender-5.1.2/source --output-dir reports/extension-validation/<run-id>/blender-5.1.2
blender --background --factory-startup --command extension server-generate --repo-dir reports/extension-validation/<run-id>/blender-5.1.2 --html
```

Do not run the printed commands against the normal user profile. The
`--run-blender` path captures stdout/stderr and fails closed on a non-zero exit,
`Traceback`, error/warning markers, or missing command-specific success text.
Temporary-profile cleanup residue is intentionally nonfatal to the helper, but
its `[extension-cli:WARN]` invalidates release acceptance even when the process
exits zero; resolve the residue and rerun with a new `<run-id>`.
`server-generate` must report exactly one package. Its output must be a fresh
per-run directory containing only the helper's direct staged `source/` before
execution; the helper rejects stale ZIP/index entries and never deletes or
mixes an older baseline implicitly.

The default `reports/extension/` directory is unsuitable for a server gate while
older canonical ZIPs are present. After all version-specific build gates pass,
audit allowlist, member digests, Git bytes, SHA-256, and size in fresh outputs.
Do not byte-copy a 0.2.3 validation ZIP to a canonical path during this task,
and do not rebuild, overwrite, delete, or mix an existing historical baseline.
After a full gate, only separate explicit owner candidate-retention acceptance
may preserve a local candidate, which remains non-canonical and not
publication. Only separate explicit owner publication acceptance may select
that exact retained 0.2.3 artifact for a `v0.2.3` tag and GitHub Release.

## Asset Policy

The add-on code is GPL-3.0-or-later and the full license text ships as `LICENSE`. No reward `.blend` or icon assets are bundled until compatible licenses are explicitly approved; future extension assets must follow Blender's CC0 asset policy. Missing-asset fallbacks for material, mesh, and Geometry Nodes rewards remain part of the release contract.

## Release Gate

Before shipping a release package:

- Run the fast gate: `verify_frozen`, `verify_codex_plugin`, `verify_predicates`, `ruff`, and `pytest`.
- Run all six Blender smoke suites under temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES` on Blender 5.0.1, 5.1.2, and 5.2.0.
- Run isolated extension `validate`, `build`, and `server-generate` through
  `--run-blender` on all three targets; require clean `[extension-cli:PASS]`
  markers and no traceback/error/warning output. Give each server gate its own
  fresh per-run output directory.
- Treat any `[extension-cli:WARN]` as a failed release gate even when the helper
  exits zero; resolve cleanup residue and rerun in a new `<run-id>`.
- Install/enable the ZIP and run register/unregister smoke on all three targets.
- Use the same exact audited validation/retained local-candidate SHA for those
  three install smokes. That retained local candidate is not publication;
  per-version self-built ZIPs are build evidence only.
- Confirm the allowlist, absence of symlink/traversal/duplicates, Git-blob byte equality, member digests, final ZIP SHA-256, and byte size.
- Confirm package-relative runtime imports, absence of runtime `sys.path` mutation, the exact manifest `files` reason, and absence of manifest `network` permission.
- Run `/review`; if the slash command is unavailable, use `docs/agent/code-review.md` fallback.
- A verified candidate does not authorize a tag, GitHub Release, or merge.
