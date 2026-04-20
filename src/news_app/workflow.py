from __future__ import annotations

import json
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from email.utils import parsedate_to_datetime
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


SourceFetcher = Callable[[requests.Session, dict[str, Any], RunInput, int | None], SourceResult]


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

    # Unwrap aggregator redirects where the original URL is encoded as query param.
    if "news.google." in parsed.netloc.lower():
        query_pairs = parse_qsl(parsed.query, keep_blank_values=False)
        target_url = next((value for key, value in query_pairs if key.lower() == "url" and value), "")
        if target_url:
            return _canonicalize_url(target_url)

    tracking_query_prefixes = ("utm_",)
    tracking_query_exact = {"gclid", "fbclid", "oc", "ved", "ei", "guccounter"}
    clean_pairs = []
    for key, value in parse_qsl(parsed.query, keep_blank_values=False):
        normalized_key = key.lower()
        if normalized_key in tracking_query_exact:
            continue
        if any(normalized_key.startswith(prefix) for prefix in tracking_query_prefixes):
            continue
        clean_pairs.append((key, value))

    canonical = parsed._replace(
        scheme=parsed.scheme.lower(),
        netloc=parsed.netloc.lower().removeprefix("www."),
        query=urlencode(sorted(clean_pairs)),
        fragment="",
    )
    return urlunparse(canonical).rstrip("/")


def _load_all_source_configs() -> list[dict[str, Any]]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "sources.json"
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("sources", [])


def _load_source_configs() -> list[dict[str, Any]]:
    return [source for source in _load_all_source_configs() if source.get("enabled", True)]


def _resolve_source_settings(
    source_configs: list[dict[str, Any]],
    source_settings: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if not source_settings:
        return source_configs

    source_settings_by_id = source_settings.get("sources") if isinstance(source_settings, dict) else None
    if not isinstance(source_settings_by_id, dict):
        return source_configs

    resolved: list[dict[str, Any]] = []
    for source in source_configs:
        source_copy = dict(source)
        override = source_settings_by_id.get(source["id"])
        if isinstance(override, dict):
            if "enabled" in override:
                source_copy["enabled"] = bool(override["enabled"])
            if "credential" in override:
                source_copy["credential_override"] = str(override.get("credential") or "")
        resolved.append(source_copy)
    return resolved


def _resolve_source_credential(source: dict[str, Any]) -> tuple[str, bool]:
    override = str(source.get("credential_override") or "").strip()
    if override:
        return override, True

    env_name = source.get("credential_env") or source.get("required_env")
    if env_name:
        env_value = os.getenv(str(env_name), "").strip()
        if env_value:
            return env_value, False

    config_key = str(source.get("api_key") or "").strip()
    if config_key:
        return config_key, False
    return "", False


def get_source_settings_model() -> list[dict[str, Any]]:
    model: list[dict[str, Any]] = []
    for source in _load_all_source_configs():
        auth_mode = source.get("auth_mode", "no_key")
        credential_env = source.get("credential_env") or source.get("required_env")
        credential_value = ""
        if credential_env:
            credential_value = os.getenv(str(credential_env), "").strip()
        if not credential_value:
            credential_value = str(source.get("api_key") or "").strip()
        model.append(
            {
                "source_id": source["id"],
                "source_label": source.get("label", source["id"]),
                "enabled": bool(source.get("enabled", True)),
                "auth_mode": auth_mode,
                "status": "configured" if (auth_mode == "no_key" or bool(credential_value)) else "missing_credentials",
                "credential_present": bool(credential_value),
                "credential_env": credential_env,
            }
        )
    return model


def _date_to_epoch_bounds(start_date: date, end_date: date) -> tuple[int, int]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def _parse_date_with_diagnostics(value: Any) -> dict[str, Any]:
    if value is None:
        return {"parsed": None, "format_used": None, "error": "missing_value"}
    candidate = str(value).strip()
    if not candidate:
        return {"parsed": None, "format_used": None, "error": "empty_value"}

    iso_candidate = candidate.replace("Z", "+00:00")
    try:
        parsed_iso = datetime.fromisoformat(iso_candidate)
        if parsed_iso.tzinfo is None:
            parsed_iso = parsed_iso.replace(tzinfo=timezone.utc)
        return {"parsed": parsed_iso.astimezone(timezone.utc), "format_used": "iso8601", "error": None}
    except ValueError:
        pass

    try:
        parsed_rfc = parsedate_to_datetime(candidate)
        if parsed_rfc:
            if parsed_rfc.tzinfo is None:
                parsed_rfc = parsed_rfc.replace(tzinfo=timezone.utc)
            return {"parsed": parsed_rfc.astimezone(timezone.utc), "format_used": "rfc2822", "error": None}
    except (TypeError, ValueError):
        pass

    formats = [
        ("%Y-%m-%d %H:%M:%S", "datetime_space"),
        ("%Y/%m/%d %H:%M:%S", "datetime_slash"),
        ("%Y-%m-%d", "date_only_iso"),
        ("%Y/%m/%d", "date_only_slash"),
        ("%Y%m%d%H%M%S", "compact_datetime"),
        ("%Y%m%dT%H%M%SZ", "compact_iso_zulu"),
        ("%Y%m%dT%H%M%S", "compact_iso"),
        ("%Y%m%d", "compact_date"),
    ]
    for fmt, label in formats:
        try:
            parsed = datetime.strptime(candidate, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return {"parsed": parsed.astimezone(timezone.utc), "format_used": label, "error": None}
        except ValueError:
            continue

    digits = re.fullmatch(r"\d{10,13}", candidate)
    if digits:
        try:
            epoch = int(candidate)
            if len(candidate) == 13:
                epoch = epoch // 1000
            return {
                "parsed": datetime.fromtimestamp(epoch, tz=timezone.utc),
                "format_used": "unix_epoch",
                "error": None,
            }
        except (ValueError, OverflowError) as exc:
            return {"parsed": None, "format_used": None, "error": f"unix_epoch_parse_error:{exc}"}

    return {"parsed": None, "format_used": None, "error": f"unrecognized_date_format:{candidate[:64]}"}


def _parse_date(value: str | None) -> datetime | None:
    return _parse_date_with_diagnostics(value).get("parsed")


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
    updated_at = raw.get("updated_at")
    retrieved_at = raw.get("retrieved_at") or datetime.now(timezone.utc).isoformat()

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
        "updated_at": updated_at,
        "retrieved_at": retrieved_at,
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


def _resolve_max_records(max_records: int | None, source: dict[str, Any], default: int = 250) -> int:
    if source.get("max_records"):
        return int(source["max_records"])
    if max_records is None:
        return default
    return max(1, int(max_records))


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
    max_records: int | None,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]
    warnings: list[str] = []
    resolved_max_records = _resolve_max_records(max_records, source, default=200)

    headers = {"User-Agent": source.get("user_agent", "news-discovery-system/1.0")}
    json_url = source["endpoint"]
    resolved_max_records = _resolve_max_records(max_records, source, default=100)
    json_params = {"q": run_input.topic, "sort": "new", "t": "all", "limit": min(resolved_max_records, 100)}
    primary_items: list[dict[str, Any]] = []
    fallback_items: list[dict[str, Any]] = []
    fallback_reason: str | None = None
    retry_meta: dict[str, Any] = {"attempts": 0, "retried_429": False}

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
        for child in children:
            data = child.get("data", {})
            primary_items.append(
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
        if not primary_items:
            fallback_reason = "empty_primary_result"
            warnings.append("json_api_empty_result")
    except Exception as exc:  # fallback path on transport/rate errors
        fallback_reason = "json_error"
        warnings.append(f"json_api_failed:{exc}")

    if fallback_reason:
        rss_response = session.get(
            source.get("rss_fallback"),
            params={"q": run_input.topic, "sort": "new"},
            headers=headers,
            timeout=20,
        )
        rss_response.raise_for_status()
        fallback_items = [
            {
                **item,
                "external_id": item.get("url"),
                "raw_source": "reddit_rss",
            }
            for item in _extract_rss_items(rss_response.text)
        ]
        if not fallback_items:
            warnings.append("rss_fallback_empty_result")

    raw_items = primary_items or fallback_items

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
            "primary_result_count": len(primary_items),
            "fallback_result_count": len(fallback_items),
            "fallback_reason": fallback_reason,
            "used_rss_fallback": bool(fallback_reason),
            "final_status": "success" if raw_items else "empty",
        },
    )


