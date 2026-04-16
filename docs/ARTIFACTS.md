# Artifact and Evidence Specification

## 1) Purpose
Define the canonical artifacts produced through the workflow, their schemas at a conceptual level, and lineage requirements.

## 2) Artifact Principles
- Every artifact has a stable ID.
- Every artifact is timestamped and linked to run/stage IDs.
- Artifacts are immutable once finalized for a stage.
- Derived artifacts must reference parent artifact IDs.

## 3) Core Artifact Catalog
1. **Run Manifest**
   - Contains topic, date window, config profile, orchestration mode.
2. **Source Plan**
   - Source list, query parameters, credential mode (key/non-key), fallback order.
3. **Raw Retrieval Bundle**
   - Source responses, retrieval metadata, errors.
4. **Canonical Article Set**
   - Normalized schema records.
5. **Deduplication Map**
   - Canonical-to-duplicate relationships + rationale.
6. **Event Group Set**
   - Event IDs, member articles, event summaries, confidence.
7. **Timeline Metrics Set**
   - Time buckets, counts, detected patterns.
8. **Geospatial Entity Set**
   - Place entities, disambiguation outcomes, coordinates/regions, confidence.
9. **Narrative Matrix**
   - Agreements, contradictions, unique claims by source/event.
10. **Citation Graph**
    - Claim nodes mapped to evidence nodes and source metadata.
11. **Report Package**
    - Final report content + export variants.
12. **Critic Log**
    - Iteration critiques, revisions, resolved/unresolved issues.

## 4) Citation and Evidence Mapping
Each claim-level citation entry must include:
- Claim ID
- Evidence item ID(s)
- Source name
- Source URL or immutable source locator
- Publish timestamp (if available)
- Retrieval timestamp
- Excerpt/snippet reference or content hash
- Confidence contribution

## 5) Traceability Requirements
- Any UI insight (chart point, map marker, narrative statement) must resolve to underlying artifact IDs.
- Any report sentence flagged as analytical claim must resolve to Citation Graph nodes.
- Orphan claims are prohibited for publishable reports.

## 6) Retention and Versioning (design requirement)
- Keep raw retrieval artifacts for audit duration policy.
- Keep derived artifacts with version tags per run and refinement iteration.
- Critic revisions must not overwrite prior versions.

## 7) Export Bundles
Minimum export bundle contents:
- Final report (human-readable)
- Citation appendix
- Evidence index
- Machine-readable manifest of artifact IDs and lineage

## 8) Assumptions
- Underlying data store supports immutable versioned records.
- UI can request artifact details by ID on demand.

## 9) Open Decisions
1. Storage format standards for large artifact bundles.
2. Long-term archive and legal-hold policy.
3. Whether evidence snippets are stored inline or referenced externally.
