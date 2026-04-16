# Artifact and Evidence Specification

## 1) Purpose
Define the canonical artifacts produced through the workflow, their schemas at a conceptual level, and lineage requirements.

## 2) Artifact Principles
- Every artifact has a stable ID.
- Every artifact is timestamped and linked to run/stage IDs.
- Artifacts are immutable once finalized for a stage.
- Derived artifacts must reference parent artifact IDs.
- Geospatial and cluster artifacts must remain traceable to canonical article IDs.
- No artifact may contain simulated clusters or simulated citations.

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
8. **Cluster Set**
   - Cluster IDs, member articles, source-diversity metrics, confidence metrics.
9. **Timeline Metrics Set**
   - Time buckets, counts, detected patterns.
10. **Narrative Matrix**
    - Agreements, contradictions, unique claims by source/cluster.
11. **Citation Set**
    - Article-level citations and claim linkage records.
12. **Evidence Bundle Index**
    - Cross-artifact bundle pointers for cluster/peak/location drill-down.
13. **Report Package**
    - Final report content + export variants.
14. **Critic Log**
    - Iteration critiques, revisions, resolved/unresolved issues.

## 4) Core Schemas (Conceptual)

### 4.1 Cluster Record
Required fields:
- `cluster_id`
- `cluster_label`
- `article_ids[]`
- `article_membership[]` (article-level membership rows with at minimum `article_id`, `source`, `duplicate_flag`)
- `source_diversity` (count and/or normalized score across independent sources)
- `cluster_confidence` (bounded numeric score)
- `duplicate_ratio`
- `duplicate_heavy` (boolean threshold flag for analyst triage)

Recommended fields:
- `unassigned_reason` (if cluster is fallback/weak)
- `linked_location_group_ids[]`
- `linked_peak_ids[]`
- `created_at`

### 4.2 Citation Record
Required fields:
- `citation_id`
- `article_id`
- `source`
- `url`
- `publication_date`
- `claim_linkage[]`
- `claim_classification` (`supported` | `inferred` | `speculative`)

Recommended fields:
- `retrieved_at`
- `excerpt_ref`
- `stance` (`supports` | `contradicts` | `context`)
- `confidence_contribution`

### 4.3 Evidence Bundle Record
Required fields:
- `bundle_id`
- `bundle_type` (`cluster_support` | `peak_support` | `location_support`)
- `bundle_subject_id` (cluster_id, peak_id, or location_group_id)
- `cluster_ids[]`
- `article_ids[]`
- `citation_ids[]`
- `created_at`
- `source_attribution[]`

## 5) Evidence Bundle Relationship Requirements
The pipeline must produce explicit, queryable relationships for:
- `cluster -> supporting articles`
- `peak -> clusters -> articles`
- `location -> clusters -> articles`
- `cluster -> citations -> claim classifications`

Each relationship layer must be materialized in artifacts (not inferred only at render time) so UI and export packages can audit lineage deterministically.

## 6) Traceability Requirements
- Any UI insight (chart point, map marker, narrative statement) must resolve to underlying artifact IDs.
- Any report sentence flagged as analytical claim must resolve to citation records.
- Any cluster claim must resolve to member `article_ids[]` and corresponding citation IDs.
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
- Cluster and evidence-bundle artifacts used by timeline/map/report narratives

## 9) Assumptions
- Underlying data store supports immutable versioned records.
- UI can request artifact details by ID on demand.
- Cluster generation runs only on validated canonical article sets.

## 10) Open Decisions
1. Storage format standards for large artifact bundles.
2. Long-term archive and legal-hold policy.
3. Whether evidence snippets are stored inline or referenced externally.
4. Whether source diversity is stored as scalar score only or with decomposed metrics.
