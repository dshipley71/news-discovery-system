# Failure Modes and Reliability Safeguards

## 1) Purpose
Document common failure patterns for the current design-doc + n8n + Gradio vertical slice, define how they are detected, and specify required system behavior to avoid silent or misleading analyst outputs.

## 2) Scope
Applies to:
- UI-triggered runs from Run Builder / Gradio surface
- n8n ingestion + normalization + aggregation workflow slice
- downstream stage contracts defined in `docs/WORKFLOWS.md`

## 3) Core Failure Modes

## 3.1 Duplicate Article Inflation
**How it happens**
- Syndicated stories appear across sources with small headline edits.
- Same source item is retrieved multiple times across retries/windows.
- URL variants (tracking params, mirror domains) bypass naive dedupe.

**Detection signals**
- Duplicate ratio > configured threshold.
- Spike day where many records share near-identical text hash.
- High count of items with same root URL + same publication hour.

**Required behavior**
- Mark temporal outputs as **dedupe-risk** until dedupe pass completes.
- Block spike classification if dedupe uncertainty is high.
- Require lineage map for every merged duplicate.

## 3.2 Empty Ingestion Results
**How it happens**
- Topic too narrow.
- Source query mismatch.
- Source API schema/rate-limit change.

**Detection signals**
- `retrieved_count == 0` across all sources.
- Non-zero source attempts but all return empty payloads.

**Required behavior**
- Fail with explicit reason (no silent "success").
- UI must show: attempted sources, query terms, date window, and remediation actions.
- Offer guided rerun with widened date window or expanded source profile.

## 3.3 Partial Source Failures
**How it happens**
- One or more providers timeout, auth fail, or throttle.

**Detection signals**
- Source-level failures with at least one successful source.
- Source diversity drops below threshold.

**Required behavior**
- Continue run as **partial** when minimum viable coverage is met.
- Downgrade confidence for narrative/contradiction claims dependent on missing sources.
- Show source gap warning in run monitor and report limitations section.

## 3.4 Incorrect Date Parsing
**How it happens**
- Mixed timestamp formats/timezones.
- Locale-specific ambiguous dates.
- Null or malformed publication timestamps.

**Detection signals**
- Parse failure rate above threshold.
- Records outside requested date bounds after normalization.
- Timeline bucket has future dates or impossible regressions.

**Required behavior**
- Reject records with invalid timestamps from timeline computations.
- Keep excluded records in an "invalid-date" bucket for audit.
- Block publish if valid timestamp coverage falls below minimum threshold.

## 3.5 Inconsistent Schemas
**How it happens**
- Source payload changes field names/types.
- Optional fields unexpectedly absent.

**Detection signals**
- Required canonical fields missing.
- Type mismatch in normalized schema.

**Required behavior**
- Record-level validation flags are mandatory.
- Stop stage when required-field completeness drops below fail threshold.
- Display exact field-level error counts in Stage Detail.

## 3.6 Broken UI → Workflow Connections
**How it happens**
- UI sends wrong payload keys.
- Webhook URL stale/incorrect.
- UI accepts invalid date ranges not accepted by workflow.

**Detection signals**
- Run starts in UI but no orchestrator run ID returned.
- 4xx/5xx webhook response or timeout.
- UI status stuck in pending with no stage transitions.

**Required behavior**
- Fail fast at intake with actionable endpoint/contract error.
- Never show "run started" without confirmed run ID and timestamp.
- Persist request/response envelope for debugging.

## 3.7 Timeline Inaccuracies
**How it happens**
- Wrong bucket timezone.
- Event timestamps use retrieval time instead of publish time.
- Mixed daily/hourly bins without clear policy.

**Detection signals**
- Bucket totals not equal to counted valid records.
- Sudden day shifts around midnight UTC/local boundary.

**Required behavior**
- Use explicit canonical timezone (UTC) for aggregation.
- Store both publish timestamp and retrieval timestamp separately.
- Expose bucket policy and timezone in Timeline tooltip/legend.

## 3.8 Misleading Spikes from Batching/Syndication
**How it happens**
- Bulk publication at a single time from one wire source.
- Backfill jobs ingest older items together.

**Detection signals**
- Spike dominated by one source or one duplicate lineage family.
- Spike window has low source diversity.

**Required behavior**
- Classify as **distribution anomaly** unless corroborated by diverse sources.
- Mark spike confidence low when source concentration is high.
- Require analyst-visible explanation for each spike marker.

## 4) Severity Model
- **Critical (block publish):** empty ingestion, broken UI-workflow contract, orphan claims, severe timestamp corruption.
- **Major (allow partial with warning):** partial source outage above warning threshold, high duplicate uncertainty, low source diversity.
- **Minor (warn):** non-critical schema drift with successful normalization fallback.

## 5) Standard Remediation Paths
1. Retry failed source connectors with bounded backoff.
2. Rerun stage with stricter dedupe or adjusted temporal sensitivity.
3. Expand source profile when diversity threshold is not met.
4. Escalate to admin when contract/schema changes require connector update.

## 6) Assumptions
- UI can render stage-level warnings/errors and suggested remediations.
- Artifact lineage is available for drill-down.

## 7) Unresolved Questions
1. Final numeric values for warning/fail thresholds by environment.
2. Whether strict mode should block publish on any partial-source condition.
