# Validation Rules (Enforceable)

## Purpose
Define enforceable pass/warn/fail rules for the in-repo analyst workflow.

## Status Semantics
- **PASS:** stage output is valid for downstream use.
- **WARN:** stage output is usable with confidence downgrade and UI warning.
- **FAIL:** stage output is blocked.
- **PARTIAL:** stage succeeded with degraded source coverage.

## Global Rules
- Every run must include immutable `run_id`, `started_at`, and stage outputs.
- Every article must preserve source attribution (`source`, `source_label`, `source_attribution`).
- Every ingestion run must expose source telemetry for analyst inspection.

## Ingestion Validation Rules
### Source execution transparency
- PASS: `sources_attempted` and per-source status list are present.
- FAIL: missing source-level execution metadata.

### Partial source failure handling
- PARTIAL: one or more sources failed/skipped but at least one succeeded.
- FAIL: all enabled sources failed/skipped.

### Optional source behavior (Twitter)
- PASS/PARTIAL: `TWITTER_BEARER_TOKEN` missing results in explicit `skipped` status and warning.
- FAIL: missing token causes full ingestion failure.

### Retry/fallback behavior
- PASS: Reddit adapter retries 429 and can fall back to RSS.
- WARN: JSON path failed but RSS fallback succeeded.
- FAIL: both Reddit JSON and RSS fallback failed.

### Duplicate inflation (early guard)
- PASS: ingestion duplicate ratio < 0.20.
- WARN: 0.20-0.39.
- FAIL: >= 0.40 when downstream confidence claims are requested.

## Normalization Validation Rules
### Canonical schema completeness
Required fields:
- `article_id`
- `title`
- `published_at`
- `source`

Thresholds:
- PASS >= 95%
- WARN 90-94%
- FAIL < 90%

### Source attribution completeness
- PASS: 100% of canonical rows include `source_attribution`.
- WARN: attribution present but missing optional subfields (`external_id`, `raw_source`).
- FAIL: attribution missing.

## Aggregation Validation Rules
### Date parsing integrity
- PASS: parsed date coverage >= 95%
- WARN: 90-94%
- FAIL: < 90%

## Analyst Visibility Requirements
Each stage must display:
- status,
- measured values,
- thresholds,
- warnings/errors,
- next action guidance.

## Implementation Constraint
Rules must remain executable with the current lightweight in-repo Python + Gradio architecture.
