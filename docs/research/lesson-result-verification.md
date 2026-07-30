---
status: research-draft
implementation_authorized: false
owner_approved: false
threshold_policy: calibration-required
reward_bridge: disabled
---

# Lesson Result Verification Research Draft

This is a research draft, not an ADR and not a frozen implementation contract. It does not authorize runtime, persistence, reward, schema, asset, permission, networking, or release work.

## Status And Non-Authorization

The only proposed learner action is explicit **Submit result**. A lesson URL, elapsed time, or viewing history is not proof of a result. No implementation is authorized: `implementation_authorized: false`, `owner_approved: false`, and the reward bridge is disabled.

This draft is not complete or ready for implementation. An ADR may be considered only after a future owner approval of the implementation entry gate.

## Current Frozen Boundaries

The current add-on identity is `0.2.3`; schema `1.0.0`, the 105-achievement/9-lesson catalog, XP awards `5/10/20`, cap `1550`, local files-only permission, and disabled production networking remain frozen. This research must not alter runtime behavior, catalog, XP, rewards, assets, permissions, persistence, networking, or publication policy.

The existing reward contract remains separate: this draft must not write `rewards_claimed`, bypass unlock hashes, change XP `5/10/20` or cap `1550`, treat a URL as completion, or invoke `RewardManager`. No lesson persistence is authorized.

## Glossary

- **Submit result**: a user-triggered request to evaluate a bounded Blender snapshot; it is not an automatic lesson completion event.
- **Attempt record (`attempt_id`)**: a unique local immutable submission record. It records the declared scope, Blender/version metadata, full `evaluation_cache_key`, and immutable result; no persistence is authorized by this draft.
- **Candidate digest**: the deterministic hash of the declared scope, its canonical normalized feature graph, and Blender version. It is not an attempt id and does not include `extractor_version`.
- **Evaluation cache key (`evaluation_cache_key`)**: `lesson_id + assessment_version + rubric_digest + extractor_version + candidate_digest`. It identifies deterministic evaluation reuse, not a submitted attempt or an authorization to grant a claim, XP, or reward.
- **Outcome**: observable state in the submitted snapshot. **Process** is how the learner created it; outcome evidence cannot prove process unless an owner-approved event contract explicitly says so.
- **Indeterminate**: required evidence cannot be normalized or compared safely. It is not a pass and it is not a partial score.
- **Calibration**: owner-reviewed fixture evidence establishing whether a rubric separates positives from negatives before any threshold exists.

## Assessed Unit

Each submission creates an immutable local `attempt_id`. Its `evaluation_cache_key` is `lesson_id + assessment_version + rubric_digest + extractor_version + candidate_digest`; an identical key reuses the deterministic evaluation and never grants a new claim, XP, or reward. The candidate digest is deterministic over the declared scope, canonical normalized feature graph, and Blender version. The attempt record includes its immutable id, declared scope, normalized graph, `extractor_version`, `candidate_digest`, Blender version, and `evaluation_cache_key`.

Permitted scope names are `active_object`, `selected_objects`, `assessment_collection`, and `scene`. Every scope must declare explicit closure: the root objects/datablocks included, relationship traversal rules, and whether external references are forbidden, summarized, or included. An empty, unknown, or non-closed scope is indeterminate and blocks pass.

Outcome rules inspect only the declared snapshot. Process assertions (for example, that a learner used a particular edit sequence) are unsupported unless a future owner-approved event-only rule defines durable, privacy-safe evidence; time and URL remain non-proof.

## Rubric Schema

A future rubric is data, not executable add-on behavior. Every rule must carry these fields exactly:

```text
rule_id
feature_kind
selector
normalizer
comparator
expected
tolerance_or_exact
allowed_equivalences
mandatory
weight_points
user_explanation
fixture_refs
```

`rule_id` is stable within an assessment version. `selector`, `normalizer`, and `comparator` must be closed, deterministic declarations; `fixture_refs` names the positive, negative, boundary, and equivalence evidence that justified the rule.

## Feature Normalization

Candidate feature kinds are inventory, topology, relationships, transforms, material, Geometry Nodes, render, and event-only-if-approved. Normalization emits deterministic JSON with ordered keys and explicit type tags. Inventory order, node/link order, names, and persistent IDs have no meaning unless the rule explicitly declares their semantics.

