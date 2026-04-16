# MVP Scaffold Plan (Vertical Slice)

## Purpose
Define the smallest executable scaffold mapped to the approved implementation plan, while intentionally deferring non-MVP capabilities.

## Mapping to Implementation Plan

### Built now (MVP)
1. **Phase 1: UI Shell + Workflow Trigger (partial)**
   - UI form for topic + explicit start/end date.
   - "Run Workflow" trigger from UI.
   - Run ID, stage statuses, and stage outputs visible in UI.

2. **Phase 2: Ingestion (minimal single-source subset)**
   - One real source integration via public Hacker News Algolia API.
   - Retrieval metadata and raw payload exposed for inspection.

3. **Phase 3: Normalization (basic subset)**
   - Minimal canonical fields:
     - `article_id`
     - `title`
     - `url`
     - `published_at`
     - `source`
   - Invalid records are flagged and shown in validation output.

4. **Phase 4: Temporal analytics (daily aggregation subset)**
   - Daily counts generated from normalized records.
   - Timeline chart rendered in UI.

### Deferred intentionally
- Multi-source routing/failover and credential-vault behavior.
- Deduplication, event clustering, geospatial extraction, narrative comparison.
- Report composition, citation graph, critic loop, export pipeline.
- Advanced threshold tuning and policy profiles.

## Assumptions
- MVP allows explicit date range fields for usability, while preserving plan intent (date-bounded analyst query).
- A single no-auth source is sufficient for initial end-to-end operational validation.
- Python standard-library HTTP server + browser UI is used as the thinnest practical executable UI + trigger layer for this vertical slice.

## Acceptance Criteria for this MVP
1. Analyst can run workflow from UI only.
2. At least one real source retrieval succeeds for common topics.
3. Normalized records and validation issues are inspectable.
4. Daily count aggregation is inspectable and visualized.
5. End-to-end run works locally with minimal setup.
