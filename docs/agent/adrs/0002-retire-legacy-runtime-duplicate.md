# ADR 0002: Retire the legacy runtime duplicate

Status: accepted for the Achievements 0.2.0 technical closeout.

## Context

At baseline `main@04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3`, the tracked file
`achievements_v01 (4).py` was byte-identical to the canonical root runtime
`__init__.py`. Keeping two runtime copies created an avoidable drift surface.

No-loss evidence captured before deletion:

- introduction commit: `a0e443c513976b289230072b84146de39a6a5384`
- recorded baseline revision: `04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3`
- Git blob: `21d5023697370800ced934959463da1e4be7cd5f`
- canonical LF Git blob: 84,975 bytes, SHA-256 `9CB06CA4B4CECF48B2CA52E59F5F930B45FC537F5A945D262EBC086551090681`
- captured Windows checkout with `core.autocrlf=true`: 87,144 bytes, SHA-256 `62DDB0163B29C8C4A39347DEAF19D201F71C50A3D0F9A48F803387444DB24DAE`
- equality check: the duplicate and baseline root `__init__.py` had the same Git blob

## Decision

Delete `achievements_v01 (4).py`. The repository has exactly one canonical
Blender runtime entrypoint: root `__init__.py`. Static verification must reject
reintroduction of the legacy duplicate.

## Recovery

The exact retired bytes remain recoverable from Git without relying on an
untracked backup. Perform restoration only in a disposable worktree or audit
branch so the active runtime does not regain a duplicate:

```powershell
git restore --source=04c2b02bd710d5bde0d28f3ad966a0f4d0fecae3 -- "achievements_v01 (4).py"
Get-FileHash -Algorithm SHA256 -LiteralPath "achievements_v01 (4).py"
git hash-object "achievements_v01 (4).py"
```

The restored working-tree file reproduces SHA-256 `62DDB016...24DAE` when Git
applies the recorded Windows LF-to-CRLF checkout conversion. Raw
`git cat-file blob 21d5023697370800ced934959463da1e4be7cd5f` bytes reproduce
SHA-256 `9CB06CA4...0681`. The 2,169-byte size delta equals one added carriage
return for each of the file's 2,169 lines. Recovery is for audit/history only;
the file must not be restored to the active runtime payload without a new owner
decision.
