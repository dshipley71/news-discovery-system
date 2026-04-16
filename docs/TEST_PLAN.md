# UI-Executable Test Plan

## 1) Test Philosophy
Testing must mirror analyst-visible workflow stages and run entirely from the UI. No CLI dependence for analyst validation.

## 2) Test Layers
1. **Stage validation tests** (per stage contract)
2. **Workflow integration tests** (end-to-end run)
3. **Quality behavior tests** (sparse/noisy/contradictory/spike cases)
4. **Traceability tests** (claim-to-citation lineage)
5. **Resilience tests** (partial source outages)

## 3) UI Test Console Requirements
- Launch tests by stage or full workflow.
- Select test profiles (normal load, sparse, noisy, contradictory, spike).
- Display expected vs actual assertions.
- Provide rerun with same inputs for reproducibility.

## 4) Stage-by-Stage Test Cases
## T0 Intake
- Input topic empty -> expect validation block.
- Date window outside 1-30 -> expect validation block.
- Valid input -> expect run manifest creation.

## T1 Source Discovery
- Mixed key/non-key sources configured -> expect source plan includes both classes.
- Key source unavailable -> expect fallback and warning, not full failure.

## T2 Retrieval
- Partial source timeout -> expect partial-success status and source-level errors logged.
- All sources fail -> expect run failure with remediation guidance.

## T3 Normalization
- Incomplete raw records -> expect flagging and schema completeness metrics.
- Valid records -> expect canonical schema compliance.

## T4 Geospatial Extraction
- Explicit location mention in article -> expect populated city/region/country and coordinates.
- Inferred-only location -> expect extraction_method=inferred with visible confidence.
- Ambiguous place name -> expect ambiguity flag and notes.
- Missing article linkage -> expect stage failure.

## T5 Geospatial Aggregation
- Multiple mentions of same location in one article -> unique article count increments once.
- Nearby locations within configured radius -> grouped to shared location group.
- Article with multiple distinct locations -> appears in multiple groups without duplicate inflation.

## T6 Event Clustering
- Thematically linked articles -> expect same event group with membership scores.
- Unrelated articles -> expect separate clusters or unassigned bucket.
- Cluster detail includes linked location group IDs.

## T7 Temporal Analytics
- Spike-like profile -> expect spike marker on timeline.
- Sustained elevated profile -> expect sustained trend tag.

## T8 Narrative Comparison
- Conflicting source claims -> expect contradiction labeling with citations.
- Consensus claims -> expect agreement labeling.

## T9 Evidence Packaging
- Every summary claim -> must map to citation(s).
- Missing citation mapping -> expect blocking failure.
- Geospatial claim -> must include location or location-group artifact link.

## T10 Report Composition
- Missing required section -> expect publication block.
- Complete sections -> expect export enabled.

## T11 Critic Loop
- Initial failed quality gate -> expect refinement iteration.
- Reaching max iterations -> expect stop with unresolved issue summary.

## 5) End-to-End Acceptance Tests
### AT-1 Normal run
- Valid topic, healthy source mix.
- Expected: completed status, all mandatory outputs available.

### AT-2 Sparse coverage run
- Narrow topic/window likely to produce few items.
- Expected: low-confidence labels and limitation notes.

### AT-3 Contradiction-heavy run
- Topic with disputed reporting.
- Expected: contradiction matrix + unresolved claim handling.

### AT-4 Breaking-news run
- Active developing topic.
- Expected: spike detection + developing-story warning.

### AT-5 Geospatial inspection run
- Topic with multi-location reporting.
- Expected: map markers render; drill-down path works location → cluster → articles; ambiguity visible.

## 6) Quality Gates
A run can be marked production-ready only if:
- Mandatory outputs exist (events, timeline, map, narrative, report).
- Citation completeness threshold is met.
- Critical validation failures are zero.
- Critic loop either passes gates or exits at max iterations with explicit blockers.
- Geospatial counts are deduplicated and traceable to article IDs.

## 7) Evidence of Test Completion
For each test execution, store:
- Test run ID
- Input profile
- Assertion results
- Artifact links
- Timestamp and operator

## 8) Assumptions
- UI Test Console is available as a first-class route.
- Test profiles can be injected/configured without code by analysts or admins.

## 9) Open Decisions
1. Production pass/fail thresholds for confidence and coverage.
2. Frequency and ownership of regression test runs.
3. Whether export validation includes downstream system compatibility checks.
