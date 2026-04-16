# News Discovery System - MVP Scaffold

This repository now includes a **minimal, real, executable vertical slice** aligned to the implementation plan:

- UI intake (topic + date range)
- UI workflow trigger
- Real ingestion from one public source (Hacker News Algolia API)
- Basic normalization with validation issues
- Daily aggregation + simple timeline chart
- Intermediate output inspection panels

## Run locally

```bash
python app.py
```

Open `http://localhost:8000` in your browser.

## UI step-by-step validation

1. Enter a topic and date range (<= 30 days).
2. Click **Run Workflow**.
3. Confirm run metadata appears (`run_id`, `started_at`).
4. In **Step 1: Ingestion Validation**:
   - check retrieved hit counts;
   - inspect raw records in JSON.
5. In **Step 2: Normalization Validation**:
   - verify canonical records;
   - inspect flagged invalid records.
6. In **Step 3: Aggregation + Timeline Validation**:
   - verify daily counts JSON;
   - verify line chart points match daily counts.

## What is intentionally incomplete

Deferred to next increments:
- multi-source ingestion and fallback routing
- deduplication, clustering, geospatial stages
- narrative comparison and report generation
- citation graph gating and critic loop
- exports and policy profiles

See `docs/MVP_SCAFFOLD_PLAN.md` for explicit built-vs-deferred scope.
