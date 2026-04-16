# UI-Executable Test Plan (Analyst Dashboard)

## 1) Purpose
Validate that the upgraded Gradio dashboard remains operational end-to-end, exposes required analyst panels, and handles weak/partial outputs visibly.

## 2) Required Test Environment
- Launch via `python gr_app.py` (local) or Colab launch cell with `share=True`.
- Use real workflow retrieval output only.

## 3) Core Functional Acceptance Tests

### AT-1 Happy Path Dashboard Run
1. Enter topic + valid start/end dates.
2. Run workflow.
3. Confirm status is completed and run summary is populated.
4. Confirm timeline chart renders with counts.
5. Confirm cluster explorer and citation panel populate when articles are returned.

Expected:
- no silent failure,
- all major dashboard panels render,
- raw validation accordion shows real stage outputs.

### AT-2 Empty Ingestion Handling
1. Enter topic/date range likely to return zero articles.
2. Run workflow.

Expected:
- summary warning: no articles ingested,
- timeline panel shows no-data message,
- map panel shows no-data message,
- cluster and citation tables empty but UI remains stable.

### AT-3 Input Validation Hard Fail
Run each invalid case:
- blank topic
- invalid date format
- start date after end date
- date range > 30 days
- future end date

Expected:
- status shows workflow execution failure with explicit validation reason,
- dashboard remains interactive for rerun.

### AT-4 Geospatial Partial Output Handling
1. Execute run where workflow has no geospatial markers.

Expected:
- map panel renders with explicit unavailable message,
- run summary warns that geospatial output is not available,
- no fabricated location markers appear.

### AT-5 Duplicate-Heavy Cluster Warning
1. Execute run producing duplicate titles across records.

Expected:
- cluster table shows `duplicate_ratio` and `duplicate_heavy` columns,
- run summary warning includes duplicate-heavy cluster count,
- cluster detail and membership rows remain navigable.

### AT-6 Citation and Evidence Traceability
1. After successful run, inspect citation table and evidence bundle table.
2. Select a cluster and verify corresponding article IDs appear in cluster membership.

Expected:
- citation records include source, URL (when available), and claim classification,
- evidence rows map bundle -> cluster -> article -> citation,
- citation index totals align with citation table row count.

## 4) Stage Visibility Assertions
For each run, verify UI contains inspectable stage artifacts:
- ingestion output JSON
- normalization output JSON
- aggregation output JSON
- run metadata JSON

Any missing artifact panel is a test failure.

## 5) Colab Compatibility Test
1. Open `notebooks/news_discovery_colab.ipynb`.
2. Launch Gradio with `share=True`.
3. Run AT-1 and AT-2 through shared URL.

Expected:
- dashboard loads with same panel structure,
- analyst can execute workflow without CLI.

## 6) Evidence Capture for QA
Capture per test run:
- run ID
- topic/date inputs
- pass/fail per acceptance test
- warnings observed
- screenshots of timeline/map/cluster/citation panels
