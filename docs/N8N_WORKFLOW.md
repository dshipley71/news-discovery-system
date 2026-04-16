# n8n Core Workflow (Importable Export)

## Purpose
This document provides an importable n8n workflow export that mirrors the current Python `run_workflow` vertical slice:
- input intake (`topic`, `start_date`, `end_date`)
- ingestion from Hacker News Algolia
- normalization to canonical article records
- daily aggregation
- JSON response suitable for UI integration

Workflow export file:
- `docs/n8n/news_core_pipeline.workflow.json`

## Input Contract
Send a `POST` request to the workflow webhook with JSON body:

```json
{
  "topic": "semiconductor",
  "start_date": "2026-04-10",
  "end_date": "2026-04-16"
}
```

## Output Contract
The response shape aligns with `run_workflow` and contains:
- `run_id`
- `started_at`
- `input`
- `stages.ingestion`
- `stages.normalization`
- `stages.aggregation`

## Import Instructions (n8n)
1. Open n8n.
2. Go to **Workflows** → **Import from File**.
3. Select `docs/n8n/news_core_pipeline.workflow.json`.
4. Save workflow.
5. Activate workflow (optional for production URL).

## Trigger Instructions
1. Open the imported workflow.
2. Copy the Webhook URL from node **Webhook Input**.
3. Send a `POST` request:

```bash
curl -X POST '<WEBHOOK_URL>' \
  -H 'Content-Type: application/json' \
  -d '{
    "topic": "semiconductor",
    "start_date": "2026-04-10",
    "end_date": "2026-04-16"
  }'
```

## Node-by-Node Flow
1. **Webhook Input**: receives request payload.
2. **Prepare Run Input** (Code): validates inputs, computes epoch bounds, creates `run_id`, and builds ingestion query fields.
3. **Ingest from Hacker News Algolia** (HTTP Request): calls real public API `search_by_date` with date filters.
4. **Merge Input + Ingestion** (Merge): combines intake metadata and API response.
5. **Normalize + Aggregate** (Code):
   - maps raw hits to canonical records,
   - emits validation issues for missing fields,
   - computes `daily_counts` grouped by UTC day,
   - constructs final response payload.
6. **Respond** (Respond to Webhook): returns structured JSON response.

## Current Limitations
- Single source only (`hackernews_algolia`), no source plan stage yet.
- No persistence layer for artifact versioning (response-only execution).
- Aggregation is limited to daily article counts.
- No deduplication/event clustering/geospatial/narrative/report stages in this workflow slice.

## Recommended Next Iteration
1. Add second real source branch and merge normalized outputs.
2. Add artifact persistence write nodes (run manifest + stage artifacts).
3. Add deduplication node prior to aggregation.
4. Add response metadata (`stage_durations`, `warnings`) for richer UI status.
5. Wrap webhook as a UI backend endpoint in `gr_app.py` integration path.
