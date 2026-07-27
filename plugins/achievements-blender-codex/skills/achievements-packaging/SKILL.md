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
- Reject symlinks, path traversal, duplicate ZIP entries, and unexpected files.
- Run Blender `extension validate`, `extension build`, and `server-generate`,
  then perform install/enable and register/unregister smoke in temporary user
  profiles for every supported validation target.
- Record the final ZIP SHA-256, byte size, member list, and member digests.
- Missing licensed icons/tutorial content/reward `.blend` assets are explicit
  deferred epics; preserve runtime fallbacks and do not claim those assets ship.
- A release-candidate ZIP does not authorize a tag, GitHub Release, or merge.
