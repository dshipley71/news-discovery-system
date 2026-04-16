# Evaluation Framework

## 1) Purpose
Define how to evaluate system quality, operational readiness, and analyst usefulness before and during implementation.

## 2) Evaluation Axes
1. **Workflow completeness**
2. **Evidence traceability**
3. **Analytical quality**
4. **Operational resilience**
5. **Usability for non-technical analysts**
6. **No-code/minimal-code compliance**

## 3) KPI Set
## 3.1 Workflow KPIs
- End-to-end completion rate
- Stage failure rate by stage
- Mean run time by date-window size

## 3.2 Data and evidence KPIs
- Citation completeness (% claims with valid citation)
- Orphan claim count
- Duplicate collapse precision/recall (when labeled sets available)

## 3.3 Analytical KPIs
- Event cluster coherence score
- Trend detection precision on benchmark scenarios
- Geospatial resolution confidence distribution
- Contradiction detection coverage

## 3.4 User KPIs
- Analyst time-to-first-insight
- Task completion rate without admin help
- Number of manual clarifications needed per run

## 3.5 Operational KPIs
- Source outage tolerance (successful partial runs)
- Retry effectiveness
- Critic loop convergence rate within max iterations

## 4) Scoring Model
Use weighted evaluation score (0-100):
- Workflow completeness: 20
- Evidence traceability: 25
- Analytical quality: 25
- Usability: 15
- Resilience: 10
- Minimal-code compliance: 5

Recommended readiness thresholds:
- **>=85**: production-ready candidate
- **70-84**: pilot-ready with tracked gaps
- **<70**: design/implementation iteration required

## 5) Confidence Scoring Guidance
Confidence should be computed at multiple levels:
- Article-level
- Event-level
- Insight-level (trend/geospatial/narrative)
- Report claim-level

Confidence drivers:
- Source weight
- Corroboration count/diversity
- Data quality signals
- Contradiction intensity
- Extraction/model certainty

## 6) Evaluation Cadence
- Pre-implementation design review against this framework.
- Implementation sprint-end reviews.
- Weekly regression review once workflow is operational.

## 7) Failure Analysis Requirements
Any failed gate must produce:
- Root-cause summary
- Impacted stages/artifacts
- Proposed remediation
- Owner and due date

## 8) Assumptions
- Benchmark test profiles are maintained in UI Test Console.
- Sufficient telemetry is captured at every stage.

## 9) Open Decisions
1. Final KPI threshold tuning by business risk tolerance.
2. Ownership model for ongoing evaluation governance.
3. Whether to include external human adjudication panels for contradiction quality.
