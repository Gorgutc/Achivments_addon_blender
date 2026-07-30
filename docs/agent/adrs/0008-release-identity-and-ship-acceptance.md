# ADR 0008: Release Identity And Ship Acceptance

Status: accepted for the 0.2.3 source candidate on 2026-07-30.

## Context

The immutable `achievements-0.2.2.zip` was produced before PR #16 through PR
#18. It has 22 members and does not contain `achievements/levels.py`, so it
cannot truthfully represent current `main`. Reusing its version for a new
payload would make install and release guidance ambiguous.

## Decision

- Advance the coherent source identity to `0.2.3` in `bl_info`, package
  metadata, the extension manifest, and Python project metadata.
- Treat 0.2.3 as an unpublished source candidate. Stage A is a full validation
  gate whose outputs remain ephemeral and which authorizes no retention,
  canonical artifact, or publication.
- Stage B requires separate explicit owner candidate-retention acceptance before
  preserving one exact audited local candidate SHA; it remains non-canonical and
  is not publication.
- Stage C requires separate explicit owner publication acceptance before
  creating `v0.2.3` and a GitHub Release from that exact retained candidate.
  This session grants none of stages A, B, or C.
- Keep the historical 0.2.2 ZIP immutable, pre-PR16, and unavailable as a
  current install or build artifact. Do not rebuild, overwrite, relabel, or
  delete it.
- Preserve the catalog, schema, persistence, assets, progress data, runtime
  behavior, package allowlist, files-only permission, and disabled networking.

## Consequences

Release guidance must fail closed if it loses the 0.2.3 source-candidate,
historical-artifact, or three-stage acceptance markers. A later release task
must complete Stage A, obtain Stage B retention acceptance, then separately
obtain Stage C publication acceptance for the exact retained candidate.
