# Packaging And Release

Release packaging is now active Iteration 12 tooling.

The extension manifest is `blender_manifest.toml`. Current Blender registration still lives in the repository root `__init__.py`; the `achievements/` package is included as runtime support modules. `achievements_v01 (4).py` remains a permanent byte-identical duplicate for source-drift detection, but it is not shipped in the official extension payload.

## Release Payload

`scripts/build_extension.py` prepares a clean staging tree under `reports/extension/source` and prints the exact Blender extension commands to run from the shell. The helper refuses to clean or write a release source directory outside the generated `reports/` tree.

The release package excludes docs/tests/plugins/scripts, GitHub workflow files, repository instructions, generated reports, and `achievements_v01 (4).py`. The shipped payload is intentionally lean:

- `blender_manifest.toml`
- root `__init__.py`
- `achievements/`

The generated ZIP is expected at `reports/extension/achievements-0.1.0.zip`. `reports/` is ignored and must remain a generated local output location.

## Commands

Prepare the staged source and print commands:

```bash
uv run python scripts/build_extension.py --output-dir reports/extension --server-generate
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

Iteration 8 asset policy still applies: no reward `.blend` assets are bundled or promoted into an official extension package until licenses are explicitly approved. The add-on must continue to work through missing-asset fallbacks for material, mesh, and geo node rewards.

## Release Gate

Before shipping a release package:

- Run the fast gate: `verify_frozen`, `verify_codex_plugin`, `ruff`, and `pytest`.
- Run the Blender smoke suites under temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.
- Run extension `validate`, `build`, and optional `server-generate`.
- Inspect the generated ZIP contents and confirm only the lean runtime payload is included.
- Run `/review`; if the slash command is unavailable, use `docs/agent/code-review.md` fallback.
