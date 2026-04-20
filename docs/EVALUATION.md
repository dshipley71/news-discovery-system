# Evaluation Framework (Trustworthiness and Failure Visibility)

## 1) Purpose
Evaluate whether the Gradio + Colab analyst workflow is reliable under real-world failures and prevents silent trust erosion.

## 2) Readiness gates
A run is considered trustworthy only if:
1. all STOP rules pass,
2. warnings are visible in UI,
3. citation coverage is complete,
4. artifact contract is intact.

## 3) Scoring rubric (0-100)
| Axis | Weight | Passing interpretation |
|---|---:|---|
| Failure-mode coverage | 20 | All 11 required failure modes mapped to detection/prevention/UI/fallback/stop. |
| Validation enforceability | 20 | `stages.validation` is machine-checkable and deterministic. |
| Analyst visibility | 20 | WARN/STOP signals visible in run summary + payload panels. |
| Citation traceability | 20 | Citation coverage complete; weak citation share disclosed. |
| Operational resilience | 10 | Partial source failures and rate limiting degrade safely. |
| UI degradation resistance | 10 | Missing artifacts trigger explicit STOP, not silent fallback. |

Readiness bands:
- **>= 85:** production-candidate trust posture
- **70-84:** pilot with monitored risk
- **< 70:** not ready for analyst decision support

## 4) Required KPIs

### Trust-gate KPIs
- STOP-gate correctness rate (% critical cases correctly blocked).
- False-safe rate (% unsafe runs incorrectly publishable).
- Validation visibility rate (% warn/fail events visible in UI).

### Failure-mode KPIs
- Duplicate inflation detection rate.
- Empty-ingestion block rate.
- Schema drift detection precision.
- Partial-source-failure disclosure rate.
- Rate-limit disclosure rate.
- Weak geo disclosure rate.
- Weak cluster disclosure rate.
- Citation completeness block rate.
- Artifact-contract failure detection rate.
- Temporal anomaly detection rate (late coverage spikes vs event signal).
- Source-dominance disclosure rate for peak days.

### Analyst-operations KPIs
- Median time-to-diagnose from UI-only.
- % runs with clear remediation text per warning/fail event.

## 5) Event audit requirements
For each validation event persist:
- rule_id,
- measured values,
- threshold text,
- status,
- stop flag,
- timestamp.

This supports run-level trust audits and reviewer replay.

## 6) Current trust gaps identified pre-hardening
1. Warning logic existed but no first-class stop gates.
2. Empty ingestion and missing artifacts could degrade analyst trust if not explicitly blocked.
3. Rate-limit behavior existed technically but lacked explicit validation-level signaling.
4. Timeline spike reliability and citation sufficiency needed explicit trust thresholds.

## 7) Hardening outcomes expected
- No silent major failure paths.
- Deterministic warn/stop thresholds.
- Analyst-visible remediation for each major failure family.

## 8) Remaining weak spots
- Heuristic clustering and geospatial extraction still need future calibration against benchmark datasets.
- Source-level retry telemetry is currently strongest for Reddit path; extend to all adapters over time.
- Event lifecycle modeling is deterministic/heuristic and should be benchmarked against known event calendars.

## 9) Recommended next step
Add a dedicated Gradio “Validation Gate” panel rendering `stages.validation.events` as a sortable table (rule, status, measured, threshold, fallback) for faster analyst triage.
