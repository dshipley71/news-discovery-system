# UI-Executable Test Plan (Failure-Hardening)

## 1) Purpose
Validate reliability of the Gradio analyst workflow against required failure modes, with clear warn/stop behavior and no silent failures.

## 2) Test Execution Principle
All reliability tests must be executable and reviewable from the UI (or UI test console route), not dependent on analyst CLI usage.

## 3) Must-Test Failure Modes
- duplicate article inflation
- empty ingestion
- schema drift
- incorrect date parsing
- broken UI state
- incorrect geospatial inference
- weak clustering
- missing citations
- misleading timeline spikes

## 4) Stage Visibility Assertions (Required for Every Test)
For each stage result, assert UI displays:
1. status badge (PASS/WARN/FAIL/PARTIAL),
2. metric value and threshold,
3. impacted artifacts,
4. blocked actions,
5. remediation guidance.

Any missing element is a test failure.

## 5) Core Failure Injection Tests

### FT-1 Duplicate Inflation
- Inject near-duplicate syndicated set.
- Expected:
  - duplicate ratio warning/fail shown,
  - timeline/cluster counts use unique article IDs,
  - spike claims downgraded when duplicate-driven.

### FT-2 Empty Ingestion
- Use topic/date profile returning no articles.
- Expected:
  - blocking `NO_DATA` state,
  - source attempts visible,
  - downstream stages not executed,
  - guided rerun options offered.

### FT-3 Schema Drift
- Inject payload with renamed/missing canonical fields.
- Expected:
  - `SCHEMA_DRIFT` diagnostics with field diffs,
  - invalid rows quarantined,
  - fail if completeness below threshold.

### FT-4 Date Parsing Failure
- Inject mixed invalid/ambiguous date formats and timezone offsets.
- Expected:
  - invalid-date counts shown,
  - invalid rows excluded from timeline,
  - publish block when valid coverage below threshold.

### FT-5 Broken UI State
- Simulate stale run ID and interrupted callback state.
- Expected:
  - `STATE_DESYNC` warning,
  - finalize/export controls disabled,
  - resync/rebind flow available.

### FT-6 Incorrect Geospatial Inference
- Inject ambiguous place names with conflicting country context.
- Expected:
  - ambiguity and low-confidence markers shown,
  - evidence spans visible,
  - strong geo conclusions suppressed.

### FT-7 Weak Clustering
- Inject sparse/noisy thematic overlap.
- Expected:
  - weak-cluster flags visible,
  - exploratory view allowed,
  - publish-grade cluster claims blocked.

### FT-8 Missing Citations
- Inject report claims without citation links.
- Expected:
  - `CITATION_GAP` block,
  - orphan claims listed,
  - publish/export disabled.

### FT-9 Misleading Timeline Spikes
- Inject batch backfill or single-source syndication burst.
- Expected:
  - `SPIKE_ANOMALY` label,
  - confidence reduced,
  - narrative spike claim blocked unless corroborated.

## 6) End-to-End Reliability Acceptance Tests

### AT-R1 Healthy Run
- Expected: no critical failures, all outputs present, full citation coverage.

### AT-R2 Partial Outage Run
- One source down, others healthy.
- Expected: partial label + limitations disclosure; no false "all good" signal.

### AT-R3 High-Risk Data Run
- Combined duplicates + weak clusters + date noise.
- Expected: warnings surfaced across stages; publish blocked if critical threshold crossed.

### AT-R4 Publish Gate Enforcement
- Attempt export with citation gap and unresolved critical issue.
- Expected: hard block with explicit reason and remediation.

## 7) Stop Conditions
Test run is auto-failed if either condition occurs:
- any critical failure is not surfaced in UI,
- any publish/export action succeeds while critical rules are unresolved.

## 8) Evidence to Capture per Test
- test run ID,
- input profile,
- stage-by-stage status timeline,
- screenshot or UI artifact references,
- observed vs expected assertions,
- operator and timestamp.

## 9) Remaining Gaps
1. Automated scenario generator for edge-case data profiles.
2. Baseline gold datasets for cluster and geospatial quality scoring.
3. Long-run soak tests for Gradio state consistency under repeated reruns.

## 10) Recommended Next Step
Add a dedicated "Failure Drill" panel in Gradio to launch FT-1..FT-9 profiles and export a structured validation report for each run.
