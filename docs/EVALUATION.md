# Evaluation Framework (Reliability-Focused)

## 1) Purpose
Evaluate whether the analyst-facing Gradio workflow is reliable, inspectable, and safe against high-impact failure modes.

## 2) Acceptance Criteria Mapping
This framework enforces:
- all major failure modes covered,
- validation rules enforceable,
- UI issues visible,
- no silent failures.

## 3) Reliability Scorecard
Score each axis 0-5 and convert to weighted total (0-100).

| Axis | Weight | What “good” looks like |
|---|---:|---|
| Failure-mode coverage | 20 | All required failure modes have detection + prevention + UI + fallback. |
| Validation enforceability | 20 | Rules are machine-checkable and stage-gated (stop/warn). |
| Analyst visibility | 20 | Analyst can see status, thresholds, impacted artifacts, next actions. |
| Evidence traceability | 20 | Claims, clusters, maps, and spikes resolve to citations/artifacts. |
| Operational resilience | 10 | Partial outages handled safely without false confidence. |
| Determinism/reproducibility | 10 | Same input yields consistent stage outcomes. |

Readiness bands:
- **>= 85:** production-ready candidate
- **70-84:** pilot-ready with tracked gaps
- **< 70:** not ready

## 4) Required KPI Set

### 4.1 Failure-mode KPIs
- Duplicate inflation incidents detected before publish (%).
- Empty-ingestion runs correctly blocked (%).
- Schema drift detection precision (% correct drift alerts).
- Date-parse invalid rate and out-of-range suppression correctness.
- UI state desync detection rate.
- Geospatial ambiguity disclosure rate.
- Weak-cluster disclosure rate.
- Orphan-claim (missing citation) rate.
- Spike anomaly relabeling rate.

### 4.2 Analyst-visibility KPIs
- % WARN/FAIL events with remediation text.
- % WARN/FAIL events with direct drill-down link.
- Time-to-diagnose bad run from UI only.

### 4.3 Publish-safety KPIs
- % publish attempts blocked when citation coverage < 100%.
- % publish attempts blocked when critical rules fail.
- False-safe rate (runs incorrectly allowed despite critical issues).

## 5) Stage Evaluation Checklist (Analyst Must See)
For each stage, verify UI shows:
1. Stage input summary.
2. Pass/warn/fail outcome.
3. Measured metrics vs thresholds.
4. Affected artifact IDs.
5. Recommended next action.

If any item is missing, mark stage as **visibility non-compliant**.

## 6) Stop vs Warn Decision Audit
Every decision must store:
- rule ID,
- measured value,
- threshold,
- status (warn/fail),
- downstream actions blocked/unblocked,
- timestamp and run ID.

This is mandatory for post-run reliability audits.

## 7) Risk Summary (Current)
- Highest risk: silently misleading insights from duplicate inflation and spike artifacts.
- Second highest risk: publishable reports with incomplete citations.
- Third highest risk: Gradio UI state desync showing stale or incorrect run status.

## 8) Fix Summary (This Documentation Revision)
- Added explicit failure-mode matrix with detection/prevention/UI/fallback.
- Added enforceable thresholds and stop/warn criteria.
- Added analyst-visibility requirements and UI non-compliance criteria.
- Added publish-safety KPIs for no-silent-failure operation.

## 9) Remaining Gaps
1. Final threshold tuning from production telemetry.
2. Automated UI-state checksum instrumentation.
3. Benchmark datasets for geo ambiguity and clustering quality calibration.

## 10) Recommended Next Step
Implement a lightweight "Validation Event Log" artifact (per stage) surfaced directly in Gradio so analysts and reviewers can inspect every rule decision without leaving the UI.