def fetch_google_news(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int | None,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]

    url = source["endpoint"].format(query=quote_plus(run_input.topic))
    response = session.get(url, timeout=20)
    response.raise_for_status()
    resolved_max_records = _resolve_max_records(max_records, source, default=250)
    raw_items = _extract_rss_items(response.text)[:resolved_max_records]

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
    max_records: int | None,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]
    warnings: list[str] = []
    resolved_max_records = _resolve_max_records(max_records, source, default=100)

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
                    "published_at": None,
                    "retrieved_at": datetime.now(timezone.utc).isoformat(),
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
        for item in extracted[:resolved_max_records]
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
    max_records: int | None,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]

    resolved_max_records = _resolve_max_records(max_records, source, default=250)
    params = {
        "query": run_input.topic,
        "mode": "ArtList",
        "format": "json",
        "maxrecords": resolved_max_records,
        "startdatetime": run_input.start_date.strftime("%Y%m%d000000"),
        "enddatetime": run_input.end_date.strftime("%Y%m%d235959"),
    }
    api_key, from_override = _resolve_source_credential(source)
    if api_key:
        params["key"] = api_key

    metadata: dict[str, Any] = {
        "fetch_mode": "gdelt_doc_2_json",
        "access_mode": "configured_key" if api_key else "free_public",
        "request_params": {key: value for key, value in params.items() if key != "key"},
        "api_key_provided": bool(api_key),
        "credential_from_ui_override": from_override,
        "attempted": True,
        "succeeded": False,
        "failed": False,
        "error_detail": None,
        "http_status": None,
        "response_bytes": 0,
        "result_count": 0,
        "result_state": "failed",
    }
    warnings: list[str] = []
    try:
        response = session.get(source["endpoint"], params=params, timeout=20)
        metadata["http_status"] = response.status_code
        metadata["response_bytes"] = len(response.text.encode("utf-8", errors="ignore"))
        response.raise_for_status()
        payload = response.json()
    except Exception as exc:
        metadata["failed"] = True
        metadata["error_detail"] = str(exc)
        return SourceResult(
            source_id=source_id,
            source_label=source_label,
            status="failed",
            articles=[],
            warnings=["gdelt_request_failed"],
            error=str(exc),
            metadata=metadata,
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

    metadata["result_count"] = len(raw_items)
    if not raw_items:
        warnings.append("gdelt_empty_result")
        metadata["result_state"] = "empty"
    elif len(raw_items) < resolved_max_records:
        metadata["result_state"] = "partial"
    else:
        metadata["result_state"] = "full"
    metadata["succeeded"] = True

    return SourceResult(
        source_id=source_id,
        source_label=source_label,
        status="success",
        articles=[item for item in canonical if item],
        warnings=warnings,
        metadata=metadata,
    )


def fetch_hacker_news(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int | None,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]

    resolved_max_records = _resolve_max_records(max_records, source, default=100)
    start_epoch, end_epoch = _date_to_epoch_bounds(run_input.start_date, run_input.end_date)
    payload = _safe_get_json(
        session,
        source["endpoint"],
        params={
            "query": run_input.topic,
            "tags": "story",
            "hitsPerPage": min(resolved_max_records, 1000),
            "numericFilters": ",".join(
                [
                    f"created_at_i>={start_epoch}",
                    f"created_at_i<={end_epoch}",
                ]
            ),
        },
    )

    raw_items = []
    for hit in payload.get("hits", []):
        title = hit.get("title") or hit.get("story_title")
        url = hit.get("url") or hit.get("story_url")
        raw_items.append(
            {
                "title": title,
                "url": url,
                "published_at": hit.get("created_at"),
                "external_id": hit.get("objectID"),
                "author": hit.get("author"),
                "snippet": hit.get("comment_text"),
                "raw_source": "hacker_news_algolia",
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
        metadata={"fetch_mode": "hacker_news_algolia_search_by_date"},
    )


def fetch_twitter(
    session: requests.Session,
    source: dict[str, Any],
    run_input: RunInput,
    max_records: int | None,
) -> SourceResult:
    source_id = source["id"]
    source_label = source["label"]

    token, from_override = _resolve_source_credential(source)
    if not token:
        return SourceResult(
            source_id=source_id,
            source_label=source_label,
            status="skipped",
            articles=[],
            warnings=["missing_twitter_bearer_token"],
            error="TWITTER_BEARER_TOKEN not configured",
            metadata={"fetch_mode": "twitter_api_v2", "token_present": False, "credential_from_ui_override": from_override},
        )

    resolved_max_records = _resolve_max_records(max_records, source, default=100)
    payload = _safe_get_json(
        session,
        source["endpoint"],
        params={
            "query": run_input.topic,
            "max_results": min(resolved_max_records, 100),
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
        metadata={"fetch_mode": "twitter_api_v2", "token_present": True, "credential_from_ui_override": from_override},
    )


SOURCE_ADAPTER_REGISTRY: dict[str, SourceFetcher] = {
    "reddit": fetch_reddit,
    "google_news": fetch_google_news,
    "web_duckduckgo": fetch_web_duckduckgo,
    "gdelt": fetch_gdelt,
    "hacker_news": fetch_hacker_news,
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
        article_dt = _parse_date(article.get("published_at"))
        best_cluster: dict[str, Any] | None = None
        best_score = 0.0

        for cluster in cluster_groups:
            profile_tokens = set(token for token, _ in cluster["token_profile"].most_common(12))
            lexical_overlap = _token_overlap(tokens, profile_tokens)
            day_gap = 999
            if article_dt and cluster["latest_dt"]:
                day_gap = abs((article_dt.date() - cluster["latest_dt"].date()).days)
            temporal_score = 1.0 if day_gap <= 1 else (0.5 if day_gap <= 3 else 0.0)
            source_bonus = 0.05 if article.get("source") not in cluster["sources"] else 0.0
            score = lexical_overlap + source_bonus + (0.15 * temporal_score)
            if score > best_score:
                best_score = score
                best_cluster = cluster

        if best_cluster and best_score >= 0.35:
            best_cluster["members"].append(article)
            best_cluster["token_profile"].update(tokens)
            if article.get("source"):
                best_cluster["sources"].add(article.get("source"))
            if article_dt and (best_cluster["latest_dt"] is None or article_dt > best_cluster["latest_dt"]):
                best_cluster["latest_dt"] = article_dt
        else:
            cluster_groups.append(
                {
                    "members": [article],
                    "token_profile": Counter(tokens),
                    "sources": {article.get("source")} if article.get("source") else set(),
                    "latest_dt": article_dt,
                }
            )

    clusters: list[dict[str, Any]] = []
    article_to_cluster: dict[str, str] = {}
    for cluster in cluster_groups:
        members = sorted(cluster["members"], key=lambda row: row["article_id"])
        article_ids = [article["article_id"] for article in members]
        sources = sorted({article.get("source") for article in members if article.get("source")})
        parsed_times = [parsed for parsed in (_parse_date(row.get("published_at")) for row in members) if parsed]
        representative_tokens = [token for token, _ in cluster["token_profile"].most_common(6)]
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


def _topic_tokens(topic: str) -> set[str]:
    return set(_tokenize(topic))


def _cluster_relevance_score(cluster: dict[str, Any], canonical_by_id: dict[str, dict[str, Any]], topic_tokens: set[str]) -> float:
    if not topic_tokens:
        return 1.0
    token_pool: set[str] = set()
    for article_id in cluster.get("article_ids", []):
        article = canonical_by_id.get(article_id)
        if not article:
            continue
        token_pool.update(_article_cluster_tokens(article))
    return round(_token_overlap(token_pool, topic_tokens), 3)


def _filter_clusters_by_relevance(
    clusters: list[dict[str, Any]],
    canonical_articles: list[dict[str, Any]],
    topic: str,
    threshold: float = 0.12,
) -> tuple[list[dict[str, Any]], dict[str, str], list[dict[str, Any]]]:
    canonical_by_id = {article.get("article_id"): article for article in canonical_articles if article.get("article_id")}
    topic_tokens = _topic_tokens(topic)
    filtered: list[dict[str, Any]] = []
    article_to_cluster: dict[str, str] = {}
    excluded_clusters: list[dict[str, Any]] = []

    for cluster in clusters:
        relevance_score = _cluster_relevance_score(cluster, canonical_by_id, topic_tokens)
        updated_cluster = {**cluster, "cluster_relevance_score": relevance_score}
        if relevance_score < threshold:
            excluded_clusters.append(
                {
                    "cluster_id": cluster.get("cluster_id"),
                    "cluster_label": cluster.get("cluster_label"),
                    "cluster_relevance_score": relevance_score,
                    "threshold": threshold,
                    "article_count": len(cluster.get("article_ids", [])),
                }
            )
            continue
        filtered.append(updated_cluster)
        for article_id in cluster.get("article_ids", []):
            article_to_cluster[article_id] = cluster.get("cluster_id")
    return filtered, article_to_cluster, excluded_clusters


def _cluster_lifecycle_stage(first_seen: str | None, peak_day: str | None, last_seen: str | None, latest_day: str | None) -> str:
    if not first_seen or not peak_day or not last_seen:
        return "emerging"
    if peak_day == latest_day:
        return "peak"
    if last_seen == latest_day:
        return "post-event coverage"
    if peak_day == first_seen:
        return "declining"
    return "declining"


def _build_event_lifecycle_models(
    clusters: list[dict[str, Any]],
    canonical_articles: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, dict[str, Any]]]:
    canonical_by_id = {article.get("article_id"): article for article in canonical_articles if article.get("article_id")}
    known_days = sorted(
        {
            article.get("timeline_date_used")
            for article in canonical_articles
            if article.get("timeline_date_used") and article.get("timeline_date_used") != "unknown"
        }
    )
    latest_day = known_days[-1] if known_days else None
    enriched_clusters: list[dict[str, Any]] = []
    article_to_event: dict[str, str] = {}
    lifecycle_by_event: dict[str, dict[str, Any]] = {}

    for cluster in clusters:
        event_id = _stable_id("event", cluster.get("cluster_id") or "")
        day_counts: Counter[str] = Counter()
        for article_id in cluster.get("article_ids", []):
            article = canonical_by_id.get(article_id)
            if not article:
                continue
            day = article.get("timeline_date_used")
            if day and day != "unknown":
                day_counts[day] += 1
            article_to_event[article_id] = event_id
        if day_counts:
            first_seen = min(day_counts.keys())
            peak_date = max(day_counts.keys(), key=lambda day: (day_counts[day], day))
            last_seen = max(day_counts.keys())
        else:
            first_seen = None
            peak_date = None
            last_seen = None
        stage = _cluster_lifecycle_stage(first_seen, peak_date, last_seen, latest_day)
        lifecycle = {
            "event_id": event_id,
            "first_seen_date": first_seen,
            "peak_date": peak_date,
            "last_seen_date": last_seen,
            "lifecycle_stage": stage,
            "daily_event_signal": [{"day": day, "event_signal": count} for day, count in sorted(day_counts.items())],
        }
        lifecycle_by_event[event_id] = lifecycle
        enriched_clusters.append({**cluster, **lifecycle})
    return enriched_clusters, article_to_event, lifecycle_by_event


def _build_event_signal_timeline(
    raw_articles: list[dict[str, Any]],
    canonical_articles: list[dict[str, Any]],
    clusters: list[dict[str, Any]],
    *,
    source_bias_threshold: float = 0.7,
) -> list[dict[str, Any]]:
    day_source_raw: dict[str, Counter[str]] = defaultdict(Counter)
    day_source_canonical: dict[str, Counter[str]] = defaultdict(Counter)
    day_event_ids: dict[str, set[str]] = defaultdict(set)

    for article in raw_articles:
        source = article.get("source") or "unknown"
        parsed = _parse_date(article.get("published_at"))
        day = parsed.date().isoformat() if parsed else "unknown"
        day_source_raw[day][source] += 1

    for article in canonical_articles:
        source = article.get("source") or "unknown"
        day = article.get("timeline_date_used") or "unknown"
        day_source_canonical[day][source] += 1

    for cluster in clusters:
        event_id = cluster.get("event_id")
        first_seen = cluster.get("first_seen_date")
        if event_id and first_seen:
            day_event_ids[first_seen].add(event_id)

    all_days = sorted(
        day
        for day in (set(day_source_raw.keys()) | set(day_source_canonical.keys()) | set(day_event_ids.keys()))
        if day != "unknown"
    )
    timeline_rows: list[dict[str, Any]] = []
    for day in all_days:
        source_ids = sorted(set(day_source_raw.get(day, {}).keys()) | set(day_source_canonical.get(day, {}).keys()))
        by_source: list[dict[str, Any]] = []
        total_raw = 0
        total_canonical = 0
        for source_id in source_ids:
            raw_count = int(day_source_raw.get(day, {}).get(source_id, 0))
            canonical_count = int(day_source_canonical.get(day, {}).get(source_id, 0))
            total_raw += raw_count
            total_canonical += canonical_count
            duplicates_removed = max(0, raw_count - canonical_count)
            duplicate_ratio = (duplicates_removed / raw_count) if raw_count else 0.0
            by_source.append(
                {
                    "source": source_id,
                    "raw_retrieved_count": raw_count,
                    "canonical_count": canonical_count,
                    "duplicates_removed": duplicates_removed,
                    "duplicate_ratio": round(duplicate_ratio, 3),
                }
            )
        duplicates_removed_total = max(0, total_raw - total_canonical)
        duplicate_ratio_total = (duplicates_removed_total / total_raw) if total_raw else 0.0
        dominant = max(by_source, key=lambda row: row["canonical_count"]) if by_source else {"source": "unknown", "canonical_count": 0}
        dominance_ratio = (dominant["canonical_count"] / total_canonical) if total_canonical else 0.0
        source_bias_detected = dominance_ratio > source_bias_threshold
        timeline_rows.append(
            {
                "day": day,
                "event_signal": len(day_event_ids.get(day, set())),
                "coverage_volume": total_canonical,
                "article_count": total_canonical,
                "canonical_count": total_canonical,
                "raw_retrieved_count": total_raw,
                "duplicates_removed": duplicates_removed_total,
                "duplicate_ratio": round(duplicate_ratio_total, 3),
                "source_contribution_by_day": by_source,
                "source_breakdown": by_source,
                "dominant_source": dominant["source"],
                "dominance_ratio": round(dominance_ratio, 3),
                "source_bias_detected": source_bias_detected,
            }
        )
    return timeline_rows


def _detect_temporal_anomaly(timeline: list[dict[str, Any]], clusters: list[dict[str, Any]]) -> dict[str, Any]:
    if not timeline:
        return {"temporal_anomaly": False, "anomaly_explanation": "No timeline points available."}
    event_signal_series = [int(point.get("event_signal", 0) or 0) for point in timeline]
    coverage_series = [int(point.get("coverage_volume", point.get("canonical_count", 0)) or 0) for point in timeline]
    peak_idx = max(range(len(event_signal_series)), key=lambda idx: event_signal_series[idx])
    peak_day = timeline[peak_idx]["day"]
    increasing_after_completion = False
    post_event_clusters = [cluster for cluster in clusters if cluster.get("lifecycle_stage") == "post-event coverage"]
    for cluster in post_event_clusters:
        first_seen = cluster.get("first_seen_date")
        peak_date = cluster.get("peak_date")
        last_seen = cluster.get("last_seen_date")
        if first_seen and peak_date and last_seen and peak_date < last_seen and first_seen < peak_date:
            increasing_after_completion = True
            break
    source_bias_days = [point["day"] for point in timeline if point.get("source_bias_detected")]
    late_coverage_spike = False
    if len(coverage_series) >= 2 and coverage_series[-1] > coverage_series[0] and event_signal_series[-1] <= event_signal_series[0]:
        late_coverage_spike = True

    temporal_anomaly = increasing_after_completion or late_coverage_spike or bool(source_bias_days)
    reasons: list[str] = []
    if increasing_after_completion:
        reasons.append("increasing trend after event completion in one or more event lifecycles")
    if late_coverage_spike:
        reasons.append("coverage volume increases while event signal is flat/declining")
    if source_bias_days:
        reasons.append(f"source dominance detected on {', '.join(source_bias_days)}")
    if peak_idx > 0 and peak_idx == len(timeline) - 1 and event_signal_series[-1] > 0:
        reasons.append("peak appears at end of window; confirm event timing window")
        temporal_anomaly = True
    explanation = "; ".join(reasons) if reasons else f"No temporal anomaly detected. Peak event signal day={peak_day}."
    return {"temporal_anomaly": temporal_anomaly, "anomaly_explanation": explanation, "peak_event_signal_day": peak_day}


def _build_plot_payload(timeline: list[dict[str, Any]]) -> dict[str, Any]:
    points = [point for point in timeline if point.get("day")]
    x = [str(point.get("day")) for point in points]
    event_signal = [int(point.get("event_signal", 0) or 0) for point in points]
    coverage_volume = [int(point.get("coverage_volume", point.get("canonical_count", 0)) or 0) for point in points]
    valid = bool(x) and len(x) == len(event_signal) == len(coverage_volume)
    if not valid:
        return {
            "plot_valid": False,
            "error": "timeline_plot_payload_invalid_or_empty",
            "x": x,
            "event_signal": event_signal,
            "coverage_volume": coverage_volume,
        }
    return {
        "plot_valid": True,
        "error": None,
        "x": x,
        "event_signal": event_signal,
        "coverage_volume": coverage_volume,
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
    source_location_counts: defaultdict[str, int] = defaultdict(int)

    for article in sorted(canonical_articles, key=lambda row: row["article_id"]):
        title_text = f"{article.get('title', '')}".lower()
        snippet_text = f"{article.get('snippet') or ''}".lower()
        combined_text = f"{title_text} {snippet_text}".strip()
        for location_key, location in GEO_LOCATION_LEXICON.items():
            if re.search(rf"\b{re.escape(location_key)}\b", combined_text):
                if re.search(rf"\b{re.escape(location_key)}\b", title_text):
                    location_type = "event_location"
                elif re.search(rf"\b{re.escape(location_key)}\b", snippet_text):
                    location_type = "mentioned_location"
                else:
                    location_type = "mentioned_location"
                entity_id = _stable_id("geo", f"{article['article_id']}:{location_key}")
                entity = {
                    "location_id": entity_id,
                    "article_id": article["article_id"],
                    "location_key": location_key,
                    "location_type": location_type,
                    "city": location["city"],
                    "region_or_state": location["region_or_state"],
                    "country": location["country"],
                    "latitude": location["latitude"],
                    "longitude": location["longitude"],
                    "confidence": 0.92,
                    "extraction_method": "explicit",
                    "geocode_status": "extracted",
                    "ambiguity_flag": location_key == "paris",
                    "ambiguity_notes": "Could refer to multiple regions" if location_key == "paris" else None,
                    "evidence_text": location_key,
                    "evidence_linkage": {"article_id": article["article_id"]},
                }
                entities.append(entity)
                if location_type != "event_location":
                    continue
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

        parsed_host = urlparse(str(article.get("url") or "")).netloc.lower()
        if parsed_host:
            source_location_counts[parsed_host] += 1
            entities.append(
                {
                    "location_id": _stable_id("geo", f"{article['article_id']}:source:{parsed_host}"),
                    "article_id": article["article_id"],
                    "location_key": parsed_host,
                    "location_type": "source_location",
                    "city": None,
                    "region_or_state": None,
                    "country": None,
                    "latitude": None,
                    "longitude": None,
                    "confidence": 0.5,
                    "extraction_method": "source_domain",
                    "geocode_status": "unresolved",
                    "ambiguity_flag": False,
                    "ambiguity_notes": "Publisher location unresolved without enrichment.",
                    "evidence_text": parsed_host,
                    "evidence_linkage": {"article_id": article["article_id"], "url": article.get("url")},
                }
            )

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
        "map_marker_location_type": "event_location",
        "source_location_index": dict(source_location_counts),
        "llm_geocode_hook": {"status": "not_implemented", "notes": "Reserved for future text-to-location enrichment."},
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
    unknown_date_count = len(
        [article for article in canonical_articles if article.get("date_status") in {"missing", "parse_failed"}]
    )
    if unknown_date_count:
        warnings.append(
            {
                "warning_code": "unknown_date_articles",
                "severity": "warn",
                "message": "Some canonical articles could not be parsed into timeline dates.",
                "metrics": {"unknown_date_count": unknown_date_count, "article_count": len(canonical_articles)},
            }
        )
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
    biased_days = [point.get("day") for point in timeline if point.get("source_bias_detected")]
    if biased_days:
        warnings.append(
            {
                "warning_code": "source_bias_detected",
                "severity": "warn",
                "message": "Single-source dominance detected on one or more timeline days.",
                "metrics": {"biased_days": biased_days, "day_count": len(biased_days)},
            }
        )
    if len(timeline) >= 2:
        first_signal = int(timeline[0].get("event_signal", 0) or 0)
        last_signal = int(timeline[-1].get("event_signal", 0) or 0)
        first_coverage = int(timeline[0].get("coverage_volume", timeline[0].get("article_count", 0)) or 0)
        last_coverage = int(timeline[-1].get("coverage_volume", timeline[-1].get("article_count", 0)) or 0)
        if last_coverage > first_coverage and last_signal <= first_signal:
            warnings.append(
                {
                    "warning_code": "temporal_anomaly",
                    "severity": "warn",
                    "message": "Coverage rises while event signal remains flat/declines.",
                    "metrics": {
                        "event_signal_first": first_signal,
                        "event_signal_last": last_signal,
                        "coverage_first": first_coverage,
                        "coverage_last": last_coverage,
                    },
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

    gdelt_run = next((run for run in ingestion.get("source_runs", []) if run.get("source_id") == "gdelt"), None)
    if gdelt_run and gdelt_run.get("status") != "success":
        add_event(
            "FM-013-required-gdelt-source",
            "fail",
            "Required GDELT source did not complete successfully.",
            {"gdelt_status": gdelt_run.get("status"), "gdelt_error": gdelt_run.get("error")},
            "stop when gdelt status is not success",
            "Critical trust gate: required source missing.",
            "Inspect GDELT telemetry and retry after correcting request/parsing path.",
            stop_run=True,
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

    undated_count = int(normalization.get("undated_article_count", 0) or 0)
    if undated_count == 0 and normalization.get("canonical_articles"):
        undated_count = len(
            [
                article
                for article in normalization.get("canonical_articles", [])
                if article.get("date_status") in {"missing", "parse_failed"}
            ]
        )
    undated_ratio = (undated_count / valid_count) if valid_count else 0.0
    if undated_ratio >= 0.5:
        add_event(
            "FM-016-excessive-undated-articles",
            "fail",
            "Undated article share is too high for trustworthy timeline interpretation.",
            {"undated_article_count": undated_count, "valid_count": valid_count, "percent_undated": round(undated_ratio, 3)},
            "stop if undated_ratio >= 0.50; warn if >= 0.20",
            "Critical trust gate: excessive undated coverage.",
            "Improve source date extraction before publish.",
            stop_run=True,
        )
    elif undated_ratio >= 0.2:
        add_event(
            "FM-016-excessive-undated-articles",
            "warn",
            "Undated article share is elevated and may blur timeline peaks.",
            {"undated_article_count": undated_count, "valid_count": valid_count, "percent_undated": round(undated_ratio, 3)},
            "warn if undated_ratio >= 0.20",
            "Warning badge: elevated undated article share.",
            "Proceed with caution and inspect undated bucket.",
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
        peak_candidates = timeline
        peak_count = max(point.get("article_count", 0) for point in peak_candidates)
        total = sum(point.get("article_count", 0) for point in timeline)
        peak_days = [point.get("day") for point in peak_candidates if point.get("article_count", 0) == peak_count]
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

        event_first = int(timeline[0].get("event_signal", 0) or 0)
        event_last = int(timeline[-1].get("event_signal", 0) or 0)
        coverage_first = int(timeline[0].get("coverage_volume", timeline[0].get("article_count", 0)) or 0)
        coverage_last = int(timeline[-1].get("coverage_volume", timeline[-1].get("article_count", 0)) or 0)
        source_bias_days = [point.get("day") for point in timeline if point.get("source_bias_detected")]
        if (coverage_last > coverage_first and event_last <= event_first) or source_bias_days:
            add_event(
                "FM-017-temporal-plausibility-anomaly",
                "warn",
                "Coverage trend is temporally implausible for event lifecycle progression.",
                {
                    "event_signal_first": event_first,
                    "event_signal_last": event_last,
                    "coverage_first": coverage_first,
                    "coverage_last": coverage_last,
                    "source_bias_days": source_bias_days,
                },
                "warn if coverage rises while event signal is flat/declining or source bias dominates peak days",
                "Warning badge: temporal anomaly detected.",
                "Interpret timeline using event signal and inspect source-contribution diagnostics.",
            )
    elif valid_count > 0 and undated_count == valid_count:
        add_event(
            "FM-014-unknown-date-peak",
            "fail",
            "No successfully dated articles are available for timeline peak analysis.",
            {"dated_article_count": 0, "undated_article_count": undated_count},
            "stop when all canonical articles are undated",
            "Critical trust gate: timeline dating integrity failed.",
            "Review date parsing and source fields before publishing.",
            stop_run=True,
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
    event_location_entities = [entity for entity in geo_entities if entity.get("location_type") == "event_location"]
    if valid_count >= 5 and not event_location_entities:
        add_event(
            "FM-015-missing-event-geospatial",
            "fail",
            "Geospatial extraction did not produce event locations for mapping.",
            {"valid_count": valid_count, "geo_entities": len(geo_entities)},
            "stop when event_location coverage is empty for non-trivial runs",
            "Critical trust gate: map semantics are not trustworthy.",
            "Adjust extraction rules before relying on map outputs.",
            stop_run=True,
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


def _source_settings_state(source_run: dict[str, Any]) -> str:
    metadata = source_run.get("metadata") or {}
    status = source_run.get("status")
    auth_mode = metadata.get("auth_mode", "no_key")
    credential_present = bool(metadata.get("credential_present"))

    if status == "skipped":
        return "skipped"
    if status == "failed":
        return "failed"
    if auth_mode == "no_key":
        return "no key needed"
    if auth_mode == "optional_key" and not credential_present:
        return "optional key not set"
    if auth_mode == "required_key" and credential_present:
        return "required key configured"
    return "no key needed"


def _normalized_source_status(status: str) -> str:
    normalized = {
        "success": "succeeded",
        "failed": "failed",
        "skipped": "skipped",
        "partial": "partial",
        "empty": "empty",
    }
    return normalized.get(status, status)


def _timeline_trend_direction(event_signal_timeline: list[dict[str, Any]]) -> str:
    if len(event_signal_timeline) < 2:
        return "flat"
    first_signal = int(event_signal_timeline[0].get("event_signal", 0) or 0)
    last_signal = int(event_signal_timeline[-1].get("event_signal", 0) or 0)
    if last_signal > first_signal:
        return "increasing"
    if last_signal < first_signal:
        return "decreasing"
    return "flat"


def _build_run_review_log(
    *,
    run_id: str,
    started_at: str,
    run_input: RunInput,
    ingestion: dict[str, Any],
    normalization: dict[str, Any],
    lifecycle_clusters: list[dict[str, Any]],
    event_signal_timeline: list[dict[str, Any]],
    geospatial: dict[str, Any],
    warnings: list[dict[str, Any]],
    validation: dict[str, Any],
) -> dict[str, Any]:
    source_runs = ingestion.get("source_runs", [])
    telemetry = ingestion.get("telemetry", {})
    dated_count = sum(
        1
        for article in normalization.get("canonical_articles", [])
        if article.get("timeline_date_used") not in {None, "unknown"}
    )
    undated_count = int(normalization.get("undated_article_count", 0) or 0)
    valid_count = int(normalization.get("valid_count", 0) or 0)
    percent_undated = round((undated_count / valid_count), 3) if valid_count else 0.0

    source_summary: list[dict[str, Any]] = []
    for run in source_runs:
        metadata = run.get("metadata") or {}
        source_summary.append(
            {
                "source_id": run.get("source_id"),
                "source_label": run.get("source_label"),
                "source_class": metadata.get("source_type"),
                "status": _normalized_source_status(run.get("status", "unknown")),
                "articles_returned": int(run.get("article_count", 0) or 0),
                "fallback_used": bool(metadata.get("used_rss_fallback", False)),
                "error_detail": run.get("error"),
                "retry_count": int(metadata.get("json_retry_attempts", 0) or 0),
            }
        )
    source_summary = sorted(source_summary, key=lambda item: str(item.get("source_id") or ""))

    source_settings_state = sorted(
        [
            {
                "source_id": run.get("source_id"),
                "source_label": run.get("source_label"),
                "state": _source_settings_state(run),
            }
            for run in source_runs
        ],
        key=lambda item: str(item.get("source_id") or ""),
    )

    peak_point = (
        max(event_signal_timeline, key=lambda point: int(point.get("event_signal", 0) or 0))
        if event_signal_timeline
        else None
    )
    timeline_source_by_day = [
        {
            "day": point.get("day"),
            "source_breakdown": point.get("source_breakdown", []),
        }
        for point in event_signal_timeline
    ]

    top_clusters = sorted(
        lifecycle_clusters,
        key=lambda cluster: (
            -len(cluster.get("article_ids", [])),
            -float(cluster.get("cluster_confidence", 0.0) or 0.0),
            str(cluster.get("cluster_id") or ""),
        ),
    )[:5]
    weak_clusters = [
        cluster
        for cluster in lifecycle_clusters
        if len(cluster.get("article_ids", [])) < 2 or float(cluster.get("cluster_confidence", 0.0) or 0.0) < 0.55
    ]

    map_markers = geospatial.get("map_markers", [])
    top_locations = sorted(
        map_markers,
        key=lambda marker: (
            -int(marker.get("article_count", 0) or 0),
            str(marker.get("location_label") or ""),
        ),
    )[:5]
    geo_entities = geospatial.get("entities", [])
    low_conf_geo_count = sum(1 for entity in geo_entities if float(entity.get("confidence", 0.0) or 0.0) < 0.7)
    location_type_counts = dict(Counter(entity.get("location_type") or "unknown" for entity in geo_entities))
    validation_events = validation.get("events", [])
    warning_events = [event for event in validation_events if event.get("status") == "warn"]
    fail_events = [event for event in validation_events if event.get("status") == "fail"]
    partial_failures = [
        item for item in source_summary if item.get("status") in {"failed", "skipped", "partial", "empty"}
    ]

    analyst_note_credible = "Cross-source coverage exists with dated timeline points."
    analyst_note_weak = "Signal is sparse or concentrated; interpret trends cautiously."
    analyst_note_review = "Review warning gates, low-confidence geospatial points, and partial source failures."
    if len(ingestion.get("sources_succeeded", [])) <= 1:
        analyst_note_credible = "At least one source returned data, but corroboration is limited."
    if low_conf_geo_count == 0 and map_markers:
        analyst_note_weak = "Geospatial extraction appears consistent for mapped points."
    if not warning_events and not fail_events and not partial_failures:
        analyst_note_review = "No validation gates fired; spot-check top clusters and citations before publishing."

    return {
        "query_metadata": {
            "run_id": run_id,
            "topic": run_input.topic,
            "start_date": run_input.start_date.isoformat(),
            "end_date": run_input.end_date.isoformat(),
            "execution_timestamp": started_at,
            "enabled_sources": sorted(ingestion.get("sources_attempted", [])),
            "source_settings_state": source_settings_state,
        },
        "source_retrieval_summary": source_summary,
        "date_integrity_summary": {
            "total_ingested": int(ingestion.get("hits_count", 0) or 0),
            "total_valid": valid_count,
            "dated_count": dated_count,
            "undated_count": undated_count,
            "percent_undated": percent_undated,
            "parse_failed_count": int(normalization.get("date_status_counts", {}).get("parse_failed", 0) or 0),
            "missing_date_count": int(normalization.get("date_status_counts", {}).get("missing", 0) or 0),
        },
        "timeline_summary": {
            "active_days": len(event_signal_timeline),
            "total_article_instances": int(telemetry.get("raw_retrieved_count", 0) or 0),
            "peak_day": peak_point.get("day") if peak_point else None,
            "peak_count": int(peak_point.get("event_signal", 0) or 0) if peak_point else 0,
            "trend_direction": _timeline_trend_direction(event_signal_timeline),
            "timeline_basis": "event signal" if event_signal_timeline else "raw article count",
            "source_contribution_by_day": timeline_source_by_day,
        },
        "cluster_summary": {
            "cluster_count": len(lifecycle_clusters),
            "weak_cluster_count": len(weak_clusters),
            "top_clusters": [
                {
                    "cluster_id": cluster.get("cluster_id"),
                    "cluster_label": cluster.get("cluster_label"),
                    "article_count": len(cluster.get("article_ids", [])),
                    "source_diversity": int(cluster.get("source_diversity", 0) or 0),
                    "confidence": float(cluster.get("cluster_confidence", 0.0) or 0.0),
                    "first_seen_date": cluster.get("first_seen_date"),
                    "peak_date": cluster.get("peak_date"),
                }
                for cluster in top_clusters
            ],
        },
        "geospatial_summary": {
            "map_marker_count": len(map_markers),
            "location_type_counts": location_type_counts,
            "low_confidence_geo_count": low_conf_geo_count,
            "top_locations": [
                {
                    "label": marker.get("location_label"),
                    "article_count": int(marker.get("article_count", 0) or 0),
                    "confidence": float(marker.get("avg_confidence", 0.0) or 0.0),
                    "location_type": marker.get("location_type"),
                }
                for marker in top_locations
            ],
        },
        "validation_and_warnings": {
            "can_publish": bool(validation.get("can_publish", True)),
            "warn_count": int(validation.get("warn_count", 0) or 0),
            "fail_count": int(validation.get("fail_count", 0) or 0),
            "warnings": [
                {
                    "warning_code": warning.get("warning_code"),
                    "severity": warning.get("severity"),
                    "message": warning.get("message"),
                    "metrics": warning.get("metrics"),
                }
                for warning in warnings
            ],
            "validation_gates": [
                {
                    "rule_id": event.get("rule_id"),
                    "status": event.get("status"),
                    "message": event.get("message"),
                }
                for event in validation_events
            ],
            "partial_source_failures": partial_failures,
        },
        "analyst_review_note": {
            "credible_signals": analyst_note_credible,
            "weak_signals": analyst_note_weak,
            "needs_review": analyst_note_review,
        },
    }


def _render_run_review_markdown(review_log: dict[str, Any]) -> str:
    query = review_log.get("query_metadata", {})
    date_integrity = review_log.get("date_integrity_summary", {})
    timeline = review_log.get("timeline_summary", {})
    cluster = review_log.get("cluster_summary", {})
    geospatial = review_log.get("geospatial_summary", {})
    validation = review_log.get("validation_and_warnings", {})
    analyst_note = review_log.get("analyst_review_note", {})
    top_clusters = cluster.get("top_clusters", [])
    top_locations = geospatial.get("top_locations", [])
    partial_sources = validation.get("partial_source_failures", [])

    cluster_lines = "\n".join(
        [
            f"- `{item.get('cluster_id')}` {item.get('cluster_label')} | articles={item.get('article_count')} | sources={item.get('source_diversity')} | confidence={item.get('confidence'):.2f}"
            for item in top_clusters
        ]
    ) or "- none"
    location_lines = "\n".join(
        [
            f"- {item.get('label')} | articles={item.get('article_count')} | confidence={item.get('confidence'):.2f} | type={item.get('location_type')}"
            for item in top_locations
        ]
    ) or "- none"
    partial_source_lines = "\n".join(
        [
            f"- {item.get('source_id')} ({item.get('status')}), articles={item.get('articles_returned')}, error={item.get('error_detail') or 'none'}"
            for item in partial_sources
        ]
    ) or "- none"

    return (
        "## Run Review Artifact\n"
        f"- **Run ID:** `{query.get('run_id')}`\n"
        f"- **Topic:** {query.get('topic')}\n"
        f"- **Date range:** `{query.get('start_date')} → {query.get('end_date')}`\n"
        f"- **Executed at:** `{query.get('execution_timestamp')}`\n"
        f"- **Enabled sources:** {', '.join(query.get('enabled_sources', [])) or 'none'}\n\n"
        "### Date Integrity\n"
        f"- Total ingested: {date_integrity.get('total_ingested', 0)}\n"
        f"- Total valid: {date_integrity.get('total_valid', 0)}\n"
        f"- Dated: {date_integrity.get('dated_count', 0)} | Undated: {date_integrity.get('undated_count', 0)} ({float(date_integrity.get('percent_undated', 0.0) or 0.0):.1%})\n"
        f"- Parse failed: {date_integrity.get('parse_failed_count', 0)} | Missing date: {date_integrity.get('missing_date_count', 0)}\n\n"
        "### Timeline\n"
        f"- Active days: {timeline.get('active_days', 0)}\n"
        f"- Peak day: {timeline.get('peak_day')} (count={timeline.get('peak_count', 0)})\n"
        f"- Trend direction: {timeline.get('trend_direction')}\n"
        f"- Basis: {timeline.get('timeline_basis')}\n\n"
        "### Clusters\n"
        f"- Cluster count: {cluster.get('cluster_count', 0)} | Weak clusters: {cluster.get('weak_cluster_count', 0)}\n"
        f"{cluster_lines}\n\n"
        "### Geospatial\n"
        f"- Map markers: {geospatial.get('map_marker_count', 0)} | Low-confidence geo: {geospatial.get('low_confidence_geo_count', 0)}\n"
        f"{location_lines}\n\n"
        "### Validation and Warnings\n"
        f"- can_publish: `{validation.get('can_publish', True)}` | warn={validation.get('warn_count', 0)} | fail={validation.get('fail_count', 0)}\n"
        f"- Partial source failures:\n{partial_source_lines}\n\n"
        "### Analyst Review Note\n"
        f"- **Credible:** {analyst_note.get('credible_signals', '')}\n"
        f"- **Weak:** {analyst_note.get('weak_signals', '')}\n"
        f"- **Needs review:** {analyst_note.get('needs_review', '')}\n"
    )


def ingest_articles(
    run_input: RunInput,
    max_records: int | None = None,
    source_settings: dict[str, Any] | None = None,
) -> dict[str, Any]:
    requested_at = datetime.now(timezone.utc).isoformat()
    source_configs = _resolve_source_settings(_load_all_source_configs(), source_settings)

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
        if not source.get("enabled", True):
            continue
        source_id = source["id"]
        attempted.append(source_id)
        auth_mode = source.get("auth_mode", "no_key")

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

        credential_value, credential_from_override = _resolve_source_credential(source)
        if auth_mode == "required_key" and not credential_value:
            skipped.append(source_id)
            source_runs.append(
                {
                    "source_id": source_id,
                    "source_label": source.get("label", source_id),
                    "status": "skipped",
                    "article_count": 0,
                    "warnings": ["missing_required_credentials"],
                    "error": f"Missing required credentials for source '{source_id}'",
                    "metadata": {
                        "auth_mode": auth_mode,
                        "credential_present": False,
                        "credential_from_ui_override": credential_from_override,
                    },
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
                    "metadata": {
                        "auth_mode": auth_mode,
                        "credential_present": bool(credential_value),
                        "credential_from_ui_override": credential_from_override,
                        **(result.metadata or {}),
                    },
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
                    "metadata": {
                        "auth_mode": auth_mode,
                        "credential_present": bool(credential_value),
                        "credential_from_ui_override": credential_from_override,
                    },
                }
            )

    deduped_articles, dedupe_meta = _dedupe_articles(all_articles)
    per_source_telemetry = {
        run["source_id"]: {
            "attempted": run["source_id"] in attempted,
            "succeeded": run["status"] == "success",
            "failed": run["status"] == "failed",
            "skipped": run["status"] == "skipped",
            "article_count": run["article_count"],
            "auth_mode": (run.get("metadata") or {}).get("auth_mode"),
            "credential_present": bool((run.get("metadata") or {}).get("credential_present")),
            "error_detail": run.get("error"),
            "fallback_used": bool((run.get("metadata") or {}).get("used_rss_fallback")),
        }
        for run in source_runs
    }

    return {
        "requested_at": requested_at,
        "query": run_input.topic,
        "sources_attempted": attempted,
        "sources_succeeded": succeeded,
        "sources_failed": failed,
        "sources_skipped": skipped,
        "sources_empty": empty,
        "source_runs": source_runs,
        "raw_hits": all_articles,
        "deduplicated_hits": deduped_articles,
        "hits_count": len(deduped_articles),
        "telemetry": {
            "per_source_article_counts": {
                run["source_id"]: run["article_count"] for run in source_runs
            },
            "per_source_warnings": {run["source_id"]: run["warnings"] for run in source_runs},
            "per_source_status": {run["source_id"]: run["status"] for run in source_runs},
            "per_source_telemetry": per_source_telemetry,
            "raw_retrieved_count": len(all_articles),
            "deduplicated_count": len(deduped_articles),
            **dedupe_meta,
        },
    }


def normalize_articles(raw_hits: list[dict[str, Any]], source: str = "multi") -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    validation_issues: list[dict[str, Any]] = []
    date_status_counts: Counter[str] = Counter()
    per_source_date_quality: dict[str, Counter[str]] = defaultdict(Counter)
    fallback_date_fields = [
        "published_day",
        "date",
        "date_published",
        "created_at",
        "pubDate",
        "seendate",
    ]

    for idx, hit in enumerate(raw_hits):
        missing = [
            field
            for field, value in {
                "title": hit.get("title"),
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

        source_id = hit.get("source") or source
        published_at_raw = hit.get("published_at")
        date_source_field = "published_at"
        parse_result = _parse_date_with_diagnostics(published_at_raw)
        parsed_published_at = parse_result.get("parsed")
        date_status = "parsed"
        date_parse_error = parse_result.get("error")
        date_parse_format_used = parse_result.get("format_used")

        if published_at_raw is None or not str(published_at_raw).strip():
            date_status = "missing"
            date_parse_error = "missing_published_at"
            parsed_published_at = None
            date_parse_format_used = None

            for candidate_field in fallback_date_fields:
                if candidate_field not in hit:
                    continue
                candidate_parse = _parse_date_with_diagnostics(hit.get(candidate_field))
                if candidate_parse.get("parsed"):
                    parsed_published_at = candidate_parse["parsed"]
                    date_source_field = candidate_field
                    date_parse_format_used = candidate_parse.get("format_used")
                    date_parse_error = None
                    date_status = "fallback_derived"
                    break
                if hit.get(candidate_field):
                    date_source_field = candidate_field
                    date_parse_error = candidate_parse.get("error")
        elif not parsed_published_at:
            date_status = "parse_failed"

        normalized = {
            "article_id": hit.get("article_id") or f"{source}:{idx}",
            "title": hit.get("title"),
            "url": hit.get("url"),
            "published_at": published_at_raw,
            "updated_at": hit.get("updated_at"),
            "retrieved_at": hit.get("retrieved_at"),
            "published_at_parsed": parsed_published_at.isoformat() if parsed_published_at else None,
            "published_day": parsed_published_at.date().isoformat() if parsed_published_at else "unknown",
            "timeline_date_used": parsed_published_at.date().isoformat() if parsed_published_at else "unknown",
            "timeline_date_source": date_source_field if parsed_published_at else "unknown",
            "date_status": date_status,
            "date_source_field": date_source_field,
            "date_parse_format_used": date_parse_format_used,
            "date_parse_error": date_parse_error,
            "source": source_id,
            "source_label": hit.get("source_label"),
            "snippet": hit.get("snippet"),
            "author": hit.get("author"),
            "source_attribution": hit.get("source_attribution")
            or {"source_id": source_id, "source_label": hit.get("source_label")},
        }
        date_status_counts[date_status] += 1
        per_source_date_quality[source_id]["total_articles"] += 1
        per_source_date_quality[source_id][f"{date_status}_dates"] += 1
        records.append(normalized)

    source_date_quality: dict[str, dict[str, Any]] = {}
    for source_id, counter in per_source_date_quality.items():
        total = int(counter.get("total_articles", 0))
        parsed = int(counter.get("parsed_dates", 0))
        parse_failed = int(counter.get("parse_failed_dates", 0))
        missing = int(counter.get("missing_dates", 0))
        fallback_derived = int(counter.get("fallback_derived_dates", 0))
        undated = parse_failed + missing
        source_date_quality[source_id] = {
            "total_articles": total,
            "parsed_dates": parsed,
            "parse_failures": parse_failed,
            "missing_dates": missing,
            "fallback_derived_dates": fallback_derived,
            "undated_articles": undated,
            "percent_undated": round((undated / total), 3) if total else 0.0,
        }

    return {
        "canonical_articles": records,
        "validation_issues": validation_issues,
        "valid_count": len(records),
        "invalid_count": len(validation_issues),
        "date_status_counts": dict(date_status_counts),
        "undated_article_count": len(
            [record for record in records if record.get("date_status") in {"missing", "parse_failed"}]
        ),
        "source_date_quality": source_date_quality,
    }


def aggregate_daily_counts(canonical_articles: list[dict[str, Any]], include_undated: bool = False) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()

    for article in canonical_articles:
        day = article.get("timeline_date_used") or article.get("published_day")
        if not day:
            parsed = _parse_date(article.get("published_at"))
            day = parsed.date().isoformat() if parsed else "unknown"
        if day == "unknown" and not include_undated:
            continue
        counts[day] += 1

    return [{"day": day, "article_count": counts[day]} for day in sorted(counts.keys())]


def _aggregate_cluster_daily_counts(
    clusters: list[dict[str, Any]], canonical_articles: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    canonical_by_id = {article.get("article_id"): article for article in canonical_articles if article.get("article_id")}
    cluster_counts: Counter[str] = Counter()
    for cluster in clusters:
        days = [
            canonical_by_id[article_id].get("timeline_date_used")
            for article_id in (cluster.get("article_ids") or [])
            if article_id in canonical_by_id and canonical_by_id[article_id].get("timeline_date_used") not in {None, "unknown"}
        ]
        if not days:
            continue
        cluster_counts[min(days)] += 1
    return [{"day": day, "cluster_count": cluster_counts[day]} for day in sorted(cluster_counts.keys())]


def _build_timeline_breakdown(
    raw_articles: list[dict[str, Any]],
    canonical_articles: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    day_source_raw: dict[str, Counter[str]] = defaultdict(Counter)
    day_source_canonical: dict[str, Counter[str]] = defaultdict(Counter)

    for article in raw_articles:
        source = article.get("source") or "unknown"
        parsed = _parse_date(article.get("published_at"))
        day = parsed.date().isoformat() if parsed else "unknown"
        day_source_raw[day][source] += 1

    for article in canonical_articles:
        source = article.get("source") or "unknown"
        day = article.get("timeline_date_used") or "unknown"
        day_source_canonical[day][source] += 1

    all_days = sorted(
        day
        for day in (set(day_source_raw.keys()) | set(day_source_canonical.keys()))
        if day != "unknown"
    )
    timeline_rows: list[dict[str, Any]] = []
    for day in all_days:
        source_ids = sorted(set(day_source_raw.get(day, {}).keys()) | set(day_source_canonical.get(day, {}).keys()))
        by_source: list[dict[str, Any]] = []
        total_raw = 0
        total_canonical = 0
        for source_id in source_ids:
            raw_count = int(day_source_raw.get(day, {}).get(source_id, 0))
            canonical_count = int(day_source_canonical.get(day, {}).get(source_id, 0))
            total_raw += raw_count
            total_canonical += canonical_count
            duplicates_removed = max(0, raw_count - canonical_count)
            duplicate_ratio = (duplicates_removed / raw_count) if raw_count else 0.0
            by_source.append(
                {
                    "source": source_id,
                    "raw_retrieved_count": raw_count,
                    "canonical_count": canonical_count,
                    "duplicates_removed": duplicates_removed,
                    "duplicate_ratio": round(duplicate_ratio, 3),
                }
            )

        duplicates_removed_total = max(0, total_raw - total_canonical)
        duplicate_ratio_total = (duplicates_removed_total / total_raw) if total_raw else 0.0
        driver = max(by_source, key=lambda row: row["raw_retrieved_count"])["source"] if by_source else "unknown"
        timeline_rows.append(
            {
                "day": day,
                "article_count": total_canonical,
                "canonical_count": total_canonical,
                "raw_retrieved_count": total_raw,
                "duplicates_removed": duplicates_removed_total,
                "duplicate_ratio": round(duplicate_ratio_total, 3),
                "dominant_source": driver,
                "source_breakdown": by_source,
            }
        )
    return timeline_rows


def run_workflow(run_input: RunInput, source_settings: dict[str, Any] | None = None) -> dict[str, Any]:
    run_id = f"run_{uuid4().hex[:10]}"
    started_at = datetime.now(timezone.utc).isoformat()

    if source_settings is None:
        ingestion = ingest_articles(run_input)
    else:
        ingestion = ingest_articles(run_input, source_settings=source_settings)
    normalization = normalize_articles(
        ingestion.get("deduplicated_hits", ingestion.get("raw_hits", [])),
        source="multi",
    )
    timeline = _build_timeline_breakdown(ingestion.get("raw_hits", []), normalization["canonical_articles"])
    cluster_timeline = _aggregate_cluster_daily_counts([], normalization["canonical_articles"])
    unknown_timeline_count = normalization["undated_article_count"]
    dated_count = sum(point["article_count"] for point in timeline)
    percent_undated = round((unknown_timeline_count / normalization["valid_count"]), 3) if normalization["valid_count"] else 0.0
    clustering = _build_clusters(normalization["canonical_articles"])
    filtered_clusters, filtered_article_to_cluster, excluded_clusters = _filter_clusters_by_relevance(
        clustering["clusters"],
        normalization["canonical_articles"],
        run_input.topic,
    )
    lifecycle_clusters, article_to_event, lifecycle_by_event = _build_event_lifecycle_models(
        filtered_clusters,
        normalization["canonical_articles"],
    )
    cluster_timeline = _aggregate_cluster_daily_counts(lifecycle_clusters, normalization["canonical_articles"])
    event_signal_timeline = _build_event_signal_timeline(
        ingestion.get("raw_hits", []),
        normalization["canonical_articles"],
        lifecycle_clusters,
    )
    temporal_check = _detect_temporal_anomaly(event_signal_timeline, lifecycle_clusters)
    plot_payload = _build_plot_payload(event_signal_timeline)
    peak_day = (
        max(event_signal_timeline, key=lambda item: int(item.get("event_signal", 0) or 0)).get("day")
        if event_signal_timeline
        else None
    )
    citation_index = _build_citation_index(
        normalization["canonical_articles"], filtered_article_to_cluster
    )
    geospatial = _extract_geospatial_entities(normalization["canonical_articles"])
    location_type_counts = dict(
        Counter(entity.get("location_type") or "unknown" for entity in geospatial.get("entities", []))
    )
    evidence_bundles = _build_evidence_bundles(
        lifecycle_clusters,
        event_signal_timeline,
        normalization["canonical_articles"],
        citation_index["citations"],
        geospatial["map_markers"],
    )
    warnings = _build_warnings(
        canonical_articles=normalization["canonical_articles"],
        clusters=lifecycle_clusters,
        duplicate_ratio=ingestion["telemetry"]["ingestion_duplicate_ratio"],
        geospatial_entities=geospatial["entities"],
        citation_index=citation_index,
        timeline=event_signal_timeline,
    )
    artifacts = {
        "deduplicated_article_set": normalization["canonical_articles"],
        "canonical_lineage_duplicate_map": ingestion["telemetry"].get("duplicate_map", []),
        "cluster_artifact": lifecycle_clusters,
        "citation_index": citation_index,
        "evidence_bundles": evidence_bundles,
        "geospatial_entities_markers": geospatial,
        "analyst_warnings": warnings,
        "event_lifecycle_index": lifecycle_by_event,
    }
    validation = _build_validation_report(
        ingestion=ingestion,
        normalization=normalization,
        clustering={"clusters": lifecycle_clusters, "article_to_cluster": filtered_article_to_cluster},
        geospatial=geospatial,
        citation_index=citation_index,
        evidence_bundles=evidence_bundles,
        timeline=event_signal_timeline,
        warnings=warnings,
        artifacts=artifacts,
    )
    review_log = _build_run_review_log(
        run_id=run_id,
        started_at=started_at,
        run_input=run_input,
        ingestion=ingestion,
        normalization=normalization,
        lifecycle_clusters=lifecycle_clusters,
        event_signal_timeline=event_signal_timeline,
        geospatial=geospatial,
        warnings=warnings,
        validation=validation,
    )
    review_markdown = _render_run_review_markdown(review_log)
    artifacts["run_review_log"] = {"json": review_log, "markdown": review_markdown}

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
                "clusters": lifecycle_clusters,
                "cluster_count": len(lifecycle_clusters),
                "article_to_cluster": filtered_article_to_cluster,
                "article_to_event": article_to_event,
                "excluded_clusters": excluded_clusters,
            },
            "citation_traceability": citation_index,
            "evidence": evidence_bundles,
            "geospatial": geospatial,
            "warnings": warnings,
            "validation": validation,
            "review_log": review_log,
            "review_log_markdown": review_markdown,
            "aggregation": {
                "daily_counts": event_signal_timeline,
                "event_signal_timeline": event_signal_timeline,
                "coverage_timeline_diagnostics": timeline,
                "daily_cluster_counts": cluster_timeline,
                "timeline_signal_default": "event_signal",
                "total_days": len(event_signal_timeline),
                "active_days": len(event_signal_timeline),
                "dated_article_count": dated_count,
                "undated_article_count": unknown_timeline_count,
                "percent_undated": percent_undated,
                "unknown_date_count": unknown_timeline_count,
                "primary_peak_excludes_unknown": True,
                "peak_day": peak_day,
                "raw_retrieved_count": ingestion.get("telemetry", {}).get("raw_retrieved_count", 0),
                "deduplicated_count": ingestion.get("telemetry", {}).get("deduplicated_count", 0),
                "cluster_count": len(lifecycle_clusters),
                "source_date_quality": normalization.get("source_date_quality", {}),
                "event_signal_total": sum(int(point.get("event_signal", 0) or 0) for point in event_signal_timeline),
                "coverage_volume_total": sum(int(point.get("coverage_volume", 0) or 0) for point in event_signal_timeline),
                "temporal_anomaly": temporal_check["temporal_anomaly"],
                "temporal_anomaly_explanation": temporal_check["anomaly_explanation"],
                "peak_event_signal_day": temporal_check.get("peak_event_signal_day"),
                "timeline_plot_payload": plot_payload,
                "geospatial": {
                    "map_markers": geospatial["map_markers"],
                    "location_type_counts": location_type_counts,
                },
            },
        },
        "artifacts": artifacts,
    }
