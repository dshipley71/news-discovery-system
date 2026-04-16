# Validation Rules by Stage

## 1) Purpose
Define deterministic pass/warn/fail rules, minimum data thresholds, and fallback behavior for each stage so analysts receive consistent, auditable outcomes.

## 2) Validation Status Semantics
- **Pass:** output is valid for downstream use without caveat.
- **Warn:** output usable only with explicit confidence downgrade and UI warning.
- **Fail:** stage output blocked; downstream publish blocked unless rerun succeeds.
- **Partial:** stage completed with degraded branch; downstream allowed only if minimum thresholds are still met.

## 3) Cross-Stage Global Thresholds
These defaults are starting values and must be environment-configurable.

- Minimum successful sources per run: **>= 1** (warn if only 1, fail if 0).
- Required canonical field completeness (`source`, `published_at`, `title_or_text_ref`): **>= 95% pass**, **90-94% warn**, **<90% fail**.
- Valid publish timestamp coverage: **>= 95% pass**, **90-94% warn**, **<90% fail**.
- Claim-to-citation coverage for publish: **100% required**.
- Duplicate lineage completeness for merged records: **100% required**.

## 4) Stage Rules

## Stage 0: Intake
**Rules**
- Topic non-empty.
- Date window valid and within allowed bounds.
- End date must not be in the future.

**Behavior**
- Fail fast on contract/input error.
- Show exact invalid fields and correction hint.

## Stage 1: Source Discovery
**Rules**
- At least one source planned and reachable.
- Source plan contains fallback order and credential mode.

**Behavior**
- Fail if no reachable sources.
- Warn if source diversity below configured minimum.

## Stage 2: Retrieval
**Rules**
- Response metadata logged for each attempted source.
- Explicit error recorded for each failed source.
- Retrieved volume > 0 for pass.

**Behavior**
- Fail if all sources return zero items and zero recoverable path exists.
- Partial if some sources fail but minimum coverage survives.
- UI must expose attempted/succeeded/failed counts.

## Stage 3: Normalization
**Rules**
- Canonical schema coercion applied and logged.
- Required field completeness thresholds enforced.
- Invalid records explicitly quarantined.

**Behavior**
- Fail below completeness threshold.
- Warn for type coercions above warning threshold.

## Stage 4: Deduplication
**Rules**
- Every merged duplicate must reference canonical ID and rationale.
- No orphan duplicate pointers.
- Duplicate ratio reported.

**Behavior**
- Warn when duplicate uncertainty exceeds threshold.
- Block downstream spike labeling if dedupe quality is unresolved.

## Stage 5: Event Clustering
**Rules**
- Every article assigned or explicitly unassigned.
- Cluster cohesion above minimum score.

**Behavior**
- One auto-rerun allowed with adjusted profile.
- Fail if cohesion remains below threshold after rerun.

## Stage 6: Temporal Analytics
**Rules**
- Bucket totals equal valid timestamped record count.
- Bucket timezone explicitly declared.
- Spike/trend markers include supporting evidence IDs.

**Behavior**
- Warn when low volume or low source diversity undermines confidence.
- Reject spike labels likely caused by syndication batching.

## Stage 7: Geospatial
**Rules**
- Place entities have evidence links.
- Ambiguous locations flagged.

**Behavior**
- Partial allowed for provider outage with map confidence downgrade.
- Fail only when map output is required by policy and unavailable.

## Stage 8: Narrative Comparison
**Rules**
- Contradictions require >=2 independent evidence records.
- Consensus labels require corroboration threshold.

**Behavior**
- Warn/fail when cross-source coverage is insufficient.
- Never infer consensus from single-source dominance.

## Stage 9: Evidence Packaging
**Rules**
- Every report claim maps to at least one citation.
- Citation metadata completeness validated.

**Behavior**
- Fail publish gate on any orphan claim.

## Stage 10: Report Composition
**Rules**
- Required report sections present.
- Limitations and uncertainty section required when warnings exist.

**Behavior**
- Fail if mandatory sections/citation links missing.

## Stage 11: Critic Loop
**Rules**
- Max iterations bounded (default 2).
- Critic cannot remove citation coverage.
- Confidence regressions require explicit rationale.

**Behavior**
- Re-run only when critical checks fail and a remediation path exists.
- Reject output when unresolved critical failures persist after max iterations.

## 5) Fallback Strategy Matrix
1. **Source failure fallback:** continue with available sources if minimum threshold met; otherwise fail-fast.
2. **Schema drift fallback:** map to canonical fallbacks; quarantine invalid records.
3. **Temporal ambiguity fallback:** drop invalid timestamps from analytics and surface invalid-date count.
4. **Geospatial outage fallback:** continue without map-derived claims unless map is policy-required.
5. **Narrative insufficiency fallback:** emit "insufficient evidence" instead of forced comparison.

## 6) Analyst-Facing Error Handling Requirements
At every failed/warned stage, UI must show:
- failed rule(s),
- observed metric vs threshold,
- recommended next action (rerun, broaden sources, adjust profile, escalate),
- affected downstream outputs.

## 7) Assumptions
- Thresholds are configurable in admin profile.
- Stage artifacts persist enough metadata to compute all rules.
