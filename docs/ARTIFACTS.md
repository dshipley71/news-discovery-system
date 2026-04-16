# Artifact and Evidence Specification

## 1) Purpose
Define the canonical artifacts produced through the workflow, their schemas at a conceptual level, and lineage requirements.

## 2) Artifact Principles
- Every artifact has a stable ID.
- Every artifact is timestamped and linked to run/stage IDs.
- Artifacts are immutable once finalized for a stage.
- Derived artifacts must reference parent artifact IDs.
- Geospatial artifacts must remain traceable to canonical article IDs.

## 3) Core Artifact Catalog
1. **Run Manifest**
   - Contains topic, date window, config profile, orchestration mode.
2. **Source Plan**
   - Source list, query parameters, credential mode (key/non-key), fallback order.
3. **Raw Retrieval Bundle**
   - Source responses, retrieval metadata, errors.
4. **Canonical Article Set**
   - Normalized schema records.
5. **Location Extraction Set**
   - One record per extracted location mention linked to article evidence.
6. **Geospatial Aggregation Set**
   - Unique article counts by location, nearby-location groups, confidence rollups.
7. **Geospatial Map Marker Set**
   - Marker geometry, size metric, color intensity metric, legend metadata.
8. **Event Group Set**
   - Event IDs, member articles, event summaries, confidence.
9. **Timeline Metrics Set**
   - Time buckets, counts, detected patterns.
10. **Narrative Matrix**
    - Agreements, contradictions, unique claims by source/event.
11. **Citation Graph**
    - Claim nodes mapped to evidence nodes and source metadata.
12. **Report Package**
    - Final report content + export variants.
13. **Critic Log**
    - Iteration critiques, revisions, resolved/unresolved issues.

## 4) Geospatial Artifact Schemas (Conceptual)

### 4.1 Location Extraction Record
Required fields:
- `location_id`
- `article_id`
- `city`
- `region_or_state`
- `country`
- `latitude`
- `longitude`
- `confidence_score`
- `extraction_method` (`explicit` | `inferred`)
- `ambiguity_flag`
- `evidence_text_span`
- `created_at`

### 4.2 Geospatial Aggregation Record
Required fields:
- `aggregation_id`
- `location_group_id`
- `member_location_ids[]`
- `group_latitude`
- `group_longitude`
- `unique_article_count`
- `raw_mention_count`
- `avg_confidence`
- `ambiguity_count`
- `grouping_radius_km`

### 4.3 Geospatial Marker Record
Required fields:
- `marker_id`
- `location_group_id`
- `latitude`
- `longitude`
- `marker_size_value` (article-count driven)
- `marker_color_band` (intensity driven)
- `legend_size_bucket`
- `legend_intensity_bucket`
- `linked_cluster_ids[]`

## 5) Citation and Evidence Mapping
Each claim-level citation entry must include:
- Claim ID
- Evidence item ID(s)
- Source name
- Source URL or immutable source locator
- Publish timestamp (if available)
- Retrieval timestamp
- Excerpt/snippet reference or content hash
- Confidence contribution

For geospatial claims, citation entries must also include the originating `location_id` or `location_group_id`.

## 6) Traceability Requirements
- Any UI insight (chart point, map marker, narrative statement) must resolve to underlying artifact IDs.
- Any report sentence flagged as analytical claim must resolve to Citation Graph nodes.
- Any map marker must resolve to location groups and then to article IDs.
- Orphan claims are prohibited for publishable reports.

## 7) Retention and Versioning (design requirement)
- Keep raw retrieval artifacts for audit duration policy.
- Keep derived artifacts with version tags per run and refinement iteration.
- Critic revisions must not overwrite prior versions.

## 8) Export Bundles
Minimum export bundle contents:
- Final report (human-readable)
- Citation appendix
- Evidence index
- Machine-readable manifest of artifact IDs and lineage
- Geospatial marker and aggregation artifacts used in the UI map

## 9) Assumptions
- Underlying data store supports immutable versioned records.
- UI can request artifact details by ID on demand.

## 10) Open Decisions
1. Storage format standards for large artifact bundles.
2. Long-term archive and legal-hold policy.
3. Whether evidence snippets are stored inline or referenced externally.
