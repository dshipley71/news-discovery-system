# COLAB_RUNBOOK

## Purpose
This runbook defines the **production Colab path** for running and validating the in-repo Gradio analyst application end-to-end without requiring command-line usage for analysts.

## Scope
- Notebook: `notebooks/news_discovery_colab.ipynb`
- UI: `gr_app.py` (launched with `share=True`)
- Backend workflow: `src/news_app/workflow.py`
- Source configuration: `config/sources.json`

## Colab Launch Procedure
1. Open `notebooks/news_discovery_colab.ipynb` in Google Colab.
2. Run cells in order, top to bottom.
3. In **Section 3** (repository load), either:
   - run directly from an already-mounted repository copy, or
   - set `NEWS_DISCOVERY_REPO_URL` and allow notebook-driven clone.
4. In **Section 4**, optionally set `TWITTER_BEARER_TOKEN`.
   - If not set, X/Twitter is skipped and warning behavior remains visible.
5. In **Section 5**, launch Gradio; open the generated public URL.

## Analyst Workflow (UI-Only)
From the shared Gradio URL:
1. Enter `Topic`, `Start date`, and `End date`.
2. Click **Run Workflow**.
3. Review summary and inspect all panels (timeline, geospatial, cluster, evidence/citation, validation payloads).

## Required Validation Coverage
A valid analyst session must verify all of the following:
- Per-source ingestion status for:
  - Reddit
  - Google News
  - Web via DuckDuckGo HTML
  - GDELT
  - optional X/Twitter
- Partial source failures and non-fatal warnings.
- Normalization output counts and validation issues.
- Duplicate handling telemetry and lineage map.
- Clustering output (cluster counts and membership).
- Geospatial output (entity/marker visibility and confidence cues).
- Timeline correctness (day counts and ordering).
- Citation/evidence availability.
- Warning behavior visibility in both summary and payload views.

## Notebook-Level Diagnostics (When UI Fails)
Use Section 6 notebook diagnostics to run `run_workflow(...)` directly and inspect:
- `stages.ingestion.source_runs`
- `stages.normalization`
- `stages.clustering`
- `stages.geospatial`
- `stages.aggregation.daily_counts`
- `stages.citation_traceability`
- `stages.warnings`

This allows root-cause analysis even when a UI panel appears empty.

## Known Limitations
- External providers can rate-limit or intermittently fail.
- First Colab run can be slower due to dependency cold start.
- The shared Gradio URL is temporary; keep notebook runtime active during validation.
- Geospatial results may be sparse for topics with weak location signals.
