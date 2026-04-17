# Source Integration Strategy (In-Repository)

## Purpose
Define how the in-repository backend fetches, normalizes, and reports multi-source news ingestion for analyst runs.

## Source Adapter Registry
The backend uses a lightweight adapter registry in `src/news_app/workflow.py`:
- `reddit`
- `google_news`
- `web_duckduckgo`
- `gdelt`
- `twitter` (optional)

Each adapter receives:
- shared `requests.Session` (connection reuse),
- source config object,
- `RunInput` (topic/date window),
- `max_records`.

Each adapter returns `SourceResult` with:
- source ID/label,
- status (`success`, `failed`, or `skipped`),
- normalized article list,
- warning list,
- optional error text.

## Required Source Behaviors
### Reddit
- Primary: JSON API (`/search.json`)
- Fallback: RSS (`/search.rss`) when JSON path fails
- Uses explicit user-agent header
- Retries on HTTP 429 before fallback

### Google News
- RSS ingestion via Google News search feed

### Web (DuckDuckGo HTML)
- HTML fetch and regex extraction
- Three extraction patterns in fallback order

### GDELT
- DOC 2.0 JSON API (`mode=ArtList`, `format=json`)
- No API key required

### X/Twitter
- Enabled only when `TWITTER_BEARER_TOKEN` is present
- Missing token => source marked `skipped` with warning; run continues

## Normalized Article Contract
All adapters emit records normalized into one schema:
- `article_id`
- `title`
- `url`
- `published_at`
- `source`
- `source_label`
- `snippet` (optional)
- `author` (optional)
- `source_attribution` (`source_id`, `source_label`, `external_id`, `raw_source`)

## Failure Tolerance and Telemetry
Ingestion is partial-failure tolerant:
- A single source failure does not fail entire ingestion.
- Per run output includes:
  - `sources_attempted`
  - `sources_succeeded`
  - `sources_failed`
  - per-source `status`, `article_count`, `warnings`, and `error`

## Early Duplicate Control
Before downstream dedupe stages, ingestion applies key-based dedupe:
- preferred key: canonical URL
- fallback key: normalized title + publication date

Telemetry tracks:
- `ingestion_duplicate_count`
- `ingestion_duplicate_ratio`

## Assumptions
- Source endpoints stay policy-accessible.
- UI surfaces source telemetry from ingestion payload.
- Optional token-based sources can be disabled by environment without config edits.

## Known Limits
- HTML extraction may miss items when page markup changes.
- RSS feeds do not always include complete metadata.
- Initial dedupe is conservative and URL/title based only.
