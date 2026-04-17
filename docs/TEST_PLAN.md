# UI-Executable Test Plan (Analyst Review Dashboard)

## 1) Purpose
Validate that the Gradio dashboard is operational, artifact-driven, warning-visible, and analyst-usable in browser and Colab.

## 2) Test Environment
- Launch with `python gr_app.py` (local) or Colab launch cell with `share=True`.
- Use backend workflow outputs only (`stages.*`, `artifacts.*`).
- Do not inject mock UI data.

## 3) Acceptance Tests by Dashboard Region

### AT-1 Control Panel + Theme
1. Open dashboard.
2. Confirm Theme defaults to `Dark`.
3. Switch Theme to `Light`, then back to `Dark`.
4. Enter topic + date range and run.

Expected:
- Dark is default analyst theme.
- Theme switching does not break panel layout.
- Run action remains functional after theme change.

### AT-2 Run Summary and Warnings
1. Execute normal run.
2. Confirm run summary includes run ID, date range, source totals, article totals, cluster totals, geospatial totals.
3. Confirm warnings section appears (even if only "No warnings").

Expected:
- Summary values align with payload counts.
- Partial failures are listed when any source is skipped/failed.
- No silent omission of warnings.

### AT-3 Timeline Panel + Drill-down
1. Run with data-bearing topic/date.
2. Confirm timeline chart renders daily counts.
3. Confirm peak drill-down table is populated when peaks exist.
4. Select peak day in dropdown and inspect detail JSON.

Expected:
- Peak detail maps `peak_day -> clusters -> article_ids`.
- Empty timeline shows explicit no-data message.

### AT-4 Geospatial Panel + Drill-down
1. Run with location-bearing topic/date.
2. Confirm map markers render.
3. Verify marker table shows confidence and ambiguity cues.
4. Select a location in dropdown and inspect detail JSON.

Expected:
- Location detail maps `location -> clusters -> article_ids`.
- If no geospatial artifact exists, panel shows explicit no-data state and warning.

### AT-5 Cluster Explorer
1. Confirm cluster summary table populates.
2. Select cluster and inspect detail panel + membership table.
3. Verify source diversity, top-source ratio, and duplicate-heavy indicators are present.

Expected:
- Membership rows use real article IDs from normalization payload.
- Duplicate-heavy indicator is visible where applicable.

### AT-6 Citation / Evidence Explorer
1. Confirm citation index JSON and citation records table populate.
2. Confirm evidence bundle table includes cluster/peak/location-derived bundles.
3. Compare citation row count vs `citation_index.citation_count`.

Expected:
- Citation and evidence rows are backend-artifact-derived.
- Claim classification is visible when provided.

### AT-7 Validation Panels
For each run, inspect:
- ingestion payload
- normalization payload
- aggregation payload
- cluster payload
- geospatial payload
- warning payload

Expected:
- All payload panels are visible and inspectable.
- Missing payloads are visible as empty JSON, not hidden.

### AT-8 Input Validation Hard Fail
Run invalid input cases:
- blank topic
- invalid date format
- start date > end date
- date range > 30 days
- future end date

Expected:
- status clearly reports failure reason
- run summary failure block appears
- UI remains interactive for retry

## 4) Weak/Partial Output Verification
Execute at least one sparse/weak run and verify:
- warning panel includes weakness/coverage warnings
- missing artifacts generate explicit warning entries
- empty tables/plots show explicit no-data state

## 5) Colab Compatibility Test
1. Open `notebooks/news_discovery_colab.ipynb`.
2. Launch Gradio with `share=True`.
3. Execute AT-2 through AT-7 from shared URL.

Expected:
- same panel structure as local run
- workflow fully executable in notebook-hosted UI

## 6) Evidence Capture for QA
Capture per run:
- run ID
- topic and date range
- warning messages observed
- pass/fail by acceptance test
- screenshots of summary, timeline, map, cluster, and citation panels
