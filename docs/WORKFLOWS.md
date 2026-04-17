# Workflow Operating Manual (In-Repo Execution)

## 1) Execution Model
This system executes as a single in-repository Python workflow with one entrypoint:
- `run_workflow(run_input)` in `src/news_app/workflow.py`

All ingestion and stage orchestration logic remains in-repo for analyst-facing reliability and traceability.

---

## 2) Stage Contracts
## Stage 0: Intake
- Inputs: topic, start_date, end_date
- Output: run input manifest
- Validation:
  - topic non-empty
  - start_date <= end_date

## Stage 1: Multi-Source Ingestion
- Inputs: run input + `config/sources.json`
- Behavior:
  - loads enabled sources
  - executes per-source adapters
  - keeps run alive on partial source failure
  - captures source telemetry
- Output:
  - merged raw hits
  - `sources_attempted`, `sources_succeeded`, `sources_failed`
  - per-source status/warnings/errors and count metadata

## Stage 2: Normalization
- Inputs: merged raw hits
- Behavior:
  - validates canonical fields
  - emits `canonical_articles`
  - preserves source attribution per record
- Output:
  - canonical set + validation issues

## Stage 3: Aggregation
- Inputs: canonical articles
- Behavior:
  - computes day-level article counts
- Output:
  - daily timeline buckets

---

## 3) Source Adapter Behavior
Adapters are registered by source ID and implement source-specific fetch behavior.

Current adapters:
1. Reddit: JSON API + RSS fallback, user-agent, retry on 429
2. Google News: RSS search feed
3. Web: DuckDuckGo HTML with 3-pattern extraction fallback
4. GDELT: DOC 2.0 JSON API
5. X/Twitter: optional; skipped when `TWITTER_BEARER_TOKEN` missing

---

## 4) Analyst-Visible Telemetry Requirements
The ingestion output must expose:
- attempted/success/failed source lists,
- per-source article counts,
- per-source warnings,
- source-level error details,
- ingestion duplicate metrics.

This telemetry is required for run inspection in UI panels.

---

## 5) Partial Failure Rules
- Any individual source can fail without failing full run.
- Failed/skipped sources are explicitly recorded.
- Run fails only if no usable articles are produced and no source succeeded.

---

## 6) Assumptions
- Analysts run all stages from front end.
- Source config stays in `config/sources.json`.
- Environment secrets are provided only for optional sources when needed.
