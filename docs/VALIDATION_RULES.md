# Validation Rules (In-Repo Multi-Source Workflow)

## Purpose
Define enforceable pass/warn/fail rules for ingestion, normalization, and aggregation in the in-repo analyst workflow.

## Status semantics
- **PASS:** stage output is valid for downstream use.
- **WARN:** stage output remains usable with reduced confidence.
- **FAIL:** stage output is blocked.
- **PARTIAL:** stage succeeded with degraded source coverage.

## Global rules
- Every run must include immutable `run_id` and `started_at`.
- Every article must preserve source attribution (`source`, `source_label`, `source_attribution`).
- Every ingestion run must expose source telemetry for analyst inspection.

## Ingestion rules
### Source execution transparency
- PASS: `sources_attempted` exists and `source_runs` includes per-source status/count/warnings/error/metadata.
- FAIL: missing source execution metadata.

### Multi-source operation
- PASS: more than one enabled source can be attempted in the same run.
- FAIL: ingestion collapses to single-source behavior while multiple sources are enabled.

### Partial source failure handling
- PARTIAL: one or more sources failed/skipped and at least one source succeeded.
- FAIL: all enabled sources failed/skipped.

### Optional source behavior (X/Twitter)
- PASS/PARTIAL: missing `TWITTER_BEARER_TOKEN` yields explicit `skipped` status + warning.
- FAIL: missing token causes entire ingestion to fail.

### Retry/fallback behavior
- PASS: Reddit adapter retries 429 responses and can fall back to RSS.
- WARN: JSON path failed and RSS fallback recovered.
- FAIL: both JSON and RSS paths failed for Reddit.

### Duplicate inflation guard
- PASS: ingestion duplicate ratio < 0.20.
- WARN: 0.20-0.39.
- FAIL: >= 0.40 when high-confidence downstream output is requested.

## Normalization rules
### Canonical schema completeness
Required fields:
- `article_id`
- `title`
- `published_at`
- `source`

Thresholds:
- PASS: >= 95%
- WARN: 90-94%
- FAIL: < 90%

### Source attribution completeness
- PASS: 100% of canonical records include `source_attribution`.
- WARN: attribution present with missing optional subfields.
- FAIL: attribution missing.

## Aggregation rules
### Date parsing integrity
- PASS: parsed-date coverage >= 95%
- WARN: 90-94%
- FAIL: < 90%

## Analyst visibility requirements
UI stage views must show:
- status,
- measured values,
- thresholds,
- warnings/errors,
- recommended next action.

## Implementation constraint
Validation must remain executable with the current lightweight in-repo Python + Gradio architecture.
