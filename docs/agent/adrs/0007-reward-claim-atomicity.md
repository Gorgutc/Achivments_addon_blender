# ADR 0007: Reward Claim Atomicity

Status: accepted for the 2026-07-29 reward-correctness slice.

## Context

Asset rewards were added to `stats.rewards_claimed` and persisted even when the expected datablock was absent or Blender-side application was a no-op. A JSON write failure after a successful Blender mutation also left no reliable way to finish the claim without applying a duplicate reward. Production `.blend` rewards require a strict boundary between an attempted action, a proven action, and a persisted claim.

## Decision

- Preserve unlock and unlock-hash verification as the entry gate. This ADR does not turn local integrity markers into authentication or anti-piracy controls.
- `material`, `mesh`, and `geo_nodes` plans set `claim_after_apply`; tutorial and `none` rewards remain claim-free. Preserve `RewardResult.mark_claimed` as a read-only compatibility alias.
- A material succeeds only after the expected/generated Material is assigned to an active mesh. A mesh succeeds only after an expected/generated MESH Object is linked to a collection. A geo-node reward succeeds only after Blender returns a real `NODES` modifier on the active object and the expected/generated GeometryNodeTree is assigned to it; supported non-mesh geometry targets remain valid.
- A missing expected datablock, incompatible target, wrong datablock subtype, false postcondition, or Blender exception does not call persistence and does not change the runtime claim set. Newly loaded/created Blender ID deltas and partial modifiers are removed; failed material replacement restores data/object links, empty slots, and the active slot index for every object sharing the mesh.
- On first successful application, `payload_from_stats(..., reward_claim=id)` builds a prospective payload without mutating `stats.rewards_claimed`. `save_data` performs the existing same-directory atomic JSON write first and adds the runtime claim only after that write succeeds.
- A JSON write failure after confirmed application returns `FINISHED` with an explicit retry warning because the Blender action already happened. The action witness remains marked with `_achievements_reward_id`, `_achievements_reward_type`, and `_achievements_reward_name`; an unclaimed retry recovers that witness and retries persistence without duplicating the reward.
- Recovery markers live on Material, Object, or GeometryNodeTree IDs. They are idempotency metadata for the current Blender scene, not security credentials and not a persistence-schema field.
- A reward whose claim is already persisted keeps the existing explicit reapply behavior and does not perform a redundant claim save.
- Keep `SCHEMA_VERSION = "1.0.0"`, the exact JSON key set, add-on version `0.2.2`, catalog IDs, reward manifest, asset paths, and extension permissions unchanged.

## Verification

- Pure tests freeze prospective payload construction without runtime mutation and planner behavior for first claim versus persisted reapply.
- The static verifier freezes action-before-save ordering, fail-closed dispatch, absence of direct operator claim mutation, prospective-save gating, and the required retry matrix; mutant tests prove the guard fails on regressions.
- Blender reward smoke covers linked and fallback material/mesh/geo actions, two failed writes followed by recovery, exact runtime/JSON claims, no-op and wrong-type denials, nested dependency cleanup, material-slot and active-index restoration, partial modifier/object rollback, and persisted reapply.
- Reward smoke runs only with disposable `HOME`, `USERPROFILE`, and `BLENDER_USER_RESOURCES`.

## Consequences

Claims now mean both the Blender-side action and the atomic JSON commit succeeded. A failed persistence attempt leaves a visible/recoverable witness rather than a false claim; retry completes the write without creating a duplicate. An external process crash between action and save can only recover automatically when the marked Blender scene state survives. This ADR does not add licensing, cloud identity, catalog authoring UI, bundled production assets, or a release artifact.
