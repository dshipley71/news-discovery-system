# Validation Rules (Enforceable)

## 1) Purpose
Define enforceable pass/warn/fail rules for Gradio-based analyst workflows so reliability issues are explicit, actionable, and auditable.

## 2) Status Semantics
- **PASS:** stage output is valid for downstream use.
- **WARN:** stage output is usable with confidence downgrade and required UI warning.
- **FAIL:** stage output blocked; downstream publish path blocked.
- **PARTIAL:** stage completed with degraded coverage, must carry limitation labels.

## 3) Global Enforceable Rules
- Every run must have immutable `run_id`, `started_at`, and stage status timeline.
- Publish mode requires 100% claim-to-citation linkage.
- Every insight shown in UI (timeline spike, map hotspot, cluster claim) must link to evidence artifacts.
- Any WARN/FAIL must include remediation text and a drill-down path.

## 4) Numeric Default Thresholds (Configurable)
- Required canonical completeness (`source`, `published_at`, `title_or_text_ref`):
  - PASS >= 95%
  - WARN 90-94%
  - FAIL < 90%
- Valid parsed publication dates:
  - PASS >= 95%
  - WARN 90-94%
  - FAIL < 90%
- Duplicate ratio (run level):
  - PASS < 0.20
  - WARN 0.20-0.39
  - FAIL >= 0.40
- Geospatial low-confidence share:
  - PASS < 0.20
  - WARN 0.20-0.39
  - FAIL >= 0.40 (for geo-claim-enabled publish)
- Weak clusters share:
  - PASS < 0.25
  - WARN 0.25-0.49
  - FAIL >= 0.50 (for publish-grade clustering)

## 5) Failure-Mode Rules (Required)

### 5.1 Duplicate Article Inflation
- **Detect:** duplicate ratio + duplicate family concentration by bin/cluster.
- **Prevent:** dedupe before clustering and timeline generation.
- **UI signal:** `WARN_DUPLICATES` or `FAIL_DUPLICATES` with impacted artifacts.
- **Fallback:** anomaly-only spike labels; block publish-grade event assertions on affected bins.

### 5.2 Empty Ingestion
- **Detect:** `retrieved_count == 0` after retrieval/normalization.
- **Prevent:** source health + query guardrails at intake.
- **UI signal:** blocking `NO_DATA` state.
- **Fallback:** guided rerun presets only; no downstream stage execution.

### 5.3 Schema Drift
- **Detect:** field/type drift and completeness drop.
- **Prevent:** canonical schema contract validation at normalization boundary.
- **UI signal:** `SCHEMA_DRIFT` field-level diff summary.
- **Fallback:** quarantine invalid rows; fail stage if completeness < fail threshold.

### 5.4 Incorrect Date Parsing
- **Detect:** invalid parse count, out-of-range count, impossible future buckets.
- **Prevent:** strict timezone-aware parser + accepted format policy.
- **UI signal:** `DATE_PARSE_ISSUE` counter and record list.
- **Fallback:** exclude invalid-date records from timeline; fail publish if coverage below threshold.

### 5.5 Broken UI State
- **Detect:** UI run state checksum mismatch; heartbeat timeout; callback result bound to wrong run.
- **Prevent:** backend-authoritative state sync and run-token checks.
- **UI signal:** `STATE_DESYNC` and disabled finalize/export controls.
- **Fallback:** force resync/rebind; fail safe if mismatch persists.

### 5.6 Incorrect Geospatial Inference
- **Detect:** ambiguity/conflict checks; low-confidence geocoding rates.
- **Prevent:** require confidence + evidence span + extraction method on every location.
- **UI signal:** `LOW_GEO_CONFIDENCE` map and panel warnings.
- **Fallback:** suppress strong geo conclusions; retain uncertain items as review artifacts.

### 5.7 Weak Clustering
- **Detect:** low cohesion, low unique-evidence count, high source concentration.
- **Prevent:** enforce minimum cluster evidence and confidence thresholds.
- **UI signal:** `WEAK_CLUSTER` flags in cluster table and details.
- **Fallback:** exploratory-only clusters allowed; publish claims blocked for weak clusters.

### 5.8 Missing Citations
- **Detect:** orphan claim count > 0 or required citation fields missing.
- **Prevent:** citation-link check at evidence packaging and report composition.
- **UI signal:** `CITATION_GAP` blocking indicator.
- **Fallback:** review-only mode; disable publish/export.

### 5.9 Misleading Timeline Spikes
- **Detect:** spike dominated by one source, duplicate family, or backfill artifact.
- **Prevent:** corroboration rule (minimum source diversity + duplicate-adjusted volume).
- **UI signal:** `SPIKE_ANOMALY` label with confidence score.
- **Fallback:** downgrade to anomaly marker; narrative claims require corroboration.

## 6) Stage Stop/Warn Matrix
- Intake: fail on invalid input/date range.
- Retrieval: fail on empty ingestion; partial on source subset failures.
- Normalization: fail on schema completeness below threshold.
- Geospatial: warn/fail on low-confidence or traceability gaps depending on severity.
- Clustering: warn for weak clusters, fail for missing cluster schema/attribution.
- Timeline: warn/fail on date quality and anomaly conditions.
- Evidence/report: fail on citation gaps and orphan claims.

## 7) Analyst Visibility Requirements
At each stage, analyst must see:
- status (PASS/WARN/FAIL/PARTIAL),
- measured value and threshold,
- affected artifacts,
- exact blocked actions,
- next best action.

## 8) Implementation Constraint
Rules must be executable with current lightweight architecture (Gradio + orchestrated workflow + validation contracts), without introducing heavy frameworks.
