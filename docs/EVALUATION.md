# Evaluation Framework

## 1) Purpose
Define how to evaluate system quality, operational readiness, and analyst usefulness before and during implementation, with explicit safeguards against silent failures and misleading analytics.

## 2) Evaluation Axes
1. **Workflow completeness**
2. **Evidence traceability**
3. **Analytical quality**
4. **Operational resilience**
5. **Usability for non-technical analysts**
6. **No-code/minimal-code compliance**
7. **Determinism and reproducibility**

## 3) KPI Set

## 3.1 Workflow KPIs
- End-to-end completion rate
- Stage failure rate by stage
- Mean run time by date-window size
- Contract error rate (UI request rejected by orchestrator)

## 3.2 Data and evidence KPIs
- Citation completeness (% claims with valid citation)
- Orphan claim count
- Duplicate collapse precision/recall (when labeled sets available)
- Timestamp validity rate

## 3.3 Analytical KPIs
- Event cluster cohesion score
- Trend detection precision on benchmark scenarios
- Spike integrity score (discounting syndication/batch artifacts)
- Geospatial resolution confidence distribution
- Contradiction detection coverage

## 3.4 User KPIs
- Analyst time-to-first-insight
- Task completion rate without admin help
- Number of manual clarifications needed per run
- Percentage of runs with fully actionable remediation hints

## 3.5 Operational KPIs
- Source outage tolerance (successful partial runs)
- Retry effectiveness
- Critic loop convergence rate within max iterations
- Partial-run transparency rate (partial runs correctly labeled)

## 3.6 Determinism KPIs
- Same-input rerun divergence rate
- Stage output schema stability across reruns
- Critical-threshold decision consistency (pass/warn/fail)

## 4) Scoring Model
Use weighted evaluation score (0-100):
- Workflow completeness: 18
- Evidence traceability: 24
- Analytical quality: 22
- Usability: 14
- Resilience: 10
- Determinism/reproducibility: 8
- Minimal-code compliance: 4

Recommended readiness thresholds:
- **>=85**: production-ready candidate
- **70-84**: pilot-ready with tracked gaps
- **<70**: design/implementation iteration required

## 5) Stage-Gate Reliability Checks
A run is only publishable when all are true:
1. No unresolved **Critical** failures.
2. Claim-to-citation coverage is 100%.
3. Timestamp validity and required schema completeness meet configured minimums.
4. Partial-source conditions (if any) are visibly disclosed in output limitations.
5. Timeline spikes are either corroborated or explicitly marked as low-confidence anomalies.

## 6) Critic Layer Decision Policy

## 6.1 When to re-run workflow (or stage)
Re-run is required when:
- Critical validation checks fail and a known remediation path exists.
- Output appears non-deterministic relative to same input profile.
- Timeline or contradiction outputs fail evidence-link integrity checks.

## 6.2 When to expand sources
Source expansion is required when:
- Cross-source coverage falls below contradiction/comparison minimum.
- Single-source dominance causes low-confidence spike or narrative conclusions.
- Repeated partial failures from the same subset of sources persist.

## 6.3 When to reject results
Reject (block publish) when:
- Orphan claims remain.
- Empty ingestion persists after allowed remediation attempts.
- Broken UI→workflow contract means run metadata is incomplete/untrusted.
- Critical date parsing/timeline integrity failures remain unresolved.

## 7) Observability Requirements (Analyst-Visible)

## 7.1 What must be visible at each stage
- Inputs consumed
- Outputs produced
- Validation rules executed with pass/warn/fail status
- Metrics vs thresholds
- Artifact IDs and lineage links
- Suggested next action

## 7.2 How to detect bad data quickly
UI must provide:
- Duplicate ratio and source concentration indicators
- Invalid timestamp count and out-of-range date count
- Source success/failure matrix
- Claim-to-citation coverage counter
- Unassigned article count for clustering stage

## 7.3 How outputs trace to inputs
- Every insight in timeline/map/narrative/report must resolve to artifact IDs.
- Every claim must resolve to citation nodes and source records.
- Every stage transition records actor, timestamp, and status decision.

## 8) Evaluation Cadence
- Pre-implementation design review against this framework.
- Sprint-end reliability review (must include one failure-injection scenario).
- Weekly regression review once workflow is operational.
- Monthly critic-policy calibration using false-positive/false-negative samples.

## 9) Failure Analysis Requirements
Any failed gate must produce:
- Root-cause summary
- Impacted stages/artifacts
- Proposed remediation
- Owner and due date
- Whether the issue is deterministic or intermittent

## 10) Assumptions
- Benchmark test profiles are maintained in UI Test Console.
- Sufficient telemetry is captured at every stage.
- Validation thresholds are centrally configurable by admin profile.

## 11) Open Decisions
1. Final numeric threshold tuning by business risk tolerance.
2. Ownership model for ongoing evaluation governance.
3. Whether strict mode should block publish for any partial-source run.
