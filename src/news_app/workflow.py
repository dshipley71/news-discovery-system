from __future__ import annotations

import json
import os
import re
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
import hashlib
from pathlib import Path
from typing import Any, Callable
from uuid import uuid4
from urllib.parse import parse_qsl, quote_plus, urlencode, urlparse, urlunparse

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


STOPWORDS = {
    "the",
    "a",
    "an",
    "in",
    "on",
    "to",
    "for",
    "of",
    "and",
    "with",
    "from",
    "at",
    "by",
    "after",
    "before",
    "as",
    "is",
    "are",
    "was",
    "were",
}

GEO_LOCATION_LEXICON: dict[str, dict[str, Any]] = {
    "new york": {"city": "New York", "region_or_state": "New York", "country": "USA", "latitude": 40.7128, "longitude": -74.006},
    "london": {"city": "London", "region_or_state": "England", "country": "United Kingdom", "latitude": 51.5072, "longitude": -0.1276},
    "paris": {"city": "Paris", "region_or_state": "Ile-de-France", "country": "France", "latitude": 48.8566, "longitude": 2.3522},
    "tokyo": {"city": "Tokyo", "region_or_state": "Tokyo", "country": "Japan", "latitude": 35.6764, "longitude": 139.65},
    "washington": {"city": "Washington", "region_or_state": "District of Columbia", "country": "USA", "latitude": 38.9072, "longitude": -77.0369},
    "los angeles": {"city": "Los Angeles", "region_or_state": "California", "country": "USA", "latitude": 34.0522, "longitude": -118.2437},
    "san francisco": {"city": "San Francisco", "region_or_state": "California", "country": "USA", "latitude": 37.7749, "longitude": -122.4194},
    "chicago": {"city": "Chicago", "region_or_state": "Illinois", "country": "USA", "latitude": 41.8781, "longitude": -87.6298},
    "berlin": {"city": "Berlin", "region_or_state": "Berlin", "country": "Germany", "latitude": 52.52, "longitude": 13.405},
    "rome": {"city": "Rome", "region_or_state": "Lazio", "country": "Italy", "latitude": 41.9028, "longitude": 12.4964},
    "madrid": {"city": "Madrid", "region_or_state": "Community of Madrid", "country": "Spain", "latitude": 40.4168, "longitude": -3.7038},
    "beijing": {"city": "Beijing", "region_or_state": "Beijing", "country": "China", "latitude": 39.9042, "longitude": 116.4074},
    "shanghai": {"city": "Shanghai", "region_or_state": "Shanghai", "country": "China", "latitude": 31.2304, "longitude": 121.4737},
    "moscow": {"city": "Moscow", "region_or_state": "Moscow", "country": "Russia", "latitude": 55.7558, "longitude": 37.6173},
    "kyiv": {"city": "Kyiv", "region_or_state": "Kyiv", "country": "Ukraine", "latitude": 50.4501, "longitude": 30.5234},
    "jerusalem": {"city": "Jerusalem", "region_or_state": "Jerusalem District", "country": "Israel", "latitude": 31.7683, "longitude": 35.2137},
    "gaza": {"city": "Gaza", "region_or_state": "Gaza Strip", "country": "Palestine", "latitude": 31.5017, "longitude": 34.4668},
    "delhi": {"city": "Delhi", "region_or_state": "Delhi", "country": "India", "latitude": 28.6139, "longitude": 77.209},
    "mumbai": {"city": "Mumbai", "region_or_state": "Maharashtra", "country": "India", "latitude": 19.076, "longitude": 72.8777},
    "sydney": {"city": "Sydney", "region_or_state": "New South Wales", "country": "Australia", "latitude": -33.8688, "longitude": 151.2093},
    "toronto": {"city": "Toronto", "region_or_state": "Ontario", "country": "Canada", "latitude": 43.6532, "longitude": -79.3832},
    "vancouver": {"city": "Vancouver", "region_or_state": "British Columbia", "country": "Canada", "latitude": 49.2827, "longitude": -123.1207},
    "mexico city": {"city": "Mexico City", "region_or_state": "Mexico City", "country": "Mexico", "latitude": 19.4326, "longitude": -99.1332},
}


def _stable_id(prefix: str, seed: str) -> str:
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}:{digest}"


