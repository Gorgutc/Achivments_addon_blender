# ADR 0004: Extension Namespace And Files Permission

Status: accepted for Achievements 0.2.2.

## Context

Blender installs extensions below a repository-specific namespace such as `bl_ext.<repository>.achievements`. The repository root is therefore a package whose exact qualified name is chosen by Blender. Importing support modules through an ambient top-level `achievements` name can bind an unrelated package or fail when the extension directory is not already on Python's search path. Adding that directory to `sys.path` creates a process-global alias that can survive reloads and interfere with another installed extension.

The add-on also keeps progress under `~/BlenderAchievements/` and may load local reward `.blend` assets. The extension manifest must state this file access narrowly and must not imply network access while production sync remains disabled.

## Decision

- Import every root-to-support-module dependency through package-relative `.achievements` paths inside Blender's installed namespace.
- Do not import the support package through top-level `achievements.*` paths from shipped root runtime code.
- Do not access or mutate `sys.path` in shipped runtime code. Test and verifier harnesses may configure their own import context without changing the production loader contract.
- Declare exactly `files = "Store progress and load local reward assets"` under `[permissions]` in `blender_manifest.toml`.
- Do not declare `network` permission while the production sync backend remains disabled.
- Keep the package ID, Blender floor, catalog IDs, `SCHEMA_VERSION`, persistence keys and paths, operators, handlers, UI behavior, reward fallbacks, and extension-removal flow unchanged. The release identity advances to 0.2.2 only.

## Verification

- Parse every shipped Python file with `ast` and reject absolute intra-extension `achievements` imports and `sys.path` access or mutation.
- Parse `blender_manifest.toml` and require the exact `files` permission reason and absence of a `network` permission.
- Run source-checkout and installed-ZIP register/unregister smoke under temporary `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES` on Blender 5.0.1, 5.1.2, and 5.2.0.
- Retain the release payload allowlist and exact Git-byte audit. The immutable 0.2.1 and 0.2.0 ZIPs remain historical evidence and are never overwritten or relabeled as 0.2.2.

## Consequences

Installed imports are isolated to Blender's chosen extension namespace and do not leak a top-level alias into the interpreter. The manifest accurately discloses the existing local file operations without expanding the disabled cloud surface. Any future network backend or file-scope change requires a separate owner-approved decision and matching manifest, runtime, test, and documentation updates.