Numeric values use canonical Blender units, normalized quaternion sign/convention, and finite floats only. Unsupported datablocks, non-finite floats, unavailable render evidence, or unsupported Blender-version semantics produce `indeterminate`, never an inferred match. Every equivalence (for example, permitted node substitution, modifier realization, transform representation, or material graph variant) must be explicit Blender equivalence declared by the rule and backed by fixtures.

## Mandatory Gates And Scoring

Mandatory gates have weight 0. Any mandatory failure, indeterminate result, unknown feature, empty scope, or missing required feature blocks pass. A missing feature fails; it does not become N/A.

Scored rules use positive integer `weight_points` values whose sum is exactly 1000. There is no partial rule credit, no N/A, and no dynamic denominator. `passed_weight` is the integer sum of passed scored-rule weights and `denominator = 1000` exactly.

```text
threshold_basis_points: null
```

The proposed `>=90%` threshold is only a rejected/unvalidated hypothesis, never a default or approved threshold. After calibration, `threshold_basis_points` is either `null` or an integer in `0..10000`; its only decision comparison is `passed_weight * 10000 >= threshold_basis_points * 1000`. Decimal display uses half-up rounding to `0.1%` and never decides an outcome.

## Tolerances And Equivalences

Tolerances and equivalences are rule-local, explicit, and boundary-fixtured. A tolerance names its unit, comparison operator, inclusivity, normalization stage, and representative just-inside/just-outside fixtures. An equivalence is neither a global fuzzy match nor a name-based heuristic: it is a documented alternative expected structure with its own positive and negative fixtures.

No rule may silently broaden its selector, tolerance, or equivalence after a result has been evaluated. Such a semantic change requires a new assessment version.

## Explainable Result

A future deterministic result must expose one of `passed`, `failed`, `indeterminate`, or `not_calibrated`; `passed` is unavailable while `threshold_basis_points: null`. The result record has stable field order: `status`, `lesson_id`, `assessment_version`, `rubric_digest`, `extractor_version`, `candidate_digest`, `scope`, `passed_weight`, `denominator`, `threshold_basis_points`, `rule_results`, and `remediation`.

Each `rule_result` is ordered by `rule_id` and contains `status`, `expected`, `observed`, `tolerance_or_exact`, `allowed_equivalences`, fixture references, a Russian user explanation, and remediation. It must include observed normalized evidence or an absence reason; comparator/tolerance, equivalence, and expected evidence remain inspectable.

The result must explain mandatory blockers before score details, preserve the immutable `attempt_id` and `evaluation_cache_key`, and make repeated evaluation of an identical cache key return the same explanation without creating a new attempt. It must not expose hidden reward or anti-cheat secrets.

## Fixture And Calibration Protocol

Future fixtures belong only under `tests/fixtures/lesson_assessment/<lesson_id>/<assessment_version>/`. Each assessment needs a manifest plus calibration, holdout, and adversarial sets: canonical positives, equivalence positives, mandatory negatives, single-fault scored negatives, tolerance boundaries, adversarial cases, cross-version cases for Blender 5.0.1/5.1.2/5.2.0, and an independent holdout.

Calibration can establish a threshold only when `max_negative_score < min_positive_score` with a nonzero integer gap. Any adversarial false positive or canonical-positive failure blocks calibration. An equivalence false negative blocks calibration or narrows the equivalence policy through a new owner decision. Holdout size and acceptable false-negative rate are owner decisions, not defaults.

## FP/FN Acceptance

False positives and false negatives are measured separately by rule, lesson, Blender version, and fixture class. A mandatory negative that passes is an adversarial false positive and blocks calibration. A canonical positive that fails blocks calibration. Equivalence false negatives either block calibration or require an owner-approved narrower policy.

No aggregate success rate can override these blockers. The owner must approve holdout size, the acceptable false-negative rate, and the disposition of any disputed equivalence before threshold assignment.

## Retry And Anti-Farming

Retries are explicit user actions only. An identical `evaluation_cache_key` reuses the deterministic evaluation; attempts and elapsed time grant no XP and no reward. Re-evaluating a pass cannot create a repeat claim. Idempotency is a correctness property, not anti-cheat.

