# Validation Rules and Enforceable Trust Thresholds

## Purpose
Define machine-checkable validation rules for the in-repo analyst workflow so warning and stop behavior is deterministic, visible, and auditable.

## Validation output contract
Each run emits `stages.validation` with:
- `events[]` (rule-level decisions)
- `warn_count`
- `fail_count`
- `stop_recommended`
- `can_publish`

Each `event` includes:
- `rule_id`
- `status` (`warn` or `fail`)
- `message`
- `measured`
- `threshold`
- `analyst_visible_signal`
- `fallback`
- `stop_run`
- `timestamp`

## Rule Set

| Rule ID | Failure mode | Status trigger | Enforceable threshold |
|---|---|---|---|
| FM-001-duplicate-inflation | Duplicate inflation | warn/fail | warn >= 0.35 duplicate ratio; fail >= 0.60 |
| FM-002-source-specific-failure | Source failures | warn/fail | warn any non-success source; fail if all non-success |
| FM-003-rate-limit-backoff | Rate limiting | warn | warn if source metadata indicates 429 retry/backoff |
| FM-004-empty-ingestion | Empty canonical evidence | fail | fail if `valid_count == 0` |
| FM-005-schema-drift | Schema drift | warn/fail | warn invalid ratio >= 0.20; fail >= 0.50 |
| FM-006-weak-source-diversity | Weak diversity | warn | warn if unique sources <= 1 (with non-trivial evidence) |
| FM-007-misleading-timeline-spikes | Misleading spikes | warn | warn if peak ratio >= 0.70 and duplicate ratio >= 0.35 |
| FM-008-low-confidence-geospatial | Weak geo inference | warn | warn if all geo entities are ambiguous/low confidence |
| FM-009-weak-clusters | Weak clustering | warn | warn if weak cluster ratio >= 0.75 |
| FM-010-citation-support | Missing/weak citations | warn/fail | fail if citation coverage incomplete; warn if weak citation share >= 0.40 |
| FM-011-silent-ui-degradation | Missing artifact contract | fail | fail if any required artifact key is absent |
| FM-012-timeline-normalization-mismatch | Aggregation inconsistency | fail | fail if timeline total article count != normalization valid_count |

## Warn vs Stop policy
- **Warn:** analyst may continue inspection, but must see issue and remediation in UI.
- **Stop:** `stop_recommended=true`, `can_publish=false`; run data remains inspectable for diagnosis.

## Required artifact keys
Validation enforces presence of:
- `deduplicated_article_set`
- `canonical_lineage_duplicate_map`
- `cluster_artifact`
- `citation_index`
- `evidence_bundles`
- `geospatial_entities_markers`
- `analyst_warnings`

## UI visibility requirements
Major warnings and stop gates must be visible in Gradio outputs, not logs-only:
1. run summary warning block,
2. warning payload,
3. validation payload.

## Publish safety rule
A run is publish-safe only when:
- `can_publish == true`
- all stop rules pass
- citation coverage is complete.

## Lightweight implementation principle
Rules stay in-repo and deterministic; thresholds are explicit constants/conditions, not hidden heuristics.

## Additional enforced gates (2026-04)
| Rule ID | Failure mode | Status trigger | Enforceable threshold |
|---|---|---|---|
| FM-013-required-gdelt-source | Required GDELT source unavailable | fail | fail if GDELT source status != success |
| FM-014-unknown-date-peak | Timeline date integrity failure | fail | fail if peak day resolves to `unknown` |
| FM-015-missing-event-geospatial | Invalid map semantics | fail | fail when non-trivial run has zero `event_location` entities |

These rules strengthen publish safety when analyst trust would otherwise be overstated.

## Phase A date-integrity clarification
- `unknown` publication dates are tracked explicitly and surfaced in aggregation and warnings.
- Timeline peak evaluation prioritizes known-day buckets whenever any known-day evidence exists.
- `FM-014-unknown-date-peak` remains a stop gate only when the peak candidates are entirely unknown-dated evidence.
