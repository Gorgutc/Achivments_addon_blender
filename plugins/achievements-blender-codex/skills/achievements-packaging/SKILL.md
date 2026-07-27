---
name: achievements-packaging
description: Build and audit deterministic Blender extension release candidates.
---

# Achievements Packaging

Use for packaging, extension validation, and release-candidate audits.

Rules:
- Use `scripts/build_extension.py` instead of assembling ZIP members manually.
- Working-tree mode normalizes known UTF-8 runtime text to LF and copies binary
  payloads byte-for-byte.
- Release mode uses `--revision HEAD`, reads committed Git blobs, and fails
  closed when tracked or untracked runtime payload differs from that revision.
- Allow only `blender_manifest.toml`, `LICENSE`, root `__init__.py`, and the
  Python runtime package under `achievements/`.
- Require package-relative root runtime imports, no shipped runtime `sys.path`
  mutation, exact manifest `files = "Store progress and load local reward assets"`,
  and no manifest `network` permission.
- Reject symlinks, path traversal, duplicate ZIP entries, and unexpected files.
- Run Blender `extension validate`, `extension build`, and
  `extension server-generate` through `build_extension.py --run-blender` for
  every supported validation target. The wrapper must use `--factory-startup`
  and one disposable profile with temporary `HOME`, `USERPROFILE`, and
  `BLENDER_USER_RESOURCES`.
- Give each `server-generate` run a fresh, never-used per-run output directory
  with a new `<run-id>`. Fail closed on stale ZIP/index entries; never delete or
  mix an older baseline implicitly.
- `reports/extension/` is unsuitable for a server gate while older canonical
  ZIPs are present. Audit the ZIP in a fresh output
  and only then select one exact verified 0.2.2 candidate and deliberately
  byte-copy it to its canonical path. The destination must not already exist;
  confirm identical source/destination SHA-256 and never rebuild or overwrite
  the canonical ZIP.
- Treat per-version self-built ZIPs as build evidence only. Run install/enable
  and register/unregister smoke on all supported versions against the same exact
  frozen canonical SHA.
- Record the final ZIP SHA-256, byte size, member list, and member digests.
- Preserve immutable 0.2.1 and 0.2.0 candidates as historical evidence; never
  overwrite or relabel them.
- Missing licensed icons/tutorial content/reward `.blend` assets are explicit
  deferred epics; preserve runtime fallbacks and do not claim those assets ship.
- A release-candidate ZIP does not authorize a tag, GitHub Release, or merge.
