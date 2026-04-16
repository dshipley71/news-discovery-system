from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import urlopen
from uuid import uuid4


@dataclass(frozen=True)
class RunInput:
    topic: str
    start_date: date
    end_date: date


def _load_source_config() -> dict[str, Any]:
    config_path = Path(__file__).resolve().parents[2] / "config" / "sources.json"
    with config_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data["sources"][0]


def _date_to_epoch_bounds(start_date: date, end_date: date) -> tuple[int, int]:
    start_dt = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_dt = datetime.combine(end_date, time.max, tzinfo=timezone.utc)
    return int(start_dt.timestamp()), int(end_dt.timestamp())


def ingest_articles(run_input: RunInput, max_records: int = 200) -> dict[str, Any]:
    start_epoch, end_epoch = _date_to_epoch_bounds(run_input.start_date, run_input.end_date)
    source = _load_source_config()

    query = urlencode(
        {
            "query": run_input.topic,
            "tags": source.get("tags", "story"),
            "numericFilters": f"created_at_i>={start_epoch},created_at_i<={end_epoch}",
            "hitsPerPage": max_records,
        }
    )

    with urlopen(f"{source['endpoint']}?{query}", timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))

    return {
        "source": source["id"],
        "requested_at": datetime.now(timezone.utc).isoformat(),
        "query": run_input.topic,
        "hits_count": payload.get("nbHits", 0),
        "raw_hits": payload.get("hits", []),
    }


def normalize_articles(raw_hits: list[dict[str, Any]], source: str) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    validation_issues: list[dict[str, Any]] = []

    for idx, hit in enumerate(raw_hits):
        title = hit.get("title") or hit.get("story_title")
        url = hit.get("url") or hit.get("story_url")
        published_at = hit.get("created_at")
        object_id = hit.get("objectID")

        missing = [
            field
            for field, value in {
                "title": title,
                "published_at": published_at,
                "object_id": object_id,
            }.items()
            if not value
        ]

        if missing:
            validation_issues.append(
                {"hit_index": idx, "object_id": object_id, "missing_fields": missing}
            )
            continue

        records.append(
            {
                "article_id": f"{source}:{object_id}",
                "title": title,
                "url": url,
                "published_at": published_at,
                "source": source,
            }
        )

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
        if not published_at:
            continue
        try:
            day = datetime.fromisoformat(published_at.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            continue
        counts[day] += 1

    return [{"day": day, "article_count": counts[day]} for day in sorted(counts.keys())]


def run_workflow(run_input: RunInput) -> dict[str, Any]:
    run_id = f"run_{uuid4().hex[:10]}"
    started_at = datetime.now(timezone.utc).isoformat()

    ingestion = ingest_articles(run_input)
    normalization = normalize_articles(ingestion["raw_hits"], ingestion["source"])
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
            "aggregation": {"daily_counts": timeline, "total_days": len(timeline)},
        },
    }
