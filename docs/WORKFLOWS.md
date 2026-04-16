# Workflow Operating Manual

## 1) Execution Model
This system supports two architecture patterns:

## A) Multi-agent (recommended)
A no-code orchestrator coordinates specialized agents with explicit contracts.

Agents:
1. Intake Agent
2. Source Discovery Agent
3. Retrieval Agent
4. Normalization Agent
5. Deduplication Agent
6. Event Clustering Agent
7. Temporal Analytics Agent
8. Geospatial Agent
9. Narrative Comparison Agent
10. Evidence & Citation Agent
11. Report Composer Agent
12. Critic Agent

## B) Single-orchestrator (simpler alternative)
One orchestrator executes the same stages as internal modules with identical stage I/O contracts.

---

## 2) Stage Contracts (applies to both architectures)
## Stage 0: Intake
- Inputs: topic, date-window-length (1-30)
- Outputs: run manifest, normalized query spec
- Validation rules:
  - Topic non-empty
  - End date == current date
  - Window within 1-30 days
- Stop conditions: invalid input => fail-fast with UI guidance

## Stage 1: Source Discovery
- Inputs: query spec, source catalog, credential status
- Outputs: source plan (source IDs, query params, fallback order)
- Validation rules:
  - At least one active source reachable
  - Mixed key/non-key coverage allowed
- Stop conditions:
  - If zero sources available => fail run
  - If partial availability => continue with warning

## Stage 2: Retrieval
- Inputs: source plan
- Outputs: raw item set, retrieval logs, source errors
- Validation rules:
  - Timestamp and source identity present
  - Response metadata captured
- Stop conditions:
  - Catastrophic retrieval failure threshold exceeded => stop
  - Otherwise continue as partial success

## Stage 3: Normalization
- Inputs: raw item set
- Outputs: canonical article records
- Validation rules:
  - Required schema fields populated or flagged
  - Encoding/timezone normalization complete
- Stop conditions: schema failure rate above threshold => halt for review

## Stage 4: Deduplication
- Inputs: canonical records
- Outputs: canonical unique set + duplicate lineage map
- Validation rules:
  - Duplicate rationale stored (text similarity, URL, metadata)
  - No orphan duplicate pointers
- Stop conditions: if dedupe confidence collapse detected => warning + continue

## Stage 5: Event Clustering
- Inputs: deduped records
- Outputs: event groups, membership scores, event summaries
- Validation rules:
  - Every article either assigned or explicitly unassigned
  - Cluster cohesion above minimum threshold
- Stop conditions: insufficient cohesion => rerun with adjusted settings once

## Stage 6: Temporal Analytics
- Inputs: event groups + publish timestamps
- Outputs: timeline series, peak/spike/trend detections
- Validation rules:
  - Bucket integrity check
  - Detection thresholds logged
- Stop conditions: low volume => mark insights as low confidence, continue

## Stage 7: Geospatial Extraction
- Inputs: clustered articles
- Outputs: geospatial entities, resolved coordinates/regions, uncertainty flags
- Validation rules:
  - Entity-to-evidence links present
  - Ambiguous place names flagged
- Stop conditions: geocoding provider outage => continue without map confidence overlays

## Stage 8: Narrative Comparison
- Inputs: event groups, source metadata, extracted claims
- Outputs: narrative matrix (agreement/contradiction/unique)
- Validation rules:
  - Claims mapped to supporting evidence
  - Contradictions cite at least two independent records
- Stop conditions: insufficient cross-source coverage => downgrade output confidence

## Stage 9: Evidence & Citation Packaging
- Inputs: all prior stage outputs
- Outputs: claim-evidence graph, citation appendix, evidence bundle index
- Validation rules:
  - Every report claim has >=1 citation
  - Citation metadata completeness check
- Stop conditions: unmapped claims exist => block report publication

## Stage 10: Report Composition
- Inputs: packaged evidence and analytical summaries
- Outputs: final report draft, export artifacts
- Validation rules:
  - Required report sections present
  - Uncertainty and limitations section populated
- Stop conditions: missing mandatory section => block finalization

## Stage 11: Critic Loop (bounded)
- Inputs: report draft + validation findings
- Outputs: refined report revisions, critique log
- Process:
  - Max refinement count default = 2
  - Stop early if quality target met
- Validation rules:
  - Revisions cannot remove citation coverage
  - Confidence regressions must be explained
- Stop conditions:
  - Max iterations reached
  - Or all critical checks pass

---

## 3) Handoffs and Data Contracts
Every handoff must include:
- Run ID
- Stage ID
- Input artifact IDs
- Output artifact IDs
- Validation result set
- Confidence summary
- Timestamp and actor (agent/module)

## 4) Confidence and Source Weighting
## Confidence dimensions
- Source reliability
- Cross-source corroboration
- Temporal consistency
- Extraction certainty
- Contradiction pressure

## Source weighting rules
- Admin-configurable source tiers.
- Weight contributes to claim confidence, not claim truth guarantee.
- Contradictory high-weight sources increase uncertainty flags.

## 5) Special Condition Handling
## Sparse coverage
- Trigger: low article count below threshold.
- Behavior: continue with low-confidence labels and explicit caution text.

## Noisy coverage
- Trigger: high duplicate/near-duplicate ratio, weak signal.
- Behavior: apply stricter dedupe and clustering thresholds; expose noise metrics.

## Contradictory coverage
- Trigger: competing claims for same event attributes.
- Behavior: split claim sets, label unresolved contradictions, avoid forced synthesis.

## Breaking-news spikes
- Trigger: abrupt short-interval count surge.
- Behavior: mark as developing; schedule auto-refresh run suggestion.

## 6) UI-First Operating Procedure
1. Analyst opens Run Builder.
2. Enters topic + date-window length.
3. Starts run.
4. Monitors stage progression in Run Monitor.
5. Reviews artifacts in Stage Detail panels.
6. Inspects timeline/map/narrative tabs.
7. Reviews critic loop deltas.
8. Exports final report + evidence bundle.

## 7) Minimal-Code Boundary
- Preferred: implement these stages with no-code workflow nodes and connectors.
- Allowed custom code only for:
  - Unavailable connector adapters
  - Specialized dedupe/clustering primitives not supported by platform
  - Evidence graph serialization utility
All custom code must remain small, isolated, and documented before implementation.

## 8) Assumptions
- Source catalog and credential vault are available to orchestration layer.
- Chosen no-code platform can persist stage artifacts and metadata.

## 9) Open Decisions
1. Exact clustering strategy and thresholds.
2. Temporal spike/trend parameter defaults.
3. Geospatial disambiguation fallback hierarchy.
4. Critic quality gates and pass criteria tuning.
