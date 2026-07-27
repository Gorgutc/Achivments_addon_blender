# Packaging And Release

Release packaging produces the Achievements 0.2.0 candidate from one canonical runtime.

The extension manifest is `blender_manifest.toml`. Blender registration lives in root `__init__.py`; `achievements/` contains runtime support modules. ADR 0002 retired `achievements_v01 (4).py`, and verification rejects any second runtime copy.

## Release Payload

`scripts/build_extension.py` prepares a clean staging tree under `reports/extension/source` and prints the exact Blender extension commands to run from the shell. The helper refuses to clean or write outside the generated `reports/` tree.

Working-tree mode LF-normalizes known UTF-8 runtime files and copies any approved binary payload byte-for-byte. Release mode `--revision HEAD` reads committed Git blobs and fails closed if tracked or untracked runtime payload differs from the selected revision.

The release package excludes docs/tests/plugins/scripts, GitHub workflow files, repository instructions, generated reports, historical files, symlinks, and unexpected paths. The shipped payload is intentionally lean:

- `blender_manifest.toml`
- `LICENSE`
- root `__init__.py`
- `achievements/`

The generated ZIP is expected at `reports/extension/achievements-0.2.0.zip`. `reports/` is ignored and remains generated local output.

## Commands

Prepare the staged source and print commands:

```bash
uv run python scripts/build_extension.py --revision HEAD --output-dir reports/extension --server-generate
```

Validate the staged source:

```bash
blender --background --command extension validate reports/extension/source
```

Build the ZIP:

```bash
blender --background --command extension build --source-dir reports/extension/source --output-dir reports/extension
```

Generate the optional static extensions repository metadata:

```bash
blender --background --command extension server-generate --repo-dir reports/extension --html
```

Run the Blender commands directly from the shell. The helper intentionally does not spawn Blender itself because direct shell invocation is the stable Windows path for `blender --command extension ...`.

## Asset Policy

The add-on code is GPL-3.0-or-later and the full license text ships as `LICENSE`. No reward `.blend` or icon assets are bundled until compatible licenses are explicitly approved; future extension assets must follow Blender's CC0 asset policy. Missing-asset fallbacks for material, mesh, and Geometry Nodes rewards remain part of the release contract.

## Release Gate

Before shipping a release package:

- Run the fast gate: `verify_frozen`, `verify_codex_plugin`, `ruff`, and `pytest`.
- Run all six Blender smoke suites under temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES` on Blender 5.0.1, 5.1.2, and 5.2.0.
- Run extension `validate`, `build`, and `server-generate` on all three targets.
- Install/enable the ZIP and run register/unregister smoke on all three targets.
- Confirm the allowlist, absence of symlink/traversal/duplicates, Git-blob byte equality, member digests, final ZIP SHA-256, and byte size.
- Run `/review`; if the slash command is unavailable, use `docs/agent/code-review.md` fallback.
- A verified candidate does not authorize a tag, GitHub Release, or merge.
