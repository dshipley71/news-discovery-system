from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4
from urllib.parse import quote_plus

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover
    import urllib.error
    import urllib.parse
    import urllib.request

    class _HTTPError(Exception):
        pass

    class _Response:
        def __init__(self, status_code: int, body: bytes, headers: dict[str, str]):
            self.status_code = status_code
            self._body = body
            self.headers = headers
            self.text = body.decode("utf-8", errors="replace")

        def json(self) -> dict[str, Any]:
            return json.loads(self.text)

        def raise_for_status(self) -> None:
            if self.status_code >= 400:
                raise _HTTPError(f"status={self.status_code}")

    class _Session:
        def __init__(self):
            self.headers: dict[str, str] = {}

        def get(self, url: str, params=None, headers=None, timeout: int = 20):
            final_headers = dict(self.headers)
            if headers:
                final_headers.update(headers)
            if params:
                query = urllib.parse.urlencode(params)
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}{query}"
            req = urllib.request.Request(url, headers=final_headers)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    status = getattr(resp, "status", 200)
                    body = resp.read()
                    return _Response(status, body, dict(resp.headers.items()))
            except urllib.error.HTTPError as exc:
                body = exc.read() if hasattr(exc, "read") else b""
                return _Response(exc.code, body, dict(exc.headers.items()) if exc.headers else {})

    class _RequestsShim:
        Session = _Session
        HTTPError = _HTTPError

    requests = _RequestsShim()

import xml.etree.ElementTree as ET



@dataclass(frozen=True)
class RunInput:
    topic: str
    start_date: date
    end_date: date


@dataclass
class SourceResult:
    source_id: str
    source_label: str
    status: str
    articles: list[dict[str, Any]]
    warnings: list[str]
    error: str | None = None
    metadata: dict[str, Any] | None = None


SourceFetcher = Callable[[requests.Session, dict[str, Any], RunInput, int], SourceResult]


def _load_source_configs() -> list[dict[str, Any]]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "sources.json"
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return [source for source in data.get("sources", []) if source.get("enabled", True)]


