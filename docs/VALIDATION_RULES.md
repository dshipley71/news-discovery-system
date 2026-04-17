# Validation Rules (In-Repo Multi-Source Workflow)

## Purpose
Define pass/warn/fail rules for backend artifacts produced by the in-repo workflow.

## Status semantics
- **PASS:** artifact contract is valid.
- **WARN:** artifact is usable but confidence is reduced.
- **FAIL:** required contract is missing or unusable.

## Artifact Contract Checks

### Deduplication and lineage
- PASS: duplicate telemetry includes `ingestion_duplicate_ratio` and `duplicate_map[]` with canonical IDs.
- WARN: duplicate ratio >= 0.20.
- FAIL: duplicate map missing when articles exist.

### Cluster artifact
- PASS: every cluster has `cluster_id`, `cluster_label`, `article_ids`, `source_diversity`, `cluster_confidence`, and `temporal_span`.
- WARN: cluster confidence < 0.55 or cluster has < 2 articles.
- FAIL: cluster stage missing while canonical articles exist.

### Citation index
- PASS: `citation_count == len(citations)` and every citation references canonical `article_id`.
- WARN: speculative share > 0.40.
- FAIL: missing citations for canonical articles in analysis mode.

### Evidence bundles
- PASS: all three bundle families exist:
  - `cluster_to_articles`
  - `peak_to_clusters_articles`
  - `location_to_clusters_articles`
- WARN: peak/location bundle families are empty due to sparse upstream data.
- FAIL: bundle stage absent.

### Geospatial
- PASS: each geospatial entity includes location fields, confidence, extraction method, and article linkage.
- WARN: ambiguous or low-confidence geo entities present.
- FAIL: malformed geospatial records (missing `article_id` or coordinates where marker is emitted).

### Warning signals
- PASS: warning stage present even if empty list.
- FAIL: warning stage missing.

## Analyst Warning Codes
- `weak_source_diversity`
- `duplicate_heavy_result_set`
- `low_confidence_geo`
- `weak_cluster_evidence`
- `sparse_coverage`
- `speculative_interpretation_risk`

## Implementation note
Current clustering and location extraction are explicitly heuristic and deterministic for reproducibility.
