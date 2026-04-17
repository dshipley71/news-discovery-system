from datetime import date
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.news_app import workflow
from src.news_app.workflow import RunInput, aggregate_daily_counts, ingest_articles, normalize_articles, run_workflow


def _ok_result(source_id: str, title: str, url: str, published_at: str, snippet: str = "") -> workflow.SourceResult:
    return workflow.SourceResult(
        source_id=source_id,
        source_label=source_id,
        status="success",
        warnings=[],
        articles=[
            {
                "article_id": f"{source_id}:1",
                "title": title,
                "url": url,
                "published_at": published_at,
                "source": source_id,
                "source_label": source_id,
                "snippet": snippet,
                "source_attribution": {
                    "source_id": source_id,
                    "source_label": source_id,
                    "raw_source": source_id,
                },
            }
        ],
    )


def test_multiple_source_merge_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="climate", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    monkeypatch.setattr(
        workflow,
        "_load_source_configs",
        lambda: [{"id": "reddit", "label": "Reddit"}, {"id": "google_news", "label": "Google"}],
    )

    monkeypatch.setattr(
        workflow,
        "SOURCE_ADAPTER_REGISTRY",
        {
            "reddit": lambda s, c, r, m: _ok_result(
                "reddit", "Shared Headline", "https://example.com/story", "2026-04-10T10:00:00Z"
            ),
            "google_news": lambda s, c, r, m: _ok_result(
                "google_news", "Shared Headline", "https://example.com/story", "2026-04-10T11:00:00Z"
            ),
        },
    )

    ingestion = ingest_articles(run_input)

    assert ingestion["sources_attempted"] == ["reddit", "google_news"]
    assert set(ingestion["sources_succeeded"]) == {"reddit", "google_news"}
    assert ingestion["hits_count"] == 1
    assert ingestion["telemetry"]["ingestion_duplicate_count"] == 1
    assert len(ingestion["telemetry"]["duplicate_map"]) == 1
    assert ingestion["telemetry"]["duplicate_map"][0]["duplicate_count"] == 1
    assert ingestion["telemetry"]["per_source_status"] == {
        "reddit": "success",
        "google_news": "success",
    }


def test_partial_source_failure_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="supply chain", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    def _boom(session, source, run_input, max_records):
        raise RuntimeError("upstream timeout")

    monkeypatch.setattr(
        workflow,
        "_load_source_configs",
        lambda: [{"id": "reddit", "label": "Reddit"}, {"id": "gdelt", "label": "GDELT"}],
    )
    monkeypatch.setattr(
        workflow,
        "SOURCE_ADAPTER_REGISTRY",
        {
            "reddit": lambda s, c, r, m: _ok_result(
                "reddit", "A", "https://example.com/a", "2026-04-11T10:00:00Z"
            ),
            "gdelt": _boom,
        },
    )

    ingestion = ingest_articles(run_input)

    assert "reddit" in ingestion["sources_succeeded"]
    assert "gdelt" in ingestion["sources_failed"]
    gdelt_run = next(item for item in ingestion["source_runs"] if item["source_id"] == "gdelt")
    assert gdelt_run["status"] == "failed"
    assert gdelt_run["error"]
    assert gdelt_run["metadata"] == {}


def test_twitter_disabled_when_token_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)

    result = workflow.fetch_twitter(
        session=workflow.requests.Session(),
        source={"id": "twitter", "label": "X/Twitter", "endpoint": "https://example.com"},
        run_input=RunInput(topic="energy", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17)),
        max_records=10,
    )

    assert result.status == "skipped"
    assert result.articles == []
    assert "missing_twitter_bearer_token" in result.warnings
    assert result.metadata == {"fetch_mode": "twitter_api_v2", "token_present": False}