def _date_to_epoch_bounds(start_date: date, end_date: date) -> tuple[int, int]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def _parse_date(value: str | None) -> datetime | None:
    if not value:
        return None
    candidate = value.strip()
    try:
        return datetime.fromisoformat(candidate.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        pass

    formats = [
        "%a, %d %b %Y %H:%M:%S %z",
        "%Y-%m-%d %H:%M:%S",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(candidate, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    return None


def _in_date_window(value: str | None, run_input: RunInput) -> bool:
    parsed = _parse_date(value)
    if not parsed:
        return True
    return run_input.start_date <= parsed.date() <= run_input.end_date


def _safe_get_json(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
) -> dict[str, Any]:
    response = session.get(url, params=params, headers=headers, timeout=timeout)
    response.raise_for_status()
    return response.json()


def _request_with_429_retry(
    session: requests.Session,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 20,
    max_attempts: int = 3,
) -> tuple[requests.Response, dict[str, Any]]:
    wait_seconds = 1
    for attempt in range(1, max_attempts + 1):
        response = session.get(url, params=params, headers=headers, timeout=timeout)
        if response.status_code != 429:
            response.raise_for_status()
            return response, {"attempts": attempt, "retried_429": attempt > 1}
        if attempt == max_attempts:
            response.raise_for_status()
        retry_after = response.headers.get("Retry-After")
        if retry_after and retry_after.isdigit():
            wait_seconds = int(retry_after)
        # avoid sleeping in tests and keep runs responsive
        wait_seconds = min(max(wait_seconds, 1), 4)
    raise RuntimeError("429 retry loop exhausted")


def _normalize_article(source_id: str, source_label: str, raw: dict[str, Any]) -> dict[str, Any] | None:
    title = (raw.get("title") or "").strip()
    url = (raw.get("url") or "").strip()
    published_at = raw.get("published_at")

    if not title:
        return None

    parsed_date = _parse_date(published_at)
    published_iso = parsed_date.isoformat() if parsed_date else (published_at or "")

    article_id_seed = raw.get("external_id") or url or f"{title[:50]}:{published_iso}"
    article_id = f"{source_id}:{abs(hash(article_id_seed))}"

    return {
        "article_id": article_id,
        "title": title,
        "url": url or None,
        "published_at": published_iso,
        "source": source_id,
        "source_label": source_label,
        "snippet": raw.get("snippet"),
        "author": raw.get("author"),
        "source_attribution": {
            "source_id": source_id,
            "source_label": source_label,
            "external_id": raw.get("external_id"),
            "raw_source": raw.get("raw_source"),
        },
    }


def _extract_rss_items(content: str) -> list[dict[str, str]]:
    root = ET.fromstring(content)
    items: list[dict[str, str]] = []
    for item in root.findall(".//item"):
        items.append(
            {
                "title": item.findtext("title") or "",
                "url": item.findtext("link") or "",
                "published_at": item.findtext("pubDate") or "",
                "snippet": item.findtext("description") or "",
            }
        )
    return items


def fetch_reddit(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]
    warnings: list[str] = []

    headers = {"User-Agent": source.get("user_agent", "news-discovery-system/1.0")}
    json_url = source["endpoint"]
    json_params = {"q": run_input.topic, "sort": "new", "t": "all", "limit": max_records}

    try:
        response, retry_meta = _request_with_429_retry(
            session,
            json_url,
            params=json_params,
            headers=headers,
            max_attempts=int(source.get("max_attempts", 3)),
        )
        payload = response.json()
        children = payload.get("data", {}).get("children", [])
        raw_items = []
        for child in children:
            data = child.get("data", {})
            raw_items.append(
                {
                    "title": data.get("title"),
                    "url": data.get("url"),
                    "published_at": datetime.fromtimestamp(
                        data.get("created_utc", 0), tz=timezone.utc
                    ).isoformat(),
                    "external_id": data.get("id"),
                    "author": data.get("author"),
                    "snippet": data.get("selftext", "")[:280],
                    "raw_source": "reddit_json",
                }
            )
    except Exception as exc:  # fallback path on transport/rate errors
        warnings.append(f"json_api_failed:{exc}")
        retry_meta = {"attempts": 0, "retried_429": False}
        rss_response = session.get(
            source.get("rss_fallback"),
            params={"q": run_input.topic, "sort": "new"},
            headers=headers,
            timeout=20,
        )
        rss_response.raise_for_status()
        raw_items = [
            {
                **item,
                "external_id": item.get("url"),
                "raw_source": "reddit_rss",
            }
            for item in _extract_rss_items(rss_response.text)
        ]

    canonical = [
        _normalize_article(source_id, source_label, item)
        for item in raw_items
        if _in_date_window(item.get("published_at"), run_input)
    ]

    return SourceResult(
        source_id=source_id,
        source_label=source_label,
        status="success",
        articles=[item for item in canonical if item],
        warnings=warnings,
        metadata={
            "fetch_mode": "reddit_json_with_rss_fallback",
            "json_retry_attempts": retry_meta["attempts"],
            "json_retried_429": retry_meta["retried_429"],
            "used_rss_fallback": any("json_api_failed" in warning for warning in warnings),
        },
    )


def fetch_google_news(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]

    url = source["endpoint"].format(query=quote_plus(run_input.topic))
    response = session.get(url, timeout=20)
    response.raise_for_status()
    raw_items = _extract_rss_items(response.text)[:max_records]

    canonical = [
        _normalize_article(
            source_id,
            source_label,
            {
                **item,
                "external_id": item.get("url"),
                "raw_source": "google_news_rss",
            },
        )
        for item in raw_items
        if _in_date_window(item.get("published_at"), run_input)
    ]

    return SourceResult(
        source_id=source_id,
        source_label=source_label,
        status="success",
        articles=[item for item in canonical if item],
        warnings=[],
        metadata={"fetch_mode": "google_news_rss"},
    )


def fetch_web_duckduckgo(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]
    warnings: list[str] = []

    response = session.get(source["endpoint"], params={"q": run_input.topic}, timeout=20)
    response.raise_for_status()
    html = response.text

    patterns = [
        r'<a[^>]+class="result__a"[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        r'<h2[^>]*>\s*<a[^>]+href="(?P<url>[^"]+)"[^>]*>(?P<title>.*?)</a>',
        r'<a[^>]+href="(?P<url>https?://[^"]+)"[^>]*>(?P<title>[^<]{10,})</a>',
    ]

    extracted: list[dict[str, Any]] = []
    for idx, pattern in enumerate(patterns, start=1):
        matches = re.finditer(pattern, html, re.IGNORECASE | re.DOTALL)
        for match in matches:
            url = re.sub(r"&amp;", "&", match.group("url")).strip()
            title = re.sub(r"<.*?>", "", match.group("title")).strip()
            if not url or not title:
                continue
            extracted.append(
                {
                    "title": title,
                    "url": url,
                    "published_at": datetime.now(timezone.utc).isoformat(),
                    "external_id": f"pattern{idx}:{url}",
                    "raw_source": f"ddg_html_pattern_{idx}",
                }
            )
        if extracted:
            if idx > 1:
                warnings.append(f"primary_pattern_empty_used_fallback_pattern_{idx}")
            break

    canonical = [
        _normalize_article(source_id, source_label, item)
        for item in extracted[:max_records]
        if _in_date_window(item.get("published_at"), run_input)
    ]
    canonical_items = [item for item in canonical if item]

    return SourceResult(
        source_id=source_id,
        source_label=source_label,
        status="success",
        articles=canonical_items,
        warnings=warnings,
        metadata={
            "fetch_mode": "duckduckgo_html",
            "pattern_used": canonical_items[0]["source_attribution"]["raw_source"]
            if canonical_items
            else None,
        },
    )


def fetch_gdelt(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]

    payload = _safe_get_json(
        session,
        source["endpoint"],
        params={
            "query": run_input.topic,
            "mode": "ArtList",
            "format": "json",
            "maxrecords": max_records,
            "startdatetime": run_input.start_date.strftime("%Y%m%d000000"),
            "enddatetime": run_input.end_date.strftime("%Y%m%d235959"),
        },
    )

    raw_items = []
    for item in payload.get("articles", []):
        raw_items.append(
            {
                "title": item.get("title"),
                "url": item.get("url"),
                "published_at": item.get("seendate"),
                "external_id": item.get("url"),
                "source_domain": item.get("domain"),
                "raw_source": "gdelt_doc_2",
            }
        )

    canonical = [
        _normalize_article(source_id, source_label, item)
        for item in raw_items
        if _in_date_window(item.get("published_at"), run_input)
    ]

    return SourceResult(
        source_id=source_id,
        source_label=source_label,
        status="success",
        articles=[item for item in canonical if item],
        warnings=[],
        metadata={"fetch_mode": "gdelt_doc_2_json"},
    )


def fetch_twitter(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]

    token = os.getenv("TWITTER_BEARER_TOKEN")
    if not token:
        return SourceResult(
            source_id=source_id,
            source_label=source_label,
            status="skipped",
            articles=[],
            warnings=["missing_twitter_bearer_token"],
            error="TWITTER_BEARER_TOKEN not configured",
            metadata={"fetch_mode": "twitter_api_v2", "token_present": False},
        )

    payload = _safe_get_json(
        session,
        source["endpoint"],
        params={
            "query": run_input.topic,
            "max_results": min(max_records, 100),
            "tweet.fields": "created_at,author_id",
        },
        headers={"Authorization": f"Bearer {token}"},
    )

    raw_items = []
    for tweet in payload.get("data", []):
        raw_items.append(
            {
                "title": tweet.get("text", "")[:120],
                "url": f"https://twitter.com/i/web/status/{tweet.get('id')}",
                "published_at": tweet.get("created_at"),
                "external_id": tweet.get("id"),
                "author": tweet.get("author_id"),
                "snippet": tweet.get("text"),
                "raw_source": "twitter_api_v2",
            }
        )

    canonical = [
        _normalize_article(source_id, source_label, item)
        for item in raw_items
        if _in_date_window(item.get("published_at"), run_input)
    ]

    return SourceResult(
        source_id=source_id,
        source_label=source_label,
        status="success",
        articles=[item for item in canonical if item],
        warnings=[],
        metadata={"fetch_mode": "twitter_api_v2", "token_present": True},
    )


SOURCE_ADAPTER_REGISTRY: dict[str, SourceFetcher] = {
    "reddit": fetch_reddit,
    "google_news": fetch_google_news,
    "web_duckduckgo": fetch_web_duckduckgo,
    "gdelt": fetch_gdelt,
    "twitter": fetch_twitter,
}


def _dedupe_articles(articles: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    duplicate_count = 0

    for article in articles:
        url = (article.get("url") or "").strip().lower()
        title = (article.get("title") or "").strip().lower()
        date_part = (article.get("published_at") or "")[:10]
        key = url or f"{title}:{date_part}"
        if key in seen_keys:
            duplicate_count += 1
            continue
        seen_keys.add(key)
        deduped.append(article)

    return deduped, {
        "ingestion_duplicate_count": duplicate_count,
        "ingestion_duplicate_ratio": (duplicate_count / len(articles)) if articles else 0,
    }


def ingest_articles(run_input: RunInput, max_records: int = 60) -> dict[str, Any]:
    requested_at = datetime.now(timezone.utc).isoformat()
    source_configs = _load_source_configs()

    session = requests.Session()
    session.headers.update({"User-Agent": "news-discovery-system/1.0 (+analyst-workflow)"})

    all_articles: list[dict[str, Any]] = []
    source_runs: list[dict[str, Any]] = []
    attempted: list[str] = []
    succeeded: list[str] = []
    failed: list[str] = []

    for source in source_configs:
        source_id = source["id"]
        attempted.append(source_id)

        fetcher = SOURCE_ADAPTER_REGISTRY.get(source_id)
        if not fetcher:
            failed.append(source_id)
            source_runs.append(
                {
                    "source_id": source_id,
                    "source_label": source.get("label", source_id),
                    "status": "failed",
                    "article_count": 0,
                    "warnings": ["missing_source_adapter"],
                    "error": f"No source adapter registered for {source_id}",
                    "metadata": {"source_type": source.get("type")},
                }
            )
            continue

        try:
            result = fetcher(session, source, run_input, max_records)
            if result.status == "success":
                all_articles.extend(result.articles)
                succeeded.append(source_id)
            elif result.status == "skipped":
                failed.append(source_id)
            else:
                failed.append(source_id)

            source_runs.append(
                {
                    "source_id": source_id,
                    "source_label": result.source_label,
                    "status": result.status,
                    "article_count": len(result.articles),
                    "warnings": result.warnings,
                    "error": result.error,
                    "metadata": result.metadata or {},
                }
            )
        except Exception as exc:
            failed.append(source_id)
            source_runs.append(
                {
                    "source_id": source_id,
                    "source_label": source.get("label", source_id),
                    "status": "failed",
                    "article_count": 0,
                    "warnings": ["source_fetch_failed"],
                    "error": str(exc),
                    "metadata": {},
                }
            )

    deduped_articles, dedupe_meta = _dedupe_articles(all_articles)

    return {
        "requested_at": requested_at,
        "query": run_input.topic,
        "sources_attempted": attempted,
        "sources_succeeded": succeeded,
        "sources_failed": failed,
        "source_runs": source_runs,
        "raw_hits": deduped_articles,
        "hits_count": len(deduped_articles),
        "telemetry": {
            "per_source_article_counts": {
                run["source_id"]: run["article_count"] for run in source_runs
            },
            "per_source_warnings": {run["source_id"]: run["warnings"] for run in source_runs},
            "per_source_status": {run["source_id"]: run["status"] for run in source_runs},
            **dedupe_meta,
        },
    }


def normalize_articles(raw_hits: list[dict[str, Any]], source: str = "multi") -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    validation_issues: list[dict[str, Any]] = []

    for idx, hit in enumerate(raw_hits):
        missing = [
            field
            for field, value in {
                "title": hit.get("title"),
                "published_at": hit.get("published_at"),
                "source": hit.get("source") or source,
            }.items()
            if not value
        ]

        if missing:
            validation_issues.append(
                {
                    "hit_index": idx,
                    "article_id": hit.get("article_id"),
                    "missing_fields": missing,
                }
            )
            continue

        normalized = {
            "article_id": hit.get("article_id") or f"{source}:{idx}",
            "title": hit.get("title"),
            "url": hit.get("url"),
            "published_at": hit.get("published_at"),
            "source": hit.get("source") or source,
            "source_label": hit.get("source_label"),
            "snippet": hit.get("snippet"),
            "author": hit.get("author"),
            "source_attribution": hit.get("source_attribution")
            or {"source_id": hit.get("source") or source, "source_label": hit.get("source_label")},
        }
        records.append(normalized)

    return {
        "canonical_articles": records,
        "validation_issues": validation_issues,
        "valid_count": len(records),
        "invalid_count": len(validation_issues),
    }


def aggregate_daily_counts(canonical_articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()

    for article in canonical_articles:
        published_at = article.get("published_at")
        parsed = _parse_date(published_at)
        if not parsed:
            continue
        day = parsed.date().isoformat()
        counts[day] += 1

    return [{"day": day, "article_count": counts[day]} for day in sorted(counts.keys())]


def run_workflow(run_input: RunInput) -> dict[str, Any]:
    run_id = f"run_{uuid4().hex[:10]}"
    started_at = datetime.now(timezone.utc).isoformat()

    ingestion = ingest_articles(run_input)
    normalization = normalize_articles(ingestion["raw_hits"], source="multi")
    timeline = aggregate_daily_counts(normalization["canonical_articles"])

    return {
        "run_id": run_id,
        "started_at": started_at,
        "input": {
            "topic": run_input.topic,
            "start_date": run_input.start_date.isoformat(),
            "end_date": run_input.end_date.isoformat(),
        },
        "stages": {
            "ingestion": ingestion,
            "normalization": normalization,
            "aggregation": {
                "daily_counts": timeline,
                "total_days": len(timeline),
            },
        },
    }
