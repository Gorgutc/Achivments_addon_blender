# Archive Policy

ADR 0002 retired the byte-identical `achievements_v01 (4).py` duplicate during the user-approved 0.2.0 technical closeout. Root `__init__.py` is the only canonical Blender runtime. The retired bytes remain recoverable from their recorded Git blob, commit, and SHA-256; do not restore a second active runtime without a new owner decision.

The obsolete `achievements_100_list.md` was moved byte-for-byte to `docs/archive/achievements_100_list.md`. It is historical planning evidence, not the current 105-achievement catalog.

Future archive decisions should preserve:
- The canonical source file selected by maintainers.
- A clear migration note explaining why an artifact was archived.
- A verifier update when an accepted policy change alters required tracked artifacts.
- Any historical notes needed to reconstruct old achievement IDs.

Never archive real user progress data from `~/BlenderAchievements` into the repository.