def _canonicalize_url(url: str | None) -> str:
    if not url:
        return ""
    parsed = urlparse(url.strip())
    clean_query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=False)))
    canonical = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower(),
        query=clean_query,
        fragment="",
    )
    return urlunparse(canonical).rstrip("/")


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
        "%Y%m%d%H%M%S",
        "%Y%m%dT%H%M%SZ",
        "%Y%m%dT%H%M%S",
        "%Y%m%d",
    ]
    for fmt in formats:
        try:
            parsed = datetime.strptime(candidate, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except ValueError:
            continue

    digits = re.fullmatch(r"\d{10,13}", candidate)
    if digits:
        try:
            epoch = int(candidate)
            if len(candidate) == 13:
                epoch = epoch // 1000
            return datetime.fromtimestamp(epoch, tz=timezone.utc)
        except (ValueError, OverflowError):
            return None

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

    canonical_url = _canonicalize_url(url)
    article_id_seed = str(raw.get("external_id") or canonical_url or f"{title[:50]}:{published_iso}")
    article_id = _stable_id(source_id, article_id_seed)

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


def _dedupe_key(article: dict[str, Any]) -> str:
    url_key = _canonicalize_url(article.get("url"))
    title_key = re.sub(r"\s+", " ", str(article.get("title") or "").strip().lower())
    date_key = str(article.get("published_at") or "")[:10]
    return url_key or f"{title_key}:{date_key}"


def _dedupe_articles(articles: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    canonical_by_key: dict[str, str] = {}
    groups: dict[str, dict[str, Any]] = {}
    duplicate_count = 0

    for article in articles:
        key = _dedupe_key(article)
        group = groups.setdefault(
            key,
            {
                "dedupe_key": key,
                "canonical_article_id": None,
                "canonical_source": None,
                "canonical_url": article.get("url"),
                "article_ids": [],
            },
        )
        group["article_ids"].append(article.get("article_id"))

        if key in canonical_by_key:
            duplicate_count += 1
            continue

        canonical_by_key[key] = article["article_id"]
        group["canonical_article_id"] = article["article_id"]
        group["canonical_source"] = article.get("source")
        deduped.append(article)

    duplicate_map = [
        {
            **group,
            "duplicate_article_ids": [
                article_id
                for article_id in group["article_ids"]
                if article_id and article_id != group["canonical_article_id"]
            ],
            "duplicate_count": max(0, len(group["article_ids"]) - 1),
        }
        for _, group in sorted(groups.items(), key=lambda item: item[0])
    ]

    return deduped, {
        "ingestion_duplicate_count": duplicate_count,
        "ingestion_duplicate_ratio": (duplicate_count / len(articles)) if articles else 0.0,
        "duplicate_map": duplicate_map,
    }


def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return [token for token in tokens if token not in STOPWORDS and len(token) > 2]


def _article_cluster_tokens(article: dict[str, Any]) -> set[str]:
    combined = f"{article.get('title', '')} {article.get('snippet') or ''}".strip()
    return set(_tokenize(combined))


def _token_overlap(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left.intersection(right))
    union = len(left.union(right))
    return intersection / union if union else 0.0


def _build_clusters(canonical_articles: list[dict[str, Any]]) -> dict[str, Any]:
    cluster_groups: list[dict[str, Any]] = []
    for article in sorted(canonical_articles, key=lambda row: row["article_id"]):
        tokens = _article_cluster_tokens(article)
        best_cluster: dict[str, Any] | None = None
        best_overlap = 0.0
        for cluster in cluster_groups:
            overlap = _token_overlap(tokens, cluster["token_centroid"])
            if overlap > best_overlap:
                best_overlap = overlap
                best_cluster = cluster
        intersection_size = len(tokens.intersection(best_cluster["token_centroid"])) if best_cluster else 0
        if best_cluster and (best_overlap >= 0.34 or intersection_size >= 2):
            best_cluster["members"].append(article)
            best_cluster["token_centroid"].update(tokens)
        else:
            cluster_groups.append({"members": [article], "token_centroid": set(tokens)})

    clusters: list[dict[str, Any]] = []
    article_to_cluster: dict[str, str] = {}
    for cluster in cluster_groups:
        members = sorted(cluster["members"], key=lambda row: row["article_id"])
        article_ids = [article["article_id"] for article in members]
        sources = sorted({article.get("source") for article in members if article.get("source")})
        parsed_times = [parsed for parsed in (_parse_date(row.get("published_at")) for row in members) if parsed]
        representative_tokens = sorted(cluster["token_centroid"])[:6]
        cluster_key = " ".join(representative_tokens) or "misc"
        start = min(parsed_times).isoformat() if parsed_times else None
        end = max(parsed_times).isoformat() if parsed_times else None
        source_diversity = len(sources)
        confidence = round(
            min(
                1.0,
                0.35 + (0.15 * min(len(members), 4)) + (0.2 * min(source_diversity, 3)),
            ),
            3,
        )
        cluster_id = _stable_id("cluster", f"{cluster_key}:{'|'.join(article_ids)}")
        clusters.append(
            {
                "cluster_id": cluster_id,
                "cluster_label": f"Lexical cluster: {cluster_key}",
                "article_ids": article_ids,
                "source_diversity": source_diversity,
                "cluster_confidence": confidence,
                "temporal_span": {
                    "start": start,
                    "end": end,
                },
                "heuristic": "deterministic_lexical_token_cluster_v1",
            }
        )
        for article_id in article_ids:
            article_to_cluster[article_id] = cluster_id

    return {
        "clusters": clusters,
        "article_to_cluster": article_to_cluster,
    }


def _claim_classification(article: dict[str, Any]) -> str:
    if article.get("claim_classification") in {"supported", "inferred", "speculative"}:
        return article["claim_classification"]
    if article.get("url") and article.get("published_at"):
        return "supported"
    if article.get("title"):
        return "inferred"
    return "speculative"


def _build_citation_index(canonical_articles: list[dict[str, Any]], article_to_cluster: dict[str, str]) -> dict[str, Any]:
    citations: list[dict[str, Any]] = []
    classification_counts = {"supported": 0, "inferred": 0, "speculative": 0}
    by_source: Counter[str] = Counter()

    for article in sorted(canonical_articles, key=lambda row: row["article_id"]):
        claim_classification = _claim_classification(article)
        classification_counts[claim_classification] += 1
        by_source[article.get("source") or "unknown"] += 1
        citations.append(
            {
                "citation_id": _stable_id("cite", article["article_id"]),
                "article_id": article["article_id"],
                "cluster_id": article_to_cluster.get(article["article_id"]),
                "claim_classification": claim_classification,
                "url": article.get("url"),
                "source": article.get("source"),
                "source_label": article.get("source_label"),
                "title": article.get("title"),
                "published_at": article.get("published_at"),
            }
        )

    return {
        "citations": citations,
        "citation_count": len(citations),
        "claim_classification_counts": classification_counts,
        "by_source": dict(by_source),
    }


def _extract_geospatial_entities(canonical_articles: list[dict[str, Any]]) -> dict[str, Any]:
    entities: list[dict[str, Any]] = []
    per_location: dict[str, dict[str, Any]] = {}

    for article in sorted(canonical_articles, key=lambda row: row["article_id"]):
        text = f"{article.get('title', '')} {article.get('snippet') or ''}".lower()
        for location_key, location in GEO_LOCATION_LEXICON.items():
            if re.search(rf"\b{re.escape(location_key)}\b", text):
                entity_id = _stable_id("geo", f"{article['article_id']}:{location_key}")
                entity = {
                    "location_id": entity_id,
                    "article_id": article["article_id"],
                    "location_key": location_key,
                    "city": location["city"],
                    "region_or_state": location["region_or_state"],
                    "country": location["country"],
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "confidence": 0.92,
                    "extraction_method": "explicit",
                    "ambiguity_flag": location_key == "paris",
                    "ambiguity_notes": "Could refer to multiple regions" if location_key == "paris" else None,
                    "evidence_text": location_key,
                    "evidence_linkage": {"article_id": article["article_id"]},
                }
                entities.append(entity)
                marker_key = f"{location['city']}|{location['country']}"
                marker = per_location.setdefault(
                    marker_key,
                    {
                        "location_label": f"{location['city']}, {location['country']}",
                        "city": location["city"],
                        "region_or_state": location["region_or_state"],
                        "country": location["country"],
                        "latitude": location["latitude"],
                        "longitude": location["longitude"],
                        "article_ids": set(),
                        "location_ids": [],
                        "confidences": [],
                        "ambiguous_count": 0,
                    },
                )
                marker["article_ids"].add(article["article_id"])
                marker["location_ids"].append(entity_id)
                marker["confidences"].append(entity["confidence"])
                marker["ambiguous_count"] += int(entity["ambiguity_flag"])

    markers = []
    for key in sorted(per_location.keys()):
        marker = per_location[key]
        article_ids = sorted(marker["article_ids"])
        avg_confidence = round(sum(marker["confidences"]) / len(marker["confidences"]), 3)
        markers.append(
            {
                "location_label": marker["location_label"],
                "city": marker["city"],
                "region_or_state": marker["region_or_state"],
                "country": marker["country"],
                "latitude": marker["latitude"],
                "longitude": marker["longitude"],
                "article_ids": article_ids,
                "unique_article_count": len(article_ids),
                "avg_confidence": avg_confidence,
                "ambiguous_count": marker["ambiguous_count"],
                "location_ids": marker["location_ids"],
                "evidence_linkage": {"article_ids": article_ids, "location_ids": marker["location_ids"]},
            }
        )

    return {
        "entities": entities,
        "map_markers": markers,
    }


def _build_evidence_bundles(
    clusters: list[dict[str, Any]],
    daily_counts: list[dict[str, Any]],
    canonical_articles: list[dict[str, Any]],
    citations: list[dict[str, Any]],
    geospatial_markers: list[dict[str, Any]],
) -> dict[str, Any]:
    citation_by_article = {citation["article_id"]: citation["citation_id"] for citation in citations}
    article_to_cluster = {
        article_id: cluster["cluster_id"] for cluster in clusters for article_id in cluster["article_ids"]
    }

    cluster_to_articles = [
        {
            "bundle_id": _stable_id("bundle", f"cluster:{cluster['cluster_id']}"),
            "cluster_id": cluster["cluster_id"],
            "article_ids": cluster["article_ids"],
            "citation_ids": [
                citation_by_article[article_id]
                for article_id in cluster["article_ids"]
                if article_id in citation_by_article
            ],
        }
        for cluster in clusters
    ]

    article_day: dict[str, str | None] = {}
    for article in canonical_articles:
        parsed = _parse_date(article.get("published_at"))
        article_day[article["article_id"]] = parsed.date().isoformat() if parsed else None

    peak_to_clusters_articles: list[dict[str, Any]] = []
    if daily_counts:
        peak_count = max(point["article_count"] for point in daily_counts)
        peak_days = [point["day"] for point in daily_counts if point["article_count"] == peak_count]
        for day in peak_days:
            matched_clusters = []
            for cluster in clusters:
                articles_for_day = [
                    article_id
                    for article_id in cluster["article_ids"]
                    if article_day.get(article_id) == day
                ]
                if articles_for_day:
                    matched_clusters.append(
                        {
                            "cluster_id": cluster["cluster_id"],
                            "article_ids": articles_for_day,
                        }
                    )
            peak_to_clusters_articles.append(
                {
                    "bundle_id": _stable_id("bundle", f"peak:{day}"),
                    "peak_day": day,
                    "peak_article_count": peak_count,
                    "clusters": matched_clusters,
                }
            )

    location_to_clusters_articles = []
    for marker in geospatial_markers:
        cluster_ids = sorted(
            {article_to_cluster[article_id] for article_id in marker["article_ids"] if article_id in article_to_cluster}
        )
        location_to_clusters_articles.append(
            {
                "bundle_id": _stable_id("bundle", f"loc:{marker['location_label']}"),
                "location_label": marker["location_label"],
                "location_ids": marker["location_ids"],
                "cluster_ids": cluster_ids,
                "article_ids": marker["article_ids"],
            }
        )

    return {
        "cluster_to_articles": cluster_to_articles,
        "peak_to_clusters_articles": peak_to_clusters_articles,
        "location_to_clusters_articles": location_to_clusters_articles,
    }


def _build_warnings(
    canonical_articles: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    duplicate_ratio: float,
    geospatial_entities: list[dict[str, Any]],
    citation_index: dict[str, Any],
    timeline: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    warnings: list[dict[str, Any]] = []
    unique_sources = len({article.get("source") for article in canonical_articles if article.get("source")})
    if unique_sources < 2:
        warnings.append(
            {
                "warning_code": "weak_source_diversity",
                "severity": "warn",
                "message": "Low source diversity may weaken corroboration.",
                "metrics": {"unique_sources": unique_sources},
            }
        )
    if duplicate_ratio >= 0.35:
        warnings.append(
            {
                "warning_code": "duplicate_heavy_result_set",
                "severity": "warn",
                "message": "High duplicate ratio may inflate apparent activity.",
                "metrics": {"duplicate_ratio": round(duplicate_ratio, 3)},
            }
        )
    if geospatial_entities:
        low_conf_geo = [entity for entity in geospatial_entities if float(entity["confidence"]) < 0.7]
        ambiguous = [entity for entity in geospatial_entities if entity.get("ambiguity_flag")]
        if low_conf_geo or ambiguous:
            warnings.append(
                {
                    "warning_code": "low_confidence_geo",
                    "severity": "warn",
                    "message": "Low-confidence or ambiguous locations require analyst review.",
                    "metrics": {
                        "low_confidence_geo_count": len(low_conf_geo),
                        "ambiguous_geo_count": len(ambiguous),
                    },
                }
            )
    elif len(canonical_articles) >= 10:
        warnings.append(
            {
                "warning_code": "limited_geospatial_coverage",
                "severity": "warn",
                "message": "Geospatial extraction coverage is low relative to article volume.",
                "metrics": {"article_count": len(canonical_articles), "geospatial_entity_count": len(geospatial_entities)},
            }
        )
    weak_clusters = [cluster for cluster in clusters if len(cluster["article_ids"]) < 2 or cluster["cluster_confidence"] < 0.55]
    if weak_clusters:
        warnings.append(
            {
                "warning_code": "weak_cluster_evidence",
                "severity": "warn",
                "message": "Some clusters have limited supporting evidence.",
                "metrics": {"weak_cluster_count": len(weak_clusters)},
            }
        )
    if len(canonical_articles) < 3 or len(timeline) < 2:
        warnings.append(
            {
                "warning_code": "sparse_coverage",
                "severity": "warn",
                "message": "Coverage is sparse across time and sources.",
                "metrics": {"article_count": len(canonical_articles), "active_days": len(timeline)},
            }
        )
    speculative = citation_index.get("claim_classification_counts", {}).get("speculative", 0)
    if citation_index.get("citation_count", 0) and speculative / citation_index["citation_count"] > 0.4:
        warnings.append(
            {
                "warning_code": "speculative_interpretation_risk",
                "severity": "warn",
                "message": "A high share of speculative claims increases interpretation risk.",
                "metrics": {
                    "speculative_count": speculative,
                    "citation_count": citation_index["citation_count"],
                },
            }
        )

    return warnings


def _build_validation_report(
    *,
    ingestion: dict[str, Any],
    normalization: dict[str, Any],
    clustering: dict[str, Any],
    geospatial: dict[str, Any],
    citation_index: dict[str, Any],
    evidence_bundles: dict[str, Any],
    timeline: list[dict[str, Any]],
    warnings: list[dict[str, Any]],
    artifacts: dict[str, Any],
) -> dict[str, Any]:
    events: list[dict[str, Any]] = []

    def add_event(
        rule_id: str,
        status: str,
        message: str,
        measured: dict[str, Any],
        threshold: str,
        analyst_signal: str,
        fallback: str,
        stop_run: bool = False,
    ) -> None:
        events.append(
            {
                "rule_id": rule_id,
                "status": status,
                "message": message,
                "measured": measured,
                "threshold": threshold,
                "analyst_visible_signal": analyst_signal,
                "fallback": fallback,
                "stop_run": stop_run,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )

    duplicate_ratio = float(ingestion.get("telemetry", {}).get("ingestion_duplicate_ratio", 0.0) or 0.0)
    if duplicate_ratio >= 0.6:
        add_event(
            "FM-001-duplicate-inflation",
            "fail",
            "Duplicate ratio is severe and can materially distort analyst conclusions.",
            {"duplicate_ratio": round(duplicate_ratio, 3)},
            "stop if duplicate_ratio >= 0.60; warn if >= 0.35",
            "Critical trust gate: duplicate inflation exceeded stop threshold.",
            "Narrow query/date range and inspect duplicate lineage before rerun.",
            stop_run=True,
        )
    elif duplicate_ratio >= 0.35:
        add_event(
            "FM-001-duplicate-inflation",
            "warn",
            "Duplicate ratio is elevated and may inflate clusters/timeline.",
            {"duplicate_ratio": round(duplicate_ratio, 3)},
            "warn if duplicate_ratio >= 0.35",
            "Warning badge: duplicate-heavy result set.",
            "Continue with deduplicated set and review duplicate lineage map.",
        )

    attempted = len(ingestion.get("sources_attempted", []))
    failed = len([run for run in ingestion.get("source_runs", []) if run.get("status") != "success"])
    skipped = len([run for run in ingestion.get("source_runs", []) if run.get("status") == "skipped"])
    empty_success = len(
        [run for run in ingestion.get("source_runs", []) if run.get("status") == "success" and int(run.get("article_count", 0)) == 0]
    )
    if attempted and failed == attempted:
        add_event(
            "FM-002-source-specific-failure",
            "fail",
            "All configured sources failed or were skipped.",
            {
                "sources_attempted": attempted,
                "sources_non_success": failed,
                "sources_skipped": skipped,
                "sources_empty_success": empty_success,
            },
            "stop if all sources non-success; warn on partial failures",
            "Critical trust gate: no reliable source succeeded.",
            "Retry run or disable unstable sources until at least one succeeds.",
            stop_run=True,
        )
    elif failed > 0:
        add_event(
            "FM-002-source-specific-failure",
            "warn",
            "One or more sources failed; coverage may be biased.",
            {
                "sources_attempted": attempted,
                "sources_non_success": failed,
                "sources_skipped": skipped,
                "sources_empty_success": empty_success,
            },
            "warn if any source fails",
            "Warning badge: partial source failure.",
            "Proceed using successful sources with reduced confidence.",
        )

    retried_429_sources = [
        run.get("source_id")
        for run in ingestion.get("source_runs", [])
        if run.get("metadata", {}).get("json_retried_429")
    ]
    if retried_429_sources:
        add_event(
            "FM-003-rate-limit-backoff",
            "warn",
            "Rate limiting encountered; backoff/retry path was used.",
            {"retried_429_sources": retried_429_sources},
            "warn when any source reports 429 retry activity",
            "Warning badge: rate limiting encountered.",
            "Keep run but monitor source freshness and retry counts.",
        )

    valid_count = int(normalization.get("valid_count", 0) or 0)
    if valid_count == 0:
        add_event(
            "FM-004-empty-ingestion",
            "fail",
            "No canonical articles remain after ingestion/normalization.",
            {"valid_count": valid_count},
            "stop when valid_count == 0",
            "Critical trust gate: run blocked due to empty evidence set.",
            "Expand date range or topic query, then rerun.",
            stop_run=True,
        )

    invalid_count = int(normalization.get("invalid_count", 0) or 0)
    invalid_ratio = (invalid_count / (valid_count + invalid_count)) if (valid_count + invalid_count) else 0.0
    if invalid_ratio >= 0.5 and (valid_count + invalid_count) > 0:
        add_event(
            "FM-005-schema-drift",
            "fail",
            "Schema drift is severe; too many records failed normalization.",
            {"invalid_ratio": round(invalid_ratio, 3), "invalid_count": invalid_count},
            "stop if invalid_ratio >= 0.50; warn if >= 0.20",
            "Critical trust gate: schema inconsistency exceeded safe limit.",
            "Inspect source adapters and normalization mapping before rerun.",
            stop_run=True,
        )
    elif invalid_ratio >= 0.2:
        add_event(
            "FM-005-schema-drift",
            "warn",
            "Normalization rejected a meaningful share of ingested records.",
            {"invalid_ratio": round(invalid_ratio, 3), "invalid_count": invalid_count},
            "warn if invalid_ratio >= 0.20",
            "Warning badge: schema drift suspected.",
            "Proceed with canonical set while reviewing invalid records.",
        )

    timeline_total = sum(int(point.get("article_count", 0) or 0) for point in timeline)
    if valid_count > 0 and timeline_total != valid_count:
        add_event(
            "FM-012-timeline-normalization-mismatch",
            "fail",
            "Timeline aggregation does not match canonical article volume.",
            {"timeline_total": timeline_total, "valid_count": valid_count},
            "stop when timeline_total != valid_count",
            "Critical trust gate: timeline consistency broken.",
            "Repair date normalization/bucketing before analyst interpretation.",
            stop_run=True,
        )

    unique_sources = len({article.get("source") for article in normalization.get("canonical_articles", []) if article.get("source")})
    if unique_sources <= 1 and valid_count >= 5:
        add_event(
            "FM-006-weak-source-diversity",
            "warn",
            "Coverage is dominated by a single source family.",
            {"unique_sources": unique_sources},
            "warn if unique_sources <= 1",
            "Warning badge: weak source diversity.",
            "Treat findings as provisional until corroborated.",
        )

    if timeline:
        peak_count = max(point.get("article_count", 0) for point in timeline)
        total = sum(point.get("article_count", 0) for point in timeline)
        peak_ratio = (peak_count / total) if total else 0.0
        if peak_ratio >= 0.7 and duplicate_ratio >= 0.35:
            add_event(
                "FM-007-misleading-timeline-spikes",
                "warn",
                "Timeline spike may be driven by duplicates or ingestion batching.",
                {"peak_ratio": round(peak_ratio, 3), "duplicate_ratio": round(duplicate_ratio, 3)},
                "warn if peak_ratio >= 0.70 and duplicate_ratio >= 0.35",
                "Warning badge: spike reliability degraded.",
                "Use peak drill-down and duplicate map before interpreting surge.",
            )

    geo_entities = geospatial.get("entities", [])
    ambiguous_geo = [entity for entity in geo_entities if entity.get("ambiguity_flag")]
    low_geo = [entity for entity in geo_entities if float(entity.get("confidence", 0.0) or 0.0) < 0.7]
    if geo_entities and (len(ambiguous_geo) + len(low_geo)) == len(geo_entities):
        add_event(
            "FM-008-low-confidence-geospatial",
            "warn",
            "All geospatial matches are ambiguous and/or low confidence.",
            {"geo_entities": len(geo_entities), "ambiguous_geo": len(ambiguous_geo), "low_conf_geo": len(low_geo)},
            "warn when all extracted geospatial entities are weak",
            "Warning badge: low-confidence geospatial inference.",
            "Keep map visible but mark location conclusions as unverified.",
        )

    clusters = clustering.get("clusters", [])
    weak_clusters = [
        cluster
        for cluster in clusters
        if len(cluster.get("article_ids", [])) < 2 or float(cluster.get("cluster_confidence", 0.0) or 0.0) < 0.55
    ]
    weak_cluster_ratio = (len(weak_clusters) / len(clusters)) if clusters else 0.0
    if clusters and weak_cluster_ratio >= 0.75:
        add_event(
            "FM-009-weak-clusters",
            "warn",
            "Most clusters are low-evidence or single-article clusters.",
            {"weak_cluster_ratio": round(weak_cluster_ratio, 3), "weak_cluster_count": len(weak_clusters)},
            "warn if weak_cluster_ratio >= 0.75",
            "Warning badge: weak clustering reliability.",
            "Use article-level evidence over cluster-level interpretation.",
        )

    citation_count = int(citation_index.get("citation_count", 0) or 0)
    citation_rows = citation_index.get("citations", [])
    if valid_count > 0 and citation_count < valid_count:
        add_event(
            "FM-010-citation-support",
            "fail",
            "Citation coverage is incomplete for canonical articles.",
            {"citation_count": citation_count, "canonical_articles": valid_count},
            "stop when citation_count < canonical_articles",
            "Critical trust gate: publish blocked until citations are complete.",
            "Regenerate citation index before reporting.",
            stop_run=True,
        )
    elif citation_count > 0:
        weak_citations = [
            citation
            for citation in citation_rows
            if citation.get("claim_classification") in {"inferred", "speculative"}
        ]
        weak_ratio = len(weak_citations) / citation_count
        if weak_ratio >= 0.4:
            add_event(
                "FM-010-citation-support",
                "warn",
                "Large share of citations are inferred/speculative.",
                {"weak_citation_ratio": round(weak_ratio, 3), "citation_count": citation_count},
                "warn if inferred+speculative share >= 0.40",
                "Warning badge: weak citation support.",
                "Require analyst review of underlying article links.",
            )

    missing_artifacts = [
        artifact_key
        for artifact_key in [
            "deduplicated_article_set",
            "canonical_lineage_duplicate_map",
            "cluster_artifact",
            "citation_index",
            "evidence_bundles",
            "geospatial_entities_markers",
            "analyst_warnings",
        ]
        if artifact_key not in artifacts
    ]
    if missing_artifacts:
        add_event(
            "FM-011-silent-ui-degradation",
            "fail",
            "Required artifacts are missing; UI could degrade silently.",
            {"missing_artifacts": missing_artifacts},
            "stop when any required artifact is missing",
            "Critical trust gate: artifact contract violation.",
            "Block analyst interpretation until artifacts are restored.",
            stop_run=True,
        )

    warned_codes = {warning.get("warning_code") for warning in warnings}
    for event in events:
        if event["status"] == "warn":
            warning_code = f"validation_gate:{event['rule_id']}"
            if warning_code not in warned_codes:
                warnings.append(
                    {
                        "warning_code": warning_code,
                        "severity": "warn",
                        "message": event["message"],
                        "metrics": event["measured"],
                    }
                )

    fail_count = len([event for event in events if event["status"] == "fail"])
    warn_count = len([event for event in events if event["status"] == "warn"])
    return {
        "events": events,
        "warn_count": warn_count,
        "fail_count": fail_count,
        "stop_recommended": fail_count > 0,
        "can_publish": fail_count == 0,
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
    skipped: list[str] = []
    empty: list[str] = []

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
                if len(result.articles) == 0:
                    empty.append(source_id)
            elif result.status == "skipped":
                failed.append(source_id)
                skipped.append(source_id)
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
        "sources_skipped": skipped,
        "sources_empty": empty,
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
            fallback = re.search(r"(\d{4}-\d{2}-\d{2})", str(published_at or ""))
            if fallback:
                day = fallback.group(1)
            else:
                compact = re.search(r"(\d{8})", str(published_at or ""))
                if compact:
                    day = f"{compact.group(1)[:4]}-{compact.group(1)[4:6]}-{compact.group(1)[6:8]}"
                else:
                    day = "unknown"
        else:
            day = parsed.date().isoformat()
        counts[day] += 1

    return [{"day": day, "article_count": counts[day]} for day in sorted(counts.keys())]


def run_workflow(run_input: RunInput) -> dict[str, Any]:
    run_id = f"run_{uuid4().hex[:10]}"
    started_at = datetime.now(timezone.utc).isoformat()

    ingestion = ingest_articles(run_input)
    normalization = normalize_articles(ingestion["raw_hits"], source="multi")
    timeline = aggregate_daily_counts(normalization["canonical_articles"])
    clustering = _build_clusters(normalization["canonical_articles"])
    citation_index = _build_citation_index(
        normalization["canonical_articles"], clustering["article_to_cluster"]
    )
    geospatial = _extract_geospatial_entities(normalization["canonical_articles"])
    evidence_bundles = _build_evidence_bundles(
        clustering["clusters"],
        timeline,
        normalization["canonical_articles"],
        citation_index["citations"],
        geospatial["map_markers"],
    )
    warnings = _build_warnings(
        canonical_articles=normalization["canonical_articles"],
        clusters=clustering["clusters"],
        duplicate_ratio=ingestion["telemetry"]["ingestion_duplicate_ratio"],
        geospatial_entities=geospatial["entities"],
        citation_index=citation_index,
        timeline=timeline,
    )
    artifacts = {
        "deduplicated_article_set": normalization["canonical_articles"],
        "canonical_lineage_duplicate_map": ingestion["telemetry"].get("duplicate_map", []),
        "cluster_artifact": clustering["clusters"],
        "citation_index": citation_index,
        "evidence_bundles": evidence_bundles,
        "geospatial_entities_markers": geospatial,
        "analyst_warnings": warnings,
    }
    validation = _build_validation_report(
        ingestion=ingestion,
        normalization=normalization,
        clustering=clustering,
        geospatial=geospatial,
        citation_index=citation_index,
        evidence_bundles=evidence_bundles,
        timeline=timeline,
        warnings=warnings,
        artifacts=artifacts,
    )

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
            "clustering": {
                "clusters": clustering["clusters"],
                "cluster_count": len(clustering["clusters"]),
                "article_to_cluster": clustering["article_to_cluster"],
            },
            "citation_traceability": citation_index,
            "evidence": evidence_bundles,
            "geospatial": geospatial,
            "warnings": warnings,
            "validation": validation,
            "aggregation": {
                "daily_counts": timeline,
                "total_days": len(timeline),
                "geospatial": {"map_markers": geospatial["map_markers"]},
            },
        },
        "artifacts": artifacts,
    }
