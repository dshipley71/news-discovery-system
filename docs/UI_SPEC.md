# UI Specification: Analyst Review Dashboard (Gradio + Colab)

## Scope
This document defines the analyst-grade Gradio dashboard that consumes backend run artifacts directly from `run_workflow` (`stages.*` and `artifacts.*`) with no simulated core objects.

## 1) Dashboard Layout

### 1.1 Control Panel
Required controls:
- `topic`
- `start_date (YYYY-MM-DD)`
- `end_date (YYYY-MM-DD)`
- `Run Workflow`
- optional `Theme` selector (`Dark` default, optional `Light`)

Required source controls:
- Source Settings / Credentials accordion with per-source:
  - enabled/disabled toggle
  - auth mode visibility (`no_key`, `optional_key`, `required_key`)
  - credential/token input when applicable
  - explicit status table (enabled, auth mode, credential present, execution status)

Behavior:
- Dark theme is analyst-facing default.
- Light/Dark can be switched in-session.
- Input validation hard-fails for blank topic, invalid date format, reversed range, date range > 30 days, and future end date.

### 1.2 Run Summary and Warnings Panel
Displays:
- run status
- run ID
- date range
- source totals (succeeded / attempted / partial-failed)
- article totals
- cluster totals
- geospatial totals
- timeline trend summary
- analyst warnings and partial-failure warnings

Warning sources:
- `stages.warnings`
- ingestion/normalization shortfalls
- missing artifacts (timeline/map/clusters/citations)

### 1.3 Timeline Panel
Contains:
- default event-signal plot from `stages.aggregation.event_signal_timeline`
- overlay of `coverage_volume` for diagnostic comparison
- peak annotations when available
- trend summary text
- explicit drill-down table from `artifacts.evidence_bundles.peak_to_clusters_articles`
- peak detail selector and JSON detail panel
- per-day diagnostics from `stages.aggregation.daily_counts[*]`:
  - `raw_retrieved_count`
  - `duplicate_ratio`
  - `dominant_source`
  - `dominance_ratio`
  - `source_bias_detected`
  - `source_breakdown[]`
- temporal plausibility visibility:
  - `stages.aggregation.temporal_anomaly`
  - `stages.aggregation.temporal_anomaly_explanation`
- dated/undated integrity summary:
  - dated article count
  - undated article count
  - percent undated
  - primary peak excludes unknown-date buckets when known-date buckets exist

Date semantics in timeline payload:
- `published_at` (source publication field),
- `updated_at` (source update field when present),
- `retrieved_at` (fetch timestamp),
- `timeline_date_used` (publication-based day used for default trend analysis).

Drill-down path:
- `peak day -> clusters -> article IDs`
- Event lifecycle metadata (`event_id`, `first_seen_date`, `peak_date`, `last_seen_date`, `lifecycle_stage`) must be inspectable in cluster detail.

### 1.4 Geospatial Map Panel
Contains:
- marker-based Plotly map from `stages.geospatial.map_markers` (or artifact equivalent)
- marker table
- location drill-down table and location detail selector

Map semantics:
- marker size = article volume
- marker intensity/color = activity (`low|medium|high`)
- confidence cue = `avg_confidence`
- ambiguity cue = `ambiguous_count`
- location type counts in payload for future upgrades:
  - `event_location`
  - `source_location`
  - `mentioned_location`

Drill-down path:
- `location -> clusters -> article IDs`

### 1.5 Cluster Explorer
Contains:
- cluster summary table from `artifacts.cluster_artifact`
- cluster detail selector and JSON panel
- article membership table

Indicators:
- source diversity
- top-source ratio
- duplicate ratio / duplicate-heavy flag

### 1.6 Citation / Evidence Explorer
Contains:
- citation index JSON from `artifacts.citation_index`
- citation records table
- evidence bundle table derived from `artifacts.evidence_bundles`

Traceability:
- every citation row links article and cluster IDs when available
- evidence bundles expose `cluster_to_articles`, `peak_to_clusters_articles`, and `location_to_clusters_articles`
- claim classification uses backend values (`supported|inferred|speculative`)

### 1.7 Validation Panels
Accordion provides inspectable payloads:
- run metadata
- ingestion payload
- normalization payload
- aggregation payload
- cluster payload
- geospatial payload
- warning payload

### 1.8 Run Review Log Export Panel
Accordion: **Run Review Log Export (ChatGPT-ready)**.

Contains:
- markdown review summary (`stages.review_log_markdown` with artifact fallback),
- JSON review log (`stages.review_log` with artifact fallback).

Requirements:
- generated on every run (success or partial source failure),
- copyable without requiring CLI access,
- includes query metadata, source outcomes, date integrity, timeline summary, cluster summary, geospatial summary, validation/warnings, and analyst review note.

## 2) Missing/Partial Artifact Handling
Dashboard must not fail silently. Explicit warnings are rendered for:
- empty ingestion
- normalization validation loss
- source-level partial failures
- missing timeline artifact
- missing geospatial artifact
- missing cluster artifact
- missing citation artifact

All panels preserve stable empty states; no fabricated markers/clusters/citations are produced.

## 3) Colab Compatibility
- Launch path remains `python gr_app.py` or notebook cell with `demo.launch(..., share=True)`.
- UI remains fully browser/Colab usable without analyst CLI usage.
- Components are standard Gradio blocks/tables/plots suitable for Colab shared links.
