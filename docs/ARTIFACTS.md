# Artifact and Evidence Specification

## Purpose
Define first-class backend artifacts emitted by `run_workflow` in `src/news_app/workflow.py` and consumed by the Gradio analyst dashboard.

## First-Class Backend Artifacts (Implemented)

1. **Deduplicated article set**
   - Path: `artifacts.deduplicated_article_set`
   - Source: normalized canonical records after ingestion deduplication.
   - Date normalization fields per article:
     - `updated_at`
     - `retrieved_at`
     - `published_at_parsed`
     - `published_day`
     - `timeline_date_used` (default publication-date day)
     - `timeline_date_source`
     - `date_status` (`parsed`, `missing`, `parse_failed`, `fallback_derived`)
     - `date_source_field`
     - `date_parse_format_used`
     - `date_parse_error`

2. **Canonical lineage / duplicate map**
   - Path: `artifacts.canonical_lineage_duplicate_map`
   - Fields per group:
     - `dedupe_key`
     - `canonical_article_id`
     - `canonical_source`
     - `article_ids`
     - `duplicate_article_ids`
     - `duplicate_count`

3. **Event artifact (cluster-to-event transformation)**
   - Path: `stages.clustering.clusters`, `artifacts.cluster_artifact`, and `artifacts.event_artifact`
   - Intermediate lexical clusters are no longer analyst-facing. Final records are constructed event objects.
   - Fields per event:
     - `event_id`
     - `event_label`
     - `first_seen_date`
     - `last_seen_date`
     - `peak_date`
     - `event_type`
     - `article_ids`
     - `source_ids`
     - `location` (`event_location`)
     - `confidence`
   - Backward-compatible aliases:
     - `cluster_id`
     - `cluster_label`
     - `cluster_confidence`
     - `lifecycle_stage`
     - `heuristic`

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
     - `stages.aggregation.geospatial.map_markers[]`
     - `artifacts.geospatial_entities_markers`
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
     - `temporal_anomaly`
     - `source_bias_detected`

8. **Event lifecycle index**
   - Path: `artifacts.event_lifecycle_index`
   - Keyed by `event_id`, includes:
     - `first_seen_date`
     - `peak_date`
     - `last_seen_date`
   - `lifecycle_stage`
   - `daily_event_signal[]`

9. **Run review log export artifact**
   - Path: `artifacts.run_review_log`
   - Formats:
     - `artifacts.run_review_log.json` (structured, deterministic review payload)
     - `artifacts.run_review_log.markdown` (analyst-readable summary for ChatGPT copy/paste)
   - JSON sections:
     - `query_metadata`
     - `source_retrieval_summary`
     - `date_integrity_summary`
     - `timeline_summary`
     - `cluster_summary`
     - `geospatial_summary`
     - `validation_and_warnings`
     - `analyst_review_note`
   - Source of truth:
     - Derived exclusively from workflow stage outputs (`stages.ingestion`, `stages.normalization`, `stages.aggregation`, `stages.clustering`, `stages.geospatial`, `stages.validation`, `stages.warnings`).
   - Also mirrored in stages for UI panels:
     - `stages.review_log`
     - `stages.review_log_markdown`

## Dashboard Consumption Contract (Current)
The Gradio dashboard reads artifacts directly with these mappings:

- **Run summary totals/warnings**
  - `stages.ingestion`, `stages.normalization`, `stages.warnings`
- **Timeline panel**
  - `stages.aggregation.event_signal_timeline` (also mirrored in `daily_counts` for compatibility)
  - default signal is `event_signal`
  - diagnostic signal is `coverage_volume`
  - diagnostics include `raw_retrieved_count`, `duplicate_ratio`, and `source_breakdown[]`
  - source dominance diagnostics include `dominant_source`, `dominance_ratio`, and `source_bias_detected`
  - temporal plausibility diagnostics include `temporal_anomaly`, `temporal_anomaly_explanation`
  - cluster timeline diagnostics in `stages.aggregation.daily_cluster_counts`
  - `stages.aggregation.source_date_quality`
  - `artifacts.evidence_bundles.peak_to_clusters_articles`
- **Geospatial panel**
  - `stages.geospatial.map_markers` or `artifacts.geospatial_entities_markers.map_markers`
  - `artifacts.evidence_bundles.location_to_clusters_articles`
- **Cluster explorer**
  - `artifacts.event_artifact` (fallback: `artifacts.cluster_artifact`)
  - `artifacts.deduplicated_article_set`
  - `artifacts.canonical_lineage_duplicate_map`
- **Citation/evidence explorer**
  - `artifacts.citation_index`
  - `artifacts.evidence_bundles`
- **Validation panels**
  - ingestion, normalization, aggregation, clustering, geospatial, warnings payloads from `stages.*`
- **Run review export panel**
  - markdown export: `stages.review_log_markdown` (fallback: `artifacts.run_review_log.markdown`)
  - JSON export: `stages.review_log` (fallback: `artifacts.run_review_log.json`)

## Determinism and Reproducibility
- IDs are generated with deterministic SHA-1-based seeds.
- Duplicate keys are deterministic URL/title/date keys.
- Event construction is deterministic (entity + action + location + time grouping with cross-day merge).
- Evidence bundle IDs are deterministic from subject keys.

## Deferred
- Embeddings/event-based clustering improvements.
- External geocoder-backed disambiguation for broader location coverage.
- Higher-order claim graph/report synthesis beyond current citation/evidence contracts.
