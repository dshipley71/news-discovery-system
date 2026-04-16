# Geospatial Analysis Operating Manual

## 1) Purpose
Define the geospatial stage used between normalization and aggregation so analysts can inspect location extraction, uncertainty, and map outputs directly in Gradio.

## 2) Stage Placement in Workflow
Required sequence for location-aware analytics:

**Normalization → Geospatial → Aggregation → Clustering**

- **Normalization** produces canonical article records.
- **Geospatial** extracts and resolves location evidence from canonical records.
- **Aggregation** groups extracted locations into UI-ready map summaries.
- **Clustering** uses aggregated geospatial signals plus article features to form event clusters.

## 3) Location Extraction Schema
Each extracted location entity must use this schema:

- `location_id` (stable ID)
- `article_id` (source canonical article reference)
- `city`
- `region_or_state`
- `country`
- `latitude`
- `longitude`
- `confidence_score` (0.0-1.0)
- `extraction_method` (`explicit` or `inferred`)
- `evidence_text_span` (quoted phrase or snippet pointer)
- `evidence_offset` (optional character/token offsets)
- `ambiguity_flag` (boolean)
- `ambiguity_notes` (required when flagged)
- `created_at`

### 3.1 Extraction Method Rules
- `explicit`: location string appears directly in title/body/metadata.
- `inferred`: location derived from contextual signals (publisher locale, known entity mapping, cross-sentence context).
- Inferred locations must include lower or equal confidence than equivalent explicit mentions unless manually reviewed.

## 4) Aggregation Rules
Aggregation transforms per-article location entities into map and clustering inputs.

### 4.1 Article Counts per Location
- Count unique `article_id` values per resolved coordinate pair.
- If multiple mentions in one article resolve to the same location key, count once.
- Preserve raw mention count separately for diagnostics.

### 4.2 Grouping Nearby Locations
- Build proximity groups using configurable distance radius (default design target: 25 km).
- Store grouped centroid (`group_latitude`, `group_longitude`) and member location IDs.
- Keep original points for drill-down; grouping is for map readability, not evidence loss.

### 4.3 Multiple Locations per Article
- One article may contribute to multiple location groups.
- Do not force single-location assignment.
- For ranking and map intensity, each article contributes max 1 count per group to avoid count inflation.

## 5) Geospatial Artifact Definition
Primary output artifact: **Geospatial Map Marker Set**.

### 5.1 Marker Encoding
- Marker position: aggregated centroid.
- Marker size: unique article count at marker/group.
- Marker color: normalized intensity band derived from article count and confidence-weighted density.
- Marker tooltip: location label, article count, average confidence, ambiguity count.

### 5.2 Legend Definition
Legend must include:
1. **Marker Size Legend**: ranges mapping to article count bins (e.g., 1-2, 3-5, 6-10, 10+).
2. **Color Intensity Legend**: low/medium/high concentration.
3. **Uncertainty Legend**: marker outline or icon indicating ambiguity present.

## 6) Gradio UI Integration Contract

### 6.1 Map Output Panel
- Add a dedicated map panel in Analysis Workspace.
- Panel must render the Geospatial Map Marker Set artifact.
- Filters required: date range slice, confidence threshold, ambiguity toggle, source filter, cluster filter.

### 6.2 Click-through Behavior
Required UI drill path:

1. **Location click** → opens location detail drawer.
2. **Location detail** → lists linked cluster IDs (if available).
3. **Cluster click** → opens cluster detail table with linked article IDs.
4. **Article click** → opens citation/evidence panel with location extraction evidence.

No drill step may drop artifact IDs.

## 7) Validation Hooks for Geospatial Stage
- Every location must reference `article_id` and evidence span.
- Every displayed confidence value must be sourced from `confidence_score`.
- Ambiguous locations must be visibly flagged in both table and map.
- Duplicate location mentions must not inflate unique article counts.

## 8) Assumptions
- A resolver/geocoder source is available (API or local resolver table).
- Gradio map-capable component can display markers and selection callbacks.
- Distance radius for grouping is configurable by admin profile.

## 9) Open Decisions
1. Default distance radius by deployment geography.
2. Whether confidence weighting should affect marker size or color only.
3. How to handle articles with only country-level resolution in cluster ranking.
