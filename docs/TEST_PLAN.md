# UI-Executable Test Plan (Colab + Gradio Analyst Validation)

## 1) Purpose
Validate that the in-repo Gradio analyst application is executable from Google Colab, preserves evidence traceability, and exposes inspectable outputs across all workflow stages.

## 2) Test Environment
- Primary execution path: `notebooks/news_discovery_colab.ipynb`.
- UI launch: `gr_app.py` with `share=True`.
- Workflow backend: `src/news_app/workflow.py` (real execution, no mock payload injection).
- Source configuration: `config/sources.json`.

## 3) Acceptance Tests by Analyst Objective

### AT-1 Launch Reliability (Colab)
1. Run notebook Sections 1-5 in sequence.
2. Confirm Gradio process stays alive.
3. Confirm a public Gradio URL is generated.

Expected:
- Analyst can access UI from browser without local CLI use.
- Launch path is reproducible on fresh Colab runtime.

### AT-2 Per-Source Ingestion Visibility
1. Run workflow for a current-events topic and recent date range.
2. Inspect ingestion validation output.
3. Confirm each configured source has status + article count:
   - reddit
   - google_news
   - web_duckduckgo
   - gdelt
   - twitter (optional)

Expected:
- All sources appear in ingestion output, including failed/skipped states.
- Source-level warnings are visible and inspectable.

### AT-3 Partial Source Failure Handling
1. Run without `TWITTER_BEARER_TOKEN`.
2. Re-run workflow.

Expected:
- X/Twitter is marked as skipped/failed with explicit warning.
- Overall run still completes; no fatal pipeline stop.

### AT-4 Normalization + Duplicate Handling
1. Inspect normalization panel/payload.
2. Confirm `valid_count`, `invalid_count`, and canonical article list are visible.
3. Inspect ingestion telemetry for duplicate ratio and duplicate map.

Expected:
- Normalization output is artifact-backed and inspectable.
- Duplicate handling metrics are present and explainable.

### AT-5 Clustering Output
1. Inspect cluster summary + detail panels.
2. Validate cluster counts and article membership.

Expected:
- Cluster records include IDs, labels, and article IDs.
- Cluster output is consistent with canonical article set.

### AT-6 Geospatial Output
1. Inspect map and geospatial payload.
2. Validate marker/entity counts and confidence/ambiguity metadata.

Expected:
- Geospatial output is present when location-bearing entities exist.
- No-data geospatial state is explicit when absent.

### AT-7 Timeline Correctness
1. Inspect timeline panel and aggregation payload.
2. Confirm daily counts are date-ordered and plausible.

Expected:
- Timeline ordering is correct.
- Peak day inspection aligns with article-level evidence.

### AT-8 Citation / Evidence Availability
1. Inspect citation index and evidence bundle views.
2. Compare citation count with available citation rows.

Expected:
- Citation/evidence records are present when canonical articles exist.
- Traceability fields (article ID, URL/source metadata, claim classification where available) are inspectable.

### AT-9 Warning Behavior
1. Inspect run summary warning block.
2. Inspect warnings payload in validation panel.

Expected:
- Warnings are explicit (not silent).
- Warning details include code/category/message/metrics where provided.

## 4) Notebook Diagnostic Procedure
If UI panels look empty or inconsistent:
1. Run notebook Section 6 smoke-test cells.
2. Compare backend stage payloads directly:
   - ingestion
   - normalization
   - clustering
   - geospatial
   - aggregation
   - citation_traceability
   - warnings
3. Capture mismatch details (run ID, stage key, observed vs expected).

## 5) Evidence Capture Requirements
For each analyst validation run, capture:
- run ID
- topic and date range
- source-level statuses
- warning messages
- pass/fail per acceptance test
- screenshots of summary, timeline, map, cluster, and citation/evidence panels

## 6) Exit Criteria
Testing is accepted when:
- Colab launch works without hidden manual steps.
- Gradio UI is accessible via share URL.
- All major outputs are inspectable from UI and/or diagnostics.
- Optional Twitter token path degrades gracefully with explicit warnings.
