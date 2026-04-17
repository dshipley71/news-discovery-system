# Test Plan (Failure Hardening + Trust Gates)

## 1) Purpose
Validate that the in-repo Gradio + Colab workflow handles analyst-critical failure modes with explicit warning/stop behavior and no silent degradation.

## 2) Scope
- Backend workflow and validation gates: `src/news_app/workflow.py`
- Analyst-facing behavior surfaced through workflow outputs consumed by Gradio.
- Automated checks: `tests/test_workflow.py`

## 3) Pre-hardening trust gaps observed
1. Warning generation existed, but stop-level publish gates were not first-class.
2. Some high-impact conditions (empty ingestion, artifact contract breakage) needed explicit fail-state enforcement.
3. Rate-limit retry behavior existed but lacked dedicated trust-gate eventing.

## 4) Test matrix for required failure modes

| Failure mode | Automated test coverage | Expected gate behavior |
|---|---|---|
| Duplicate article inflation | Existing + warning tests | WARN at elevated duplicates; STOP at severe ratio |
| Source-specific failure | Existing ingestion failure tests | WARN partial failure; STOP if all fail |
| Source status classification (failed/skipped/empty) | `test_source_failure_reporting_distinguishes_skipped_and_empty` | Distinct ingestion status lists remain inspectable |
| Aggregation consistency | `test_aggregation_consistency_matches_normalized_total` | Timeline total equals normalized valid count |
| Multi-day date bucketing | `test_parse_date_buckets_multi_day_for_gdelt_format` | GDELT/compact timestamps resolve to correct day buckets |
| Rate limiting/backoff | `test_reddit_retry_and_rss_fallback`, validation warning test | WARN with retry metadata |
| Empty ingestion | `test_validation_stop_on_empty_ingestion` | STOP |
| Schema drift across sources | Existing schema consistency + normalization counts | WARN/STOP by invalid ratio |
| Weak source diversity | Existing warning generation test | WARN |
| Misleading timeline spikes | Validation logic checks (rule FM-007) | WARN |
| Low-confidence geospatial inference | Existing warning generation test + validation FM-008 | WARN |
| Weak/duplicate-heavy clusters | Existing warning generation test + validation FM-009 | WARN |
| Cluster fragmentation sanity | `test_cluster_distribution_groups_related_articles` | Related headlines merge into non-singleton clusters |
| Geospatial artifact population | `test_geospatial_population_multiple_markers` | Multi-location evidence yields multiple map markers |
| Missing/weak citations | Existing citation artifact tests + validation FM-010 | WARN/STOP |
| Silent UI degradation on missing artifacts | `test_validation_detects_missing_artifact_contract` | STOP |
| Timeline mismatch trust gate | Validation logic checks (rule FM-012) | STOP |

## 5) Regression commands
1. `pytest tests/test_workflow.py`
2. Optional full suite: `pytest`

## 6) Analyst-visible verification in Colab/Gradio
For one run with induced warnings:
1. Confirm warning summary includes machine-generated warning codes.
2. Confirm `stages.validation` payload is present.
3. Confirm STOP gates set `can_publish=false` and `stop_recommended=true` for severe scenarios.
4. Confirm source failure details remain visible per source.

## 7) Exit criteria
Accepted when:
- key warning/stop rules execute deterministically,
- major failure families are represented in automated tests,
- no silent critical failure path remains undocumented or untested,
- validation behavior is inspectable from workflow output payloads.

## 8) Added regression coverage in this pass
- Multi-day timeline integrity with explicit unknown-date bucket handling.
- Reddit fallback behavior when primary JSON returns an empty payload.
- GDELT adapter transparent failure telemetry vs successful parse path.
- Validation stop gate for required GDELT failure.
- Validation stop gate for unknown-date peak bucket.
- Geospatial location-type separation (`event_location`/`mentioned_location`/`source_location`) and event-only mapping behavior.