def test_schema_consistency_across_sources() -> None:
    records = [
        {
            "article_id": "reddit:1",
            "title": "A",
            "url": "https://a",
            "published_at": "2026-04-10T01:00:00Z",
            "source": "reddit",
            "source_label": "Reddit",
            "source_attribution": {"source_id": "reddit", "source_label": "Reddit"},
        },
        {
            "article_id": "gdelt:2",
            "title": "B",
            "url": "https://b",
            "published_at": "2026-04-10T05:00:00Z",
            "source": "gdelt",
            "source_label": "GDELT",
            "source_attribution": {"source_id": "gdelt", "source_label": "GDELT"},
        },
    ]

    normalized = normalize_articles(records, source="multi")

    assert normalized["valid_count"] == 2
    required_keys = {
        "article_id",
        "title",
        "url",
        "published_at",
        "source",
        "source_label",
        "source_attribution",
    }
    for article in normalized["canonical_articles"]:
        assert required_keys.issubset(article.keys())


def test_reddit_retry_and_rss_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        def __init__(self, status_code=200, json_payload=None, text="", headers=None):
            self.status_code = status_code
            self._json_payload = json_payload or {}
            self.text = text
            self.headers = headers or {}

        def json(self):
            return self._json_payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise workflow.requests.HTTPError(f"status={self.status_code}")

    class MockSession:
        def __init__(self):
            self.calls = 0

        def get(self, url, params=None, headers=None, timeout=20):
            self.calls += 1
            if self.calls == 1:
                return MockResponse(status_code=429, headers={"Retry-After": "1"})
            if self.calls == 2:
                raise RuntimeError("json unavailable")
            return MockResponse(
                status_code=200,
                text="""
                <rss><channel><item>
                  <title>Fallback Story</title>
                  <link>https://example.com/fallback</link>
                  <pubDate>Thu, 16 Apr 2026 10:00:00 +0000</pubDate>
                </item></channel></rss>
                """,
            )

    result = workflow.fetch_reddit(
        session=MockSession(),
        source={
            "id": "reddit",
            "label": "Reddit",
            "endpoint": "https://reddit/json",
            "rss_fallback": "https://reddit/rss",
            "user_agent": "agent",
        },
        run_input=RunInput(topic="ai", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17)),
        max_records=5,
    )

    assert result.status == "success"
    assert len(result.articles) == 1
    assert result.articles[0]["source"] == "reddit"
    assert any("json_api_failed" in warning for warning in result.warnings)
    assert result.metadata["used_rss_fallback"] is True


def test_aggregate_daily_counts_groups_by_day() -> None:
    canonical = [
        {"article_id": "1", "title": "a", "url": "u", "published_at": "2026-04-10T01:00:00Z", "source": "s"},
        {"article_id": "2", "title": "b", "url": "u2", "published_at": "2026-04-10T05:00:00Z", "source": "s"},
        {"article_id": "3", "title": "c", "url": "u3", "published_at": "2026-04-11T05:00:00Z", "source": "s"},
    ]

    counts = aggregate_daily_counts(canonical)

    assert counts == [
        {"day": "2026-04-10", "article_count": 2},
        {"day": "2026-04-11", "article_count": 1},
    ]


