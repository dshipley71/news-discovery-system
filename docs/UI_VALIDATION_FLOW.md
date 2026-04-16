# UI Validation Flow

## 1) Purpose
Define exactly how a non-technical analyst validates each workflow stage from the UI, including what to inspect, what to confirm, and what actions to take when checks fail.

## 2) Validation Operating Model
- Validation is stage-scoped and always available in Stage Detail.
- Each stage shows: inputs consumed, outputs produced, pass/fail checks, warnings, artifact links.
- Analyst can trigger bounded rerun where policy allows.
- Final publication depends on cumulative stage validation and citation completeness.

## 3) Stage-by-Stage Analyst Validation

## Stage 0: Intake
**What analyst sees**
- Topic/date-window summary and run manifest preview.

**What analyst verifies**
1. Topic is correct and specific enough.
2. Date window reflects intended analysis period.

**If check fails**
- Edit inputs and relaunch run.

---

## Stage 1: Source Discovery
**What analyst sees**
- Planned sources list with source class (key/non-key), priority, fallback order.

**What analyst verifies**
1. Source diversity is acceptable (not single-source dependent).
2. Critical sources are available or fallback exists.

**If check fails**
- Adjust source profile in advanced settings and rerun discovery.

---

## Stage 2: Retrieval
**What analyst sees**
- Source ingestion table: attempted, succeeded, failed, timeout/retry count.
- Retrieval logs and warnings.

**What analyst verifies**
1. At least minimum viable source count succeeded.
2. Failure reasons are explicit and non-silent.
3. Retrieved item volume is plausible for topic/date range.

**If check fails**
- Trigger stage rerun.
- If repeated failure, switch source mix profile and rerun.

---

## Stage 3: Normalization
**What analyst sees**
- Canonical field completeness metrics.
- Flagged records panel for missing/invalid fields.

**What analyst verifies**
1. Required fields (source, timestamp, content reference) are populated or flagged.
2. Time and encoding normalization completed.

**If check fails**
- Review flagged records and rerun normalization after profile adjustment.

---

## Stage 4: Deduplication
**What analyst sees**
- Dedupe decisions log (canonical ID, merged IDs, rationale).
- Duplicate ratio metric.

**What analyst verifies**
1. Near-identical stories are collapsed.
2. Distinct stories are not over-merged.
3. Lineage is preserved for all collapsed items.

**If check fails**
- Switch strictness profile and rerun dedupe once.

---

## Stage 5: Event Clustering
**What analyst sees**
- Events table with membership counts/confidence.
- Unassigned article bucket (if any).

**What analyst verifies**
1. Major story threads are grouped sensibly.
2. Unassigned volume is acceptable.
3. Cluster confidence is not systematically low.

**If check fails**
- Trigger allowed auto-adjusted rerun for clustering.

---

## Stage 6: Temporal Analytics
**What analyst sees**
- Timeline with peaks/spikes/trend overlays.
- Marker details including threshold and linked evidence IDs.

**What analyst verifies**
1. Marker positions match visible count changes.
2. No marker appears without supporting article evidence.
3. Low-volume cases are labeled low confidence.

**If check fails**
- Adjust trend sensitivity profile and rerun temporal stage.

---

## Stage 7: Geospatial
**What analyst sees**
- Map with confidence styling.
- Ambiguous-location list and resolution status.

**What analyst verifies**
1. Key locations are mapped and contextually sensible.
2. Ambiguous places are flagged, not silently resolved.
3. Marker drill-down links to claims and citations.

**If check fails**
- Rerun geospatial stage or accept degraded mode if provider outage.

---

## Stage 8: Narrative Comparison
**What analyst sees**
- Agreement/contradiction/unique claim matrix.
- Evidence links per narrative claim.

**What analyst verifies**
1. Contradictions are supported by multi-source evidence.
2. Consensus labels are not assigned without corroboration.

**If check fails**
- Rerun narrative comparison with stricter contradiction policy.

---

## Stage 9: Evidence Packaging
**What analyst sees**
- Claim-to-citation coverage summary.
- Orphan claim list (if any).

**What analyst verifies**
1. Every report-bound claim maps to citation entries.
2. Citation metadata completeness is high enough for publish gate.

**If check fails**
- Publication blocked; rerun affected upstream stage(s) and repack evidence.

---

## Stage 10: Report Composition
**What analyst sees**
- Full report preview with expandable sections and inline citations.

**What analyst verifies**
1. Required sections are present.
2. Findings match inspected artifacts.
3. Uncertainty notes are present where needed.

**If check fails**
- Return to relevant stage and rerun before finalize.

---

## Stage 11: Critic Loop
**What analyst sees**
- Iteration history, diffs, unresolved issue list, max-iteration counter.

**What analyst verifies**
1. Refinements improve clarity/quality without removing evidence links.
2. Final status aligns with strict/permissive policy.

**If check fails**
- Stop publish and escalate unresolved blockers.

## 4) UI Controls Required for Validation
- Stage Detail: inputs/outputs/checks/artifacts.
- Validation card: pass/fail/warn with remediation suggestions.
- Rerun button: stage-scoped and policy-bounded.
- Evidence drill-down: from every chart/table/report claim.
- Audit timeline: immutable actions with timestamps and actor.

## 5) Validation Status Model
- **Pass:** stage output meets required checks.
- **Warn:** stage output usable with explicit caveats.
- **Fail:** stage output blocked; downstream publish denied until remediated.
- **Partial:** stage executed with degraded branch and confidence downgrade.

## 6) End-to-End Analyst Sign-Off Flow
1. Confirm intake correctness.
2. Confirm retrieval breadth and partial-failure handling.
3. Confirm normalization/dedupe quality.
4. Confirm event/timeline/map/narrative interpretability.
5. Confirm citation completeness.
6. Confirm report quality and critic-loop outcome.
7. Export report and evidence bundle.

## 7) Assumptions
- Analyst has role permission to rerun allowed stages.
- UI supports side-by-side current vs prior run/stage comparison.

## 8) Unresolved Decisions
1. Which stages allow analyst rerun vs admin-only rerun.
2. Whether manual approval gates are enabled by default.
3. Final thresholds for pass/warn/fail by stage.

## 9) Risks/Blockers
- Overly technical validation labels may reduce analyst usability.
- Missing remediation hints can make fail states non-actionable.
- Weak evidence drill-down UX may break trust in generated outputs.