This draft authorizes no telemetry, authentication, network, account, or anti-farming implementation. Any future abuse policy requires separate owner approval and privacy review.

## Versioning And Migration

The assessment-definition key is `lesson_id + assessment_version + rubric_digest`; it identifies a rubric definition only and is not an evidence or attempt key. Assessment versions are monotonic per lesson; any semantic change creates a new version. No silent edit, recalculation, migration, or backfill of earlier evidence is permitted.

`latest` and `best` operate on conceptual immutable attempt results keyed by `attempt_id`: `latest` is the last completed current-version result, while `best` is the maximum exact ratio among mandatory-pass results, with a latest-attempt tie break. An indeterminate result does not replace best. A new version makes older attempt records historical and leaves current status stale/not_attempted according to owner policy. Any persistence location, schema, retention, migration, or deletion policy is a separate owner/schema decision and is not authorized here.

## Reward Bridge Boundary

Passing assessment yields evidence only, not an unlock, claim, XP award, or reward action. It cannot write existing `rewards_claimed`, bypass hashes, change XP `5/10/20` or cap `1550`, treat a lesson URL as completion, or invoke `RewardManager`.

Any future bridge requires an owner-approved contract for evidence scope, claim scope, lesson-to-reward mapping, prospective payload, confirmed Blender action, atomic commit, and retry behavior. The bridge remains disabled; no lesson persistence is authorized.

## Nine-Lesson Readiness Matrix

| lesson_id | readiness_state | research boundary |
| --- | --- | --- |
| `lesson_vertices_basics` | `calibration_required` | possible exact target |
| `lesson_edit_basics` | `unsupported_pending_owner_contract` | cannot prove process from an outcome snapshot |
| `lesson_edges` | `calibration_required` | needs explicit equivalences |
| `lesson_faces` | `calibration_required` | exact topology candidate |
| `lesson_modeling` | `unsupported_pending_owner_contract` | modeling scope is too broad |
| `lesson_materials` | `calibration_required` | material node graph candidate |
| `lesson_time_management` | `unsupported_pending_owner_contract` | static snapshot is insufficient |
| `lesson_geo_nodes_intro` | `calibration_required` | Geometry Nodes graph/modifier candidate |
| `lesson_render_basics` | `calibration_required` | scene/config candidate; render event only if approved |

## Owner Decisions

- OD-01: Approve or reject assessed outcomes, lesson URLs, and canonical reference outcomes for each lesson.
- OD-02: Approve the extra-content policy for objects, collections, and external references.
- OD-03: Approve each scope and its closure rules.
- OD-04: Approve selector identity semantics for names, IDs, ordering, and relationships.
- OD-05: Approve any event-only proof contract and its privacy limits.
- OD-06: Approve rule-local tolerances and Blender equivalences.
- OD-07: Approve canonical fixtures, binary `.blend` assets, and license/provenance evidence.
- OD-08: Approve the authoring/review workflow and learner-visible diff detail.
- OD-09: Approve calibration, adversarial fixture coverage, and a nonzero-gap threshold.
- OD-10: Approve independent holdout size, acceptable false-negative rate, and equivalence disposition.
- OD-11: Approve the cross-version Blender support policy.
- OD-12: Approve evidence retention, deletion, privacy policy, and acceptance of the local-tampering limitation.
- OD-13: Approve persistence location and any schema/migration contract.
- OD-14: Approve old-pass behavior, latest/best/current-version presentation, and stale/not_attempted policy.
- OD-15: Approve whether a lesson pass gives XP; the current answer is no.
- OD-16: Approve reward-bridge evidence/claim scope, lesson-to-reward mapping, prospective payload, confirmed Blender action, atomic commit, retry, and anti-abuse policy.

## Implementation Entry Gate

The entry gate is closed. Implementation requires owner approval of rubric semantics, scope closure, fixtures and calibration, a nonzero-gap threshold, false-positive/false-negative acceptance, version policy, persistence/schema, privacy, and the reward bridge. Only then may a separate ADR and implementation task be proposed; this research draft itself authorizes none.
