# Failure Modes for In-Repo Analyst Workflow

## Purpose
Define failure modes and mitigations for backend-first artifact generation.

## Failure Mode Matrix

| Failure mode | Detection | Current mitigation | Artifact impact |
|---|---|---|---|
| Duplicate-heavy set | `ingestion_duplicate_ratio` high | deterministic dedup + duplicate map + warning `duplicate_heavy_result_set` | protects clusters/timeline/map from inflation |
| Weak source diversity | unique source count < 2 | warning `weak_source_diversity` | analyst cautioned on corroboration limits |
| Weak cluster evidence | small/low-confidence clusters | warning `weak_cluster_evidence` | clusters remain inspectable but flagged |
| Sparse coverage | few articles or active days | warning `sparse_coverage` | trend/peak interpretations flagged |
| Low-confidence/ambiguous geo | ambiguous or low-confidence geo entities | warning `low_confidence_geo` | geo claims remain evidence-linked and reviewable |
| Citation risk | high speculative citation share | warning `speculative_interpretation_risk` | claim confidence explicitly downgraded |
| Missing stage contracts | absent artifact structures | test failures + validation rules | prevents silent UI fallback invention |

## No Silent Failure Rule
Core analysis objects (clusters, citations, evidence bundles, geospatial markers, warnings) must be emitted by backend stages, not invented in UI callbacks.

## Analyst-visible remediation pattern
For warning states, analysts should:
1. Inspect duplicate lineage table.
2. Inspect cluster evidence bundles.
3. Inspect geospatial ambiguity flags.
4. Review citation classification distribution.
5. Rerun with wider date/source coverage if needed.

## Deferred failure modes
- External geocoder outages (not yet integrated).
- Embedding-model drift (semantic clustering deferred).
