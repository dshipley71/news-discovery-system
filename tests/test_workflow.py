from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.news_app.workflow import aggregate_daily_counts, normalize_articles


def test_normalize_flags_missing_fields() -> None:
    raw_hits = [
        {"objectID": "1", "title": "ok", "created_at": "2026-04-15T10:00:00Z", "url": "https://a"},
        {"objectID": "2", "created_at": "2026-04-15T11:00:00Z", "url": "https://b"},
    ]

    result = normalize_articles(raw_hits, source="hn")

    assert result["valid_count"] == 1
    assert result["invalid_count"] == 1
    assert result["canonical_articles"][0]["article_id"] == "hn:1"


def test_aggregate_daily_counts_groups_by_day() -> None:
    canonical = [
        {"article_id": "1", "title": "a", "url": "u", "published_at": "2026-04-10T01:00:00Z", "source": "s"},
        {"article_id": "2", "title": "b", "url": "u", "published_at": "2026-04-10T05:00:00Z", "source": "s"},
        {"article_id": "3", "title": "c", "url": "u", "published_at": "2026-04-11T05:00:00Z", "source": "s"},
    ]

    counts = aggregate_daily_counts(canonical)

    assert counts == [
        {"day": "2026-04-10", "article_count": 2},
        {"day": "2026-04-11", "article_count": 1},
    ]
