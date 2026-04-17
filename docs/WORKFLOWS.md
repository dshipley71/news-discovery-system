# Workflow Operating Manual (In-Repo Runtime)

## 1) Execution model
The analyst workflow executes entirely in-repo through a single Python entrypoint:
- `run_workflow(run_input)` in `src/news_app/workflow.py`

No external workflow engine is required for the current production MVP path.

## 2) Stage contracts
### Stage 0: Intake
- Inputs: `topic`, `start_date`, `end_date`
- Validation:
  - topic is non-empty
  - start date is not after end date

### Stage 1: Multi-source ingestion
- Inputs: run input + `config/sources.json`
- Behavior:
  - loads enabled sources
  - dispatches source adapters via in-repo registry
  - supports partial source failure (run continues when any source succeeds)
  - emits source-level telemetry for UI inspection
- Output:
  - merged `raw_hits`
  - `sources_attempted`, `sources_succeeded`, `sources_failed`
  - `source_runs` with per-source status, count, warnings, error, metadata

### Stage 2: Normalization
- Inputs: merged hits
- Behavior:
  - validates canonical fields
  - emits canonical article schema
  - preserves source attribution per record
- Output:
  - `canonical_articles`
  - `validation_issues`

### Stage 3: Aggregation
- Inputs: canonical articles
- Behavior:
  - computes day-level article counts
- Output:
  - `daily_counts`

## 3) Ingestion adapter coverage
- **Reddit:** JSON API + RSS fallback, user-agent, 429 retry
- **Google News:** RSS ingestion
- **Web:** DuckDuckGo HTML + 3-pattern regex fallback
- **GDELT:** DOC 2.0 JSON API
- **X/Twitter:** optional, skipped when `TWITTER_BEARER_TOKEN` missing

## 4) Analyst-visible run transparency
The ingestion payload must expose:
- sources attempted/succeeded/failed
- per-source article counts
- per-source warnings/errors
- per-source metadata
- duplicate metrics

These fields are required for front-end inspection and auditability.

## 5) Partial failure rules
- Source-level failures do not terminate full ingestion.
- Failed/skipped sources must be explicit in output.
- Full run is only considered failed when no source provides usable output.

## 6) Operating assumptions
- Analysts initiate and inspect runs from the UI.
- Source configuration remains in `config/sources.json`.
- Optional credentials are supplied through environment variables when needed.
