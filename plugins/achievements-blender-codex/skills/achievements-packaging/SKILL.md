---
name: achievements-packaging
description: Build and audit deterministic Blender extension release candidates.
---

# Achievements Packaging

Use for packaging, extension validation, and release-candidate audits.

Rules:
- Release identity: `0.2.3` source candidate. No tag, GitHub Release, or
  publication is authorized without explicit owner ship acceptance; a local
  retained candidate is not publication. The historical `achievements-0.2.2.zip` is immutable
  pre-PR16 evidence and is not a current install or build artifact.
- Release stages: (A) a full validation gate produces only ephemeral outputs and authorizes no retention, canonical artifact, or publication; (B) only separate explicit owner candidate-retention acceptance may preserve one exact audited local candidate SHA, which remains non-canonical and not publication; (C) only separate explicit owner publication acceptance may create `v0.2.3` tag and GitHub Release from that exact retained candidate. This session grants none.
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
  ZIPs are present. Audit each 0.2.3 ZIP only in its fresh output; do not
  byte-copy it to a canonical path, rebuild or overwrite historical artifacts,
  or use the historical 0.2.2 ZIP as current evidence.
- Treat per-version self-built ZIPs as build evidence only. A full gate leaves
  them ephemeral; only separate explicit owner candidate-retention acceptance
  may preserve one exact audited local-candidate SHA. A separate explicit owner
  publication acceptance is required for `v0.2.3` and GitHub Release.
- Record the final ZIP SHA-256, byte size, member list, and member digests.
- Preserve immutable 0.2.1 and 0.2.0 candidates as historical evidence; never
  overwrite or relabel them.
- Missing licensed icons/tutorial content/reward `.blend` assets are explicit
  deferred epics; preserve runtime fallbacks and do not claim those assets ship.
- A release-candidate ZIP does not authorize a tag, GitHub Release, or merge.
