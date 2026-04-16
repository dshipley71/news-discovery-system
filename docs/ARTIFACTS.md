# Artifact and Evidence Specification

## 1) Purpose
Define artifact expectations and UI-facing lineage for the current analyst dashboard implementation.

## 2) Active Workflow Artifacts (Current)
The workflow currently returns:
1. **Run Metadata**
   - `run_id`, `started_at`, input topic/date window
2. **Ingestion Output**
   - source ID, request metadata, `hits_count`, `raw_hits[]`
3. **Normalization Output**
   - `canonical_articles[]`, validation issues, valid/invalid counts
4. **Aggregation Output**
   - `daily_counts[]`, `total_days`

These are the only guaranteed stage artifacts and are shown directly in the dashboard validation accordion.

## 3) Dashboard-Derived Analyst Artifacts
The UI creates analyst views derived from current stage outputs (never simulated):

### 3.1 Timeline View Model
- Derived from `aggregation.daily_counts[]`
- Includes peak annotation and trend summary text.

### 3.2 Cluster View Model
- Derived from `normalization.canonical_articles[]`
- Current grouping uses publication-day cluster IDs (`cluster:YYYY-MM-DD`) so analysts can inspect event density and duplicate behavior.
- Includes:
  - cluster summary rows,
  - cluster detail object,
  - cluster article membership rows,
  - duplicate ratio and source concentration metrics.

### 3.3 Citation View Model
- Derived from `normalization.canonical_articles[]`
- Includes citation records with:
  - `citation_id`, `article_id`, `cluster_id`, `source`, `publication_date`, `url`, `claim_classification`, duplicate flag.
- Includes citation index totals and per-source counts.

### 3.4 Evidence Bundle View Model
- Derived from cluster and citation view models.
- Includes explicit linkage rows:
  - `bundle_id`, `bundle_type`, `bundle_subject_id`, `article_id`, `citation_id`, `source`.

### 3.5 Geospatial View Model
- Primary source: `aggregation.geospatial.map_markers[]` when provided by workflow.
- Fallback source: canonical articles carrying latitude/longitude fields.
- If neither source exists, UI emits no rows and displays explicit no-data state.

## 4) Traceability Rules in Current UI
- Every rendered panel must be reproducible from the same run payload.
- Cluster/citation/evidence rows must reference canonical `article_id` values.
- Map rows must only appear when coordinate-bearing records are present.
- No artificial rows may be generated for unavailable stages.

## 5) Planned Artifact Expansion (Not Yet Guaranteed)
Future workflow stages may supply first-class artifacts for:
- geospatial extraction + grouped markers,
- semantic/event clustering,
- claim nodes and claim-linkage references.

Until then, UI-level derived models remain inspectable and explicitly labeled as derived from existing stage artifacts.
