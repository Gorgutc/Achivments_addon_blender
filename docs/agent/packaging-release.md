# Packaging And Release

Release packaging produces the Achievements 0.2.0 candidate from one canonical runtime.

The extension manifest is `blender_manifest.toml`. Blender registration lives in root `__init__.py`; `achievements/` contains runtime support modules. ADR 0002 retired `achievements_v01 (4).py`, and verification rejects any second runtime copy.

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

The audited ZIP is deliberately published at
`reports/extension/achievements-0.2.0.zip`. `reports/` is ignored and remains
generated local output.

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
its `achievements-0.1.0.zip` baseline is present. After all version-specific
build gates pass, audit allowlist, member digests, Git bytes, SHA-256, and size
in the fresh outputs. Then select one exact audited artifact, freeze its
SHA-256/member digests, and deliberately byte-copy
that same
`achievements-0.2.0.zip` to
`reports/extension/achievements-0.2.0.zip`. This publication copy is separate
from the helper: never rebuild or overwrite the canonical ZIP, and never delete
or mix an existing baseline implicitly. The canonical destination must not
already exist; verify identical source/destination SHA-256.

After recording and comparing the audited hashes, the deliberate Windows copy
is:

```powershell
$verifiedZip = "reports/extension-validation/<run-id>/blender-5.2.0/achievements-0.2.0.zip"
$canonicalZip = "reports/extension/achievements-0.2.0.zip"
if (Test-Path -LiteralPath $canonicalZip) { throw "Canonical candidate already exists" }
Copy-Item -LiteralPath $verifiedZip -Destination $canonicalZip
if ((Get-FileHash -Algorithm SHA256 -LiteralPath $verifiedZip).Hash -ne (Get-FileHash -Algorithm SHA256 -LiteralPath $canonicalZip).Hash) { throw "Published candidate hash mismatch" }
```

## Asset Policy

The add-on code is GPL-3.0-or-later and the full license text ships as `LICENSE`. No reward `.blend` or icon assets are bundled until compatible licenses are explicitly approved; future extension assets must follow Blender's CC0 asset policy. Missing-asset fallbacks for material, mesh, and Geometry Nodes rewards remain part of the release contract.

## Release Gate

Before shipping a release package:

- Run the fast gate: `verify_frozen`, `verify_codex_plugin`, `ruff`, and `pytest`.
- Run all six Blender smoke suites under temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES` on Blender 5.0.1, 5.1.2, and 5.2.0.
- Run isolated extension `validate`, `build`, and `server-generate` through
  `--run-blender` on all three targets; require clean `[extension-cli:PASS]`
  markers and no traceback/error/warning output. Give each server gate its own
  fresh per-run output directory.
- Treat any `[extension-cli:WARN]` as a failed release gate even when the helper
  exits zero; resolve cleanup residue and rerun in a new `<run-id>`.
- Install/enable the ZIP and run register/unregister smoke on all three targets.
- Use the same exact frozen canonical SHA for those three install smokes;
  per-version self-built ZIPs are build evidence only.
- Confirm the allowlist, absence of symlink/traversal/duplicates, Git-blob byte equality, member digests, final ZIP SHA-256, and byte size.
- Run `/review`; if the slash command is unavailable, use `docs/agent/code-review.md` fallback.
- A verified candidate does not authorize a tag, GitHub Release, or merge.
