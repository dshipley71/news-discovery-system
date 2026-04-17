# Source Integration Strategy (In-Repository, Multi-Source)

## Purpose
Define how the in-repo workflow ingests multiple real sources per run while preserving attribution, traceability, and analyst-visible telemetry.

## Scope and assumptions
- All workflow execution remains inside `src/news_app/workflow.py`.
- Source enablement is driven by `config/sources.json`.
- Optional token-gated sources (X/Twitter) must degrade gracefully when credentials are missing.
- Ingestion should continue under partial source failure.

## Adapter + Registry Pattern
The ingestion stage uses a lightweight registry:
- `SOURCE_ADAPTER_REGISTRY: dict[source_id, fetcher]`
- fetcher signature: `(session, source_config, run_input, max_records) -> SourceResult`

`SourceResult` provides a uniform adapter output contract:
- `source_id`, `source_label`
- `status` (`success` | `failed` | `skipped`)
- `articles` (already normalized)
- `warnings`
- `error` (optional)
- `metadata` (source-level telemetry)

This keeps source-specific behavior isolated without introducing an external orchestrator or heavyweight plugin framework.

## Supported source behavior
1. **Reddit**
   - Primary path: JSON API (`/search.json`)
   - Shared `requests.Session` + source user-agent
   - 429-aware retry logic before fallback
   - Fallback path: RSS (`/search.rss`) if JSON path fails
2. **Google News**
   - RSS search feed ingestion
3. **Web (DuckDuckGo HTML)**
   - HTML retrieval
   - Regex extraction with 3 fallback patterns
4. **GDELT**
   - DOC 2.0 API (`mode=ArtList`, `format=json`)
   - No API key required
5. **Hacker News (Algolia)**
   - Public Algolia search API (`/api/v1/search_by_date`, `tags=story`)
   - Lightweight public/discussion source for fast signal discovery
   - No API key required
6. **X/Twitter** (optional)
   - Enabled only when `TWITTER_BEARER_TOKEN` is present
   - Missing token => `skipped` source result and run continues

## Canonical article schema
Each adapter emits records aligned to a common schema:
- `article_id`
- `title`
- `url`
- `published_at`
- `source`
- `source_label`
- `snippet` (optional)
- `author` (optional)
- `source_attribution`:
  - `source_id`
  - `source_label`
  - `external_id` (optional)
  - `raw_source` (optional)

## Ingestion telemetry contract
Ingestion output exposes:
- `sources_attempted`
- `sources_succeeded`
- `sources_failed`
- `source_runs[]` with per-source:
  - `status`
  - `article_count`
  - `warnings`
  - `error`
  - `metadata`
- `telemetry` with:
  - `per_source_article_counts`
  - `per_source_warnings`
  - `per_source_status`
  - ingestion duplicate metrics

## Early duplicate control
Before downstream normalization/analysis, ingestion applies lightweight duplicate suppression across sources:
- primary key: normalized URL
- fallback key: normalized title + publication day

This reduces cross-source duplicate inflation while preserving conservative, auditable behavior.

## Known limitations
- HTML parsing can break when upstream markup changes.
- Some RSS items have limited metadata.
- Initial duplicate suppression is intentionally simple and may miss semantic duplicates.

## 2026-04 Backend correction updates
- **Reddit is first-class and two-stage by contract:** JSON API primary, RSS fallback on both transport failure and empty primary results.
- Reddit telemetry now records primary/fallback counts, fallback reason (`json_error` or `empty_primary_result`), and final source status.
- **GDELT is required** in validation: source failure is a stop gate, not a soft warning.
- GDELT adapter now records request telemetry (`http_status`, `response_bytes`, request parameters, `error_details`) and distinguishes `failed` vs `success with empty result`.
- GDELT supports optional API key through `GDELT_API_KEY` (or source config `api_key`) while remaining functional without keys.
- Per-source hard cap defaults were raised and centralized; ingestion no longer enforces the prior low fixed cap.
