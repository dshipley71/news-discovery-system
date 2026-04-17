# Artifact and Evidence Specification

## Purpose
Define the first-class backend artifacts emitted by `run_workflow` in `src/news_app/workflow.py`.

## First-Class Backend Artifacts (Implemented)
The backend now emits explicit artifact structures under both `stages.*` and top-level `artifacts.*`.

1. **Deduplicated article set**
   - Path: `artifacts.deduplicated_article_set`
   - Source: normalized canonical records after ingestion deduplication.

2. **Canonical lineage / duplicate map**
   - Path: `artifacts.canonical_lineage_duplicate_map`
   - Fields per group:
     - `dedupe_key`
     - `canonical_article_id`
     - `canonical_source`
     - `article_ids`
     - `duplicate_article_ids`
     - `duplicate_count`

3. **Cluster artifact**
   - Path: `stages.clustering.clusters` and `artifacts.cluster_artifact`
   - Fields per cluster:
     - `cluster_id`
     - `cluster_label`
     - `article_ids`
     - `source_diversity`
     - `cluster_confidence`
     - `temporal_span.start`
     - `temporal_span.end`
     - `heuristic` (currently `deterministic_lexical_token_cluster_v1`)

4. **Citation index**
   - Path: `stages.citation_traceability` and `artifacts.citation_index`
   - Includes:
     - `citations[]`
     - `citation_count`
     - `claim_classification_counts`
     - `by_source`

5. **Evidence bundles**
   - Path: `stages.evidence` and `artifacts.evidence_bundles`
   - Includes:
     - `cluster_to_articles[]`
     - `peak_to_clusters_articles[]`
     - `location_to_clusters_articles[]`

6. **Geospatial entities / markers**
   - Paths:
     - `stages.geospatial.entities[]`
     - `stages.geospatial.map_markers[]`
     - `stages.aggregation.geospatial.map_markers[]` (UI compatibility)
   - Includes explicit evidence linkage and confidence.

7. **Analyst warnings**
   - Path: `stages.warnings` and `artifacts.analyst_warnings`
   - Warning codes currently emitted:
     - `weak_source_diversity`
     - `duplicate_heavy_result_set`
     - `low_confidence_geo`
     - `weak_cluster_evidence`
     - `sparse_coverage`
     - `speculative_interpretation_risk`

## Determinism and Reproducibility
- IDs are generated with deterministic SHA-1-based seeds.
- Duplicate keys are deterministic URL/title/date keys.
- Clustering is deterministic lexical-token grouping (explicitly heuristic).
- Evidence bundle IDs are deterministic from their subject keys.

## Deferred
- Semantic/event embeddings-based clustering (not implemented in this phase).
- External geocoder-backed disambiguation for broad location coverage.
- Claim graph/report generation beyond citation/evidence contracts.
