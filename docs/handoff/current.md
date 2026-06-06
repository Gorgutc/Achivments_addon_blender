# Current Handoff

## Goal

Iteration 12: Release.

Finalize the Blender extension release path, fix the optional Blender 5.2 alpha canary workflow behavior when `BLENDER_5_2_ALPHA_URL` is unset, and document the release packaging gate without changing add-on runtime behavior.

## Changed Files

- `.github/workflows/blender-smoke.yml`
- `README.md`
- `docs/agent/packaging-release.md`
- `docs/agent/quality-tooling.md`
- `docs/agent/verification.md`
- `docs/handoff/current.md`
- `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`
- `scripts/build_extension.py`
- `scripts/verify_codex_plugin.py`
- `tests/test_infra_scripts.py`
- `tests/test_release_packaging.py`

## Done

- Investigated the failed GitHub Actions check `Achievements Blender Smoke / blender-5-2-alpha-canary`.
- Root cause: the optional canary job received an empty `BLENDER_5_2_ALPHA_URL`, so the workflow failed while trying to install Blender 5.2 alpha.
- Added `id: install-blender` and `skip_smoke` output handling to `.github/workflows/blender-smoke.yml`.
- The canary now emits `Skipping optional Blender 5.2 alpha canary` and skips smoke steps when `BLENDER_5_2_ALPHA_URL` is empty; the stable Blender 5.1 row still fails if its URL is missing.
- Added release packaging helper `scripts/build_extension.py`.
- Prepared a lean release source tree under `reports/extension/source` with only `blender_manifest.toml`, root `__init__.py`, and `achievements/`.
- The release package excludes repository docs, tests, scripts, plugins, GitHub workflow files, and `achievements_v01 (4).py`.
- Verified the generated ZIP path `reports/extension/achievements-0.1.0.zip` and static repository generation result `found 1 packages`.
- Updated README, verification docs, quality-tooling docs, packaging-release docs, roadmap, infra verifier, and tests for Iteration 12.
- Left `__init__.py` and `achievements_v01 (4).py` untouched, so the duplicate contract remains unchanged.
- Did not touch real `~/BlenderAchievements` data.

## Remaining

- Configure repository variable `BLENDER_5_2_ALPHA_URL` if real Blender 5.2 alpha coverage is required in GitHub Actions.
- Keep Blender 5.2 alpha non-blocking unless a future explicit release decision promotes it to a blocking target.
- Asset/license policy remains open: no reward `.blend` assets are bundled until licenses are explicitly approved.
- Future release work can decide whether to update known `bl_info` policy drift; this iteration keeps runtime source unchanged.

## Verification

- Targeted checks:
  - `uv run pytest tests\test_release_packaging.py` passed: `7 passed`.
  - `uv run ruff check scripts\build_extension.py tests\test_release_packaging.py` passed.
  - `uv run python scripts/build_extension.py --output-dir reports\extension --server-generate` prepared `12 release files` and printed shell-safe Blender commands.
  - `blender --background --command extension validate reports\extension\source` passed.
  - `& 'C:\Program Files\Blender Foundation\Blender 5.1\blender.exe' '--background' '--command' 'extension' 'validate' 'reports\extension\source'` passed.
  - `blender --background --command extension build --source-dir reports\extension\source --output-dir reports\extension` passed and produced `reports/extension/achievements-0.1.0.zip`.
  - `blender --background --command extension server-generate --repo-dir reports\extension --html` passed with `found 1 packages`.
  - `tar -tf reports\extension\achievements-0.1.0.zip` confirmed the ZIP contains only `blender_manifest.toml`, root `__init__.py`, and `achievements/`.
- Final fast gate:
  - `uv run python scripts/verify_frozen.py` passed: `35/35 PASS`.
  - `uv run python scripts/verify_codex_plugin.py` passed: `94/94 PASS`.
  - `uv run ruff check .` passed.
  - `uv run pytest` passed: `61 passed`.
- Final Blender smoke gate on Blender 5.1.2 with temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`:
  - `uv run python scripts/run_blender_smoke.py --suite register` passed.
  - `uv run python scripts/run_blender_smoke.py --suite lifecycle_stress` passed.
  - `uv run python scripts/run_blender_smoke.py --suite persistence` passed.
  - `uv run python scripts/run_blender_smoke.py --suite engine` passed.
  - `uv run python scripts/run_blender_smoke.py --suite rewards` passed.
  - `uv run python scripts/run_blender_smoke.py --suite ui_visual` passed and saved `ui_visual_contract.png` under the temporary visual QA artifact directory.
  - `git diff --cached --check` passed.

## Agents And Review

- `quality_tooling_architect` sidecar audited the canary failure and recommended canary-only skip behavior for missing `BLENDER_5_2_ALPHA_URL`.
- First read-only review sidecar found four issues: unbounded `shutil.rmtree`, unsafe printed command quoting, handoff pending text, and staged whitespace. All four were fixed.
- Final read-only verification sidecar found the remaining handoff-only inconsistency (`5 passed` and pending review/gate text). This handoff now records the actual final results.
- Final `/review` fallback status: PASS. The staged diff matches Iteration 12 scope, canary skip behavior is documented and tested, release packaging uses a bounded generated directory and shell-safe printed commands, runtime source and duplicate are unchanged, generated ZIP contents are lean, and residual risks are listed below.

## Blockers

None for the release tooling PR.

## Residual Risks

- Empty `BLENDER_5_2_ALPHA_URL` now skips the optional canary without failing, but that run provides no Blender 5.2 alpha coverage.
- The generated extension ZIP intentionally omits reward `.blend` assets until asset licenses are explicitly approved.
- `reports/` remains generated local output and is ignored by git.
- Known add-on metadata drift in runtime `bl_info` is not changed in this iteration because runtime source and duplicate were intentionally left untouched.

## Next Start Prompt

Continue after Iteration 12 merge. Read `docs/superpowers/plans/2026-06-01-achievements-iterative-roadmap.md`, `docs/handoff/current.md`, `docs/agent/packaging-release.md`, `docs/agent/frozen-application-contract.md`, and `docs/agent/verification.md`. Do not touch real `~/BlenderAchievements` data. Start the next user-approved release or post-release task, preserve the byte-identical duplicate contract, keep README updated, and decide bundled reward asset/license policy before packaging any reward assets.
