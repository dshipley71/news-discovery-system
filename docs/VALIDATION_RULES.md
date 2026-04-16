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
- Location traceability coverage (`location_id -> article_id -> evidence_span`): **100% required**.
- Geospatial confidence visibility (records with shown confidence in UI): **100% required**.
- Claim-to-citation coverage for publish: **100% required**.

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

## Stage 4: Geospatial Extraction
**Rules**
- Each extracted location has: city/region-or-state/country fields when available, coordinates when resolved, confidence score, and extraction method.
- Each location links to source article and evidence span.
- Ambiguous locations are explicitly flagged.
- Confidence score is bounded in [0.0, 1.0].

**Behavior**
- Fail if traceability is incomplete.
- Warn when unresolved/ambiguous share exceeds threshold.
- Partial allowed when resolver service is degraded but extraction evidence remains available.

## Stage 5: Geospatial Aggregation
**Rules**
- Article counts per location use unique `article_id` values (duplicate mentions cannot inflate counts).
- Nearby grouping method and distance radius are logged.
- Multiple locations per article are retained.
- Marker size must equal aggregated unique article count.
- Marker color must map to defined intensity bands.

**Behavior**
- Fail if duplicate inflation is detected.
- Warn if grouping creates unstable/over-merged results above threshold.
- Block downstream cluster scoring if geospatial aggregation integrity fails.

## Stage 6: Event Clustering
**Rules**
- Every article assigned or explicitly unassigned.
- Cluster cohesion above minimum score.
- Cluster records include linked location groups when present.

**Behavior**
- One auto-rerun allowed with adjusted profile.
- Fail if cohesion remains below threshold after rerun.

## Stage 7: Temporal Analytics
**Rules**
- Bucket totals equal valid timestamped record count.
- Bucket timezone explicitly declared.
- Spike/trend markers include supporting evidence IDs.

**Behavior**
- Warn when low volume or low source diversity undermines confidence.
- Reject spike labels likely caused by syndication batching.

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
4. **Geospatial resolver outage fallback:** continue with extraction-only artifacts and uncertainty warnings; suppress map-derived claims.
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