def test_run_workflow_emits_first_class_backend_artifacts(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="city response", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    monkeypatch.setattr(
        workflow,
        "_load_source_configs",
        lambda: [{"id": "reddit", "label": "Reddit"}, {"id": "google_news", "label": "Google"}],
    )
    monkeypatch.setattr(
        workflow,
        "SOURCE_ADAPTER_REGISTRY",
        {
            "reddit": lambda s, c, r, m: workflow.SourceResult(
                source_id="reddit",
                source_label="Reddit",
                status="success",
                warnings=[],
                articles=[
                    {
                        "article_id": "reddit:a",
                        "title": "London emergency response update",
                        "url": "https://example.com/london-1",
                        "published_at": "2026-04-10T08:00:00Z",
                        "source": "reddit",
                        "source_label": "Reddit",
                        "snippet": "Officials in London reported updates.",
                        "source_attribution": {"source_id": "reddit", "source_label": "Reddit"},
                    },
                    {
                        "article_id": "reddit:b",
                        "title": "Paris transport disruption",
                        "url": "https://example.com/paris-1",
                        "published_at": "2026-04-10T10:00:00Z",
                        "source": "reddit",
                        "source_label": "Reddit",
                        "snippet": "Transit delays in Paris continue.",
                        "source_attribution": {"source_id": "reddit", "source_label": "Reddit"},
                    },
                ],
            ),
            "google_news": lambda s, c, r, m: workflow.SourceResult(
                source_id="google_news",
                source_label="Google News",
                status="success",
                warnings=[],
                articles=[
                    {
                        "article_id": "google_news:a",
                        "title": "London emergency response update",
                        "url": "https://example.com/london-1",
                        "published_at": "2026-04-10T08:05:00Z",
                        "source": "google_news",
                        "source_label": "Google News",
                        "snippet": "London emergency services remain active.",
                        "source_attribution": {"source_id": "google_news", "source_label": "Google News"},
                    }
                ],
            ),
        },
    )

    result = run_workflow(run_input)

    stages = result["stages"]
    artifacts = result["artifacts"]

    assert artifacts["deduplicated_article_set"]
    assert artifacts["canonical_lineage_duplicate_map"]
    assert stages["clustering"]["cluster_count"] >= 1
    first_cluster = stages["clustering"]["clusters"][0]
    assert {"cluster_id", "cluster_label", "article_ids", "source_diversity", "cluster_confidence", "temporal_span"}.issubset(
        first_cluster.keys()
    )

    citation_index = stages["citation_traceability"]
    assert citation_index["citation_count"] == len(citation_index["citations"])
    assert all(citation["article_id"] for citation in citation_index["citations"])

    evidence = stages["evidence"]
    assert evidence["cluster_to_articles"]
    assert "peak_to_clusters_articles" in evidence
    assert "location_to_clusters_articles" in evidence


def test_geospatial_artifacts_presence_and_absence(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="coverage", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {
                "article_id": "a1",
                "title": "London policy update",
                "url": "https://example.com/1",
                "published_at": "2026-04-10T00:00:00Z",
                "source": "reddit",
                "source_label": "Reddit",
                "snippet": "Decision in London today.",
                "source_attribution": {"source_id": "reddit", "source_label": "Reddit"},
            }
        ],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })

    with_geo = run_workflow(run_input)
    assert with_geo["stages"]["geospatial"]["entities"]
    assert with_geo["stages"]["aggregation"]["geospatial"]["map_markers"]

    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {
                "article_id": "a2",
                "title": "Market update",
                "url": "https://example.com/2",
                "published_at": "2026-04-10T00:00:00Z",
                "source": "reddit",
                "source_label": "Reddit",
                "snippet": "No location mention.",
                "source_attribution": {"source_id": "reddit", "source_label": "Reddit"},
            }
        ],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })

    without_geo = run_workflow(run_input)
    assert without_geo["stages"]["geospatial"]["entities"] == []
    assert without_geo["stages"]["aggregation"]["geospatial"]["map_markers"] == []


def test_warning_generation_on_weak_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="thin signal", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {
                "article_id": "only:1",
                "title": "Paris watch",
                "url": "https://example.com/p",
                "published_at": "2026-04-10T00:00:00Z",
                "source": "single",
                "source_label": "Single",
                "snippet": "Paris situation remains unclear.",
                "source_attribution": {"source_id": "single", "source_label": "Single"},
            }
        ],
        "telemetry": {"ingestion_duplicate_ratio": 0.6, "duplicate_map": []},
    })

    result = run_workflow(run_input)
    warning_codes = {item["warning_code"] for item in result["stages"]["warnings"]}

    assert "weak_source_diversity" in warning_codes
    assert "duplicate_heavy_result_set" in warning_codes
    assert "weak_cluster_evidence" in warning_codes
    assert "sparse_coverage" in warning_codes
    assert "low_confidence_geo" in warning_codes
