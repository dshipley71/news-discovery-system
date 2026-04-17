# Workflow Operating Manual (In-Repo Runtime)

## Execution model
The analyst workflow executes entirely in-repo through:
- `run_workflow(run_input)` in `src/news_app/workflow.py`.

No external workflow engine is required.

## Stage contracts (Implemented)

### Stage 0: Intake
Inputs:
- `topic`
- `start_date`
- `end_date`

### Stage 1: Multi-source ingestion
Behavior:
- Loads enabled source configs.
- Dispatches source adapters from in-repo registry.
- Supports partial source failures.
- Deduplicates records deterministically.
- Emits canonical lineage duplicate map.

Outputs include:
- `raw_hits` (deduplicated for downstream)
- `source_runs`, per-source status/warnings/errors/metadata
- telemetry including duplicate metrics and duplicate map

### Stage 2: Normalization
Behavior:
- Validates required fields.
- Produces canonical article schema.
- Preserves source attribution.

Output:
- `canonical_articles`
- `validation_issues`

### Stage 3: Clustering (first-class backend artifact)
Behavior:
- Deterministic lexical-token clustering heuristic.
- Produces cluster confidence, source diversity, and temporal span.

Output:
- `clusters[]`
- `article_to_cluster`

### Stage 4: Citation traceability (first-class backend artifact)
Behavior:
- Generates citation records tied to canonical article IDs and clusters.
- Classifies claim support level deterministically.

Output:
- `citations[]`
- `citation_count`
- `claim_classification_counts`
- `by_source`

### Stage 5: Geospatial extraction/aggregation (first-class backend artifact)
Behavior:
- Extracts explicit location mentions from canonical article text.
- Emits confidence and ambiguity flags.
- Aggregates map markers by location without duplicate article inflation.

Output:
- `geospatial.entities[]`
- `geospatial.map_markers[]`

### Stage 6: Evidence bundles (first-class backend artifact)
Behavior:
- Emits explicit backend evidence linkage for:
  - cluster -> articles
  - peak day -> clusters -> articles
  - location -> clusters -> articles

Output:
- `evidence.cluster_to_articles[]`
- `evidence.peak_to_clusters_articles[]`
- `evidence.location_to_clusters_articles[]`

### Stage 7: Warning signal generation
Behavior:
- Computes analyst warnings from coverage, duplicates, clustering, geospatial confidence, and citation risk.

Output:
- `warnings[]`

### Stage 8: Aggregation
Behavior:
- Computes day-level counts and exposes geospatial markers in aggregation for UI compatibility.

Output:
- `daily_counts`
- `total_days`
- `aggregation.geospatial.map_markers`

## Deferred
- Semantic clustering beyond deterministic lexical heuristics.
- Broad geocoding/resolution pipelines beyond current location lexicon.
- Full report generation layer.
