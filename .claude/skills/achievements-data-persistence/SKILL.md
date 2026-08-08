---
name: achievements-data-persistence
description: Protect progress JSON persistence and user data boundaries.
---

# Achievements Data Persistence

Use for data path, JSON schema, save/load, and test isolation work.

Rules:
- Never write tests against real `~/BlenderAchievements`.
- Preserve current JSON schema unless the task explicitly migrates it.
- Treat unlock hashes as local integrity markers, not authentication or
  anti-cheat. Preserve the salt/username/SHA-256/16-character legacy format.
  Keep `os.getlogin()` authoritative when it succeeds; a headless-only
  `getpass.getuser()`/fixed-value fallback must remain deterministic and must
  never derive from the temporary HOME path.
- Backfill missing hashes only while migrating legacy payloads without the
  current schema. Never repair a missing or forged hash in current-schema data.
- Verify temp-home isolation in Blender smoke.
- Do not track generated progress files.
