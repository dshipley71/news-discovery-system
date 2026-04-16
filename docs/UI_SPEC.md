# UI Specification: Analyst Dashboard (Gradio)

## Scope
This document defines the current Gradio implementation surface for analyst execution. It reflects the existing workflow path (`ingestion -> normalization -> aggregation`) plus analyst-facing derived views (cluster/citation explorer and geospatial panel) generated only from real workflow outputs.

## 1) Dashboard Layout

### 1.1 Top Control Panel
Required controls:
- `topic`
- `start_date (YYYY-MM-DD)`
- `end_date (YYYY-MM-DD)`
- `Run Workflow` button

Notes:
- Input validation is hard-fail for empty topic, invalid date format, reversed date range, date range over 30 days, and future end date.
- Dark analyst theme is default.

### 1.2 Status / Run Summary Panel
Shows:
- workflow status text
- run ID
- run date range
- article total
- cluster total
- location total
- timeline trend summary
- analyst warnings list for weak/partial outputs

### 1.3 Timeline Panel
Contains:
- daily article count plot
- peak annotation(s)
- trend summary text

Behavior:
- empty timeline state is explicitly rendered and called out in warnings.

### 1.4 Geospatial Panel
Contains:
- marker-based global map (Plotly `scatter_geo`)
- marker table for analyst validation

Map semantics:
- marker size: `article_count`
- marker color/intensity: `low|medium|high`
- uncertainty shown in hover and table
- ambiguous location count shown in table

Data behavior:
- reads geospatial markers from workflow aggregation artifact when available
- gracefully falls back to `No geospatial output returned` when absent
- never fabricates location rows

### 1.5 Cluster Explorer Panel
Contains:
- cluster summary table
- cluster selector dropdown
- cluster detail JSON
- article membership table per selected cluster

Cluster metrics surfaced:
- article count
- distinct source count
- duplicate count and ratio
- top-source ratio
- duplicate-heavy boolean flag

### 1.6 Citation / Evidence Panel
Contains:
- citation index JSON (counts by source + claim classification)
- citation records table
- evidence bundle table (`cluster -> article -> citation`)

Claim classification handling:
- uses upstream `claim_classification` when present
- otherwise derives from available article metadata (`supported|inferred|speculative`) to keep output explicitly labeled

### 1.7 Validation / Raw Output Panel
Accordion keeps full stage outputs inspectable:
- run metadata
- ingestion output
- normalization output
- aggregation output

## 2) Warning and Error Handling
The dashboard must visibly warn for:
- empty ingestion
- normalization invalid records
- missing timeline data
- missing geospatial output
- missing cluster output
- missing citation output
- speculative citation volume
- duplicate-heavy clusters

Execution failures produce:
- failed status message
- run summary warning block
- empty timeline/map visuals with explicit no-data message

## 3) Colab and Browser Compatibility
- App launch remains `demo.launch(..., share=True)`.
- UI is fully executable from browser/Colab link without CLI interaction by analysts.
- Layout uses core Gradio components supported in Colab notebooks.

## 4) Traceability Requirements (Current UI)
- Timeline, map, cluster, citation, and evidence panels must be generated from the same workflow run payload.
- Analyst can validate every summarized panel against raw outputs in the validation accordion.
- No simulated clusters/citations/geospatial markers are allowed.
