from datetime import date
import json
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
        "_load_all_source_configs",
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
    assert ingestion["telemetry"]["per_source_telemetry"]["reddit"]["attempted"] is True
    assert ingestion["telemetry"]["per_source_telemetry"]["reddit"]["succeeded"] is True
    assert ingestion["telemetry"]["per_source_telemetry"]["reddit"]["fallback_used"] is False


def test_partial_source_failure_behavior(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="supply chain", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    def _boom(session, source, run_input, max_records):
        raise RuntimeError("upstream timeout")

    monkeypatch.setattr(
        workflow,
        "_load_all_source_configs",
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
    assert gdelt_run["metadata"]["auth_mode"] == "no_key"


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
    assert result.metadata["fetch_mode"] == "twitter_api_v2"
    assert result.metadata["token_present"] is False


def test_hacker_news_algolia_fetch(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        def __init__(self, payload):
            self._payload = payload

        def json(self):
            return self._payload

        def raise_for_status(self):
            return None

    class MockSession:
        def __init__(self):
            self.params = None

        def get(self, url, params=None, headers=None, timeout=20):
            self.params = params
            return MockResponse(
                {
                    "hits": [
                        {
                            "objectID": "hn-123",
                            "title": "HN signal on energy grid",
                            "url": "https://example.com/hn-story",
                            "created_at": "2026-04-12T06:00:00Z",
                            "author": "analyst_user",
                        }
                    ]
                }
            )

    session = MockSession()
    result = workflow.fetch_hacker_news(
        session=session,
        source={"id": "hacker_news", "label": "Hacker News (Algolia)", "endpoint": "https://hn.algolia.com/api/v1/search_by_date"},
        run_input=RunInput(topic="energy grid", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17)),
        max_records=50,
    )

    assert result.status == "success"
    assert len(result.articles) == 1
    assert result.articles[0]["source"] == "hacker_news"
    assert result.articles[0]["source_attribution"]["raw_source"] == "hacker_news_algolia"
    assert "created_at_i>=" in session.params["numericFilters"]
    assert result.metadata == {"fetch_mode": "hacker_news_algolia_search_by_date"}


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
    assert without_geo["stages"]["geospatial"]["entities"]
    assert all(
        entity["location_type"] == "source_location"
        for entity in without_geo["stages"]["geospatial"]["entities"]
    )
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
    assert "sparse_coverage" in warning_codes
    assert "low_confidence_geo" in warning_codes


def test_validation_stop_on_empty_ingestion(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="no data", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [],
        "hits_count": 0,
        "source_runs": [{"source_id": "reddit", "status": "success", "metadata": {}, "warnings": []}],
        "sources_attempted": ["reddit"],
        "sources_succeeded": ["reddit"],
        "sources_failed": [],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })

    result = run_workflow(run_input)
    validation = result["stages"]["validation"]
    failed_rule_ids = {event["rule_id"] for event in validation["events"] if event["status"] == "fail"}

    assert validation["stop_recommended"] is True
    assert validation["can_publish"] is False
    assert "FM-004-empty-ingestion" in failed_rule_ids


def test_validation_warns_on_rate_limit_retry(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="rate limit", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {
                "article_id": "a1",
                "title": "London update",
                "url": "https://example.com/a1",
                "published_at": "2026-04-10T00:00:00Z",
                "source": "reddit",
                "source_label": "Reddit",
                "snippet": "London operations continue.",
                "source_attribution": {"source_id": "reddit", "source_label": "Reddit"},
            }
        ],
        "hits_count": 1,
        "source_runs": [{"source_id": "reddit", "status": "success", "metadata": {"json_retried_429": True}, "warnings": []}],
        "sources_attempted": ["reddit"],
        "sources_succeeded": ["reddit"],
        "sources_failed": [],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })

    result = run_workflow(run_input)
    validation = result["stages"]["validation"]
    warning_rule_ids = {event["rule_id"] for event in validation["events"] if event["status"] == "warn"}

    assert "FM-003-rate-limit-backoff" in warning_rule_ids
    assert validation["stop_recommended"] is False


def test_validation_detects_missing_artifact_contract() -> None:
    validation = workflow._build_validation_report(
        ingestion={"telemetry": {"ingestion_duplicate_ratio": 0.0}, "source_runs": [], "sources_attempted": []},
        normalization={"valid_count": 1, "invalid_count": 0, "canonical_articles": [{"source": "reddit"}]},
        clustering={"clusters": []},
        geospatial={"entities": []},
        citation_index={"citation_count": 1, "citations": [{"claim_classification": "supported"}]},
        evidence_bundles={},
        timeline=[],
        warnings=[],
        artifacts={"deduplicated_article_set": []},
    )

    failed_rule_ids = {event["rule_id"] for event in validation["events"] if event["status"] == "fail"}
    assert "FM-011-silent-ui-degradation" in failed_rule_ids


def test_aggregation_consistency_matches_normalized_total() -> None:
    canonical = [
        {"article_id": "a1", "title": "one", "url": "u1", "published_at": "20260410093000", "source": "gdelt"},
        {"article_id": "a2", "title": "two", "url": "u2", "published_at": "20260410T183000Z", "source": "gdelt"},
        {"article_id": "a3", "title": "three", "url": "u3", "published_at": "2026-04-11T03:00:00Z", "source": "reddit"},
    ]

    counts = aggregate_daily_counts(canonical)

    assert sum(point["article_count"] for point in counts) == len(canonical)
    assert len(counts) == 2


def test_parse_date_buckets_multi_day_for_gdelt_format() -> None:
    parsed_1 = workflow._parse_date("20260410093000")
    parsed_2 = workflow._parse_date("20260412001500")

    assert parsed_1 is not None
    assert parsed_2 is not None
    assert parsed_1.date().isoformat() == "2026-04-10"
    assert parsed_2.date().isoformat() == "2026-04-12"


def test_source_failure_reporting_distinguishes_skipped_and_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="signal", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))

    monkeypatch.setattr(
        workflow,
        "_load_source_configs",
        lambda: [{"id": "twitter", "label": "Twitter"}, {"id": "reddit", "label": "Reddit"}],
    )
    monkeypatch.setattr(
        workflow,
        "SOURCE_ADAPTER_REGISTRY",
        {
            "twitter": lambda s, c, r, m: workflow.SourceResult(
                source_id="twitter",
                source_label="Twitter",
                status="skipped",
                articles=[],
                warnings=["missing_twitter_bearer_token"],
                error="missing token",
            ),
            "reddit": lambda s, c, r, m: workflow.SourceResult(
                source_id="reddit",
                source_label="Reddit",
                status="success",
                articles=[],
                warnings=[],
            ),
        },
    )

    ingestion = ingest_articles(run_input)

    assert "twitter" not in ingestion["sources_failed"]
    assert ingestion["sources_skipped"] == ["twitter"]
    assert ingestion["sources_empty"] == ["reddit"]
    assert ingestion["telemetry"]["per_source_telemetry"]["twitter"]["skipped"] is True
    assert ingestion["telemetry"]["per_source_telemetry"]["twitter"]["failed"] is False


def test_cluster_distribution_groups_related_articles() -> None:
    canonical = [
        {"article_id": "a1", "title": "London transit strike causes delays", "snippet": "Commuters face major strike delays", "source": "s1", "published_at": "2026-04-10T01:00:00Z"},
        {"article_id": "a2", "title": "Major strike disrupts London transit", "snippet": "London commuters report delays", "source": "s2", "published_at": "2026-04-10T04:00:00Z"},
        {"article_id": "a3", "title": "Transit disruption expands in London", "snippet": "Strike enters second day", "source": "s3", "published_at": "2026-04-11T01:00:00Z"},
        {"article_id": "b1", "title": "Tokyo markets rally on export data", "snippet": "Stocks rise in Tokyo session", "source": "s1", "published_at": "2026-04-10T03:00:00Z"},
        {"article_id": "b2", "title": "Export optimism lifts Tokyo stocks", "snippet": "Tokyo benchmark closes higher", "source": "s2", "published_at": "2026-04-11T03:00:00Z"},
    ]

    clustering = workflow._build_clusters(canonical)
    cluster_sizes = sorted([len(cluster["article_ids"]) for cluster in clustering["clusters"]], reverse=True)

    assert len(clustering["clusters"]) <= 3
    assert cluster_sizes[0] >= 3


def test_geospatial_population_multiple_markers() -> None:
    canonical = [
        {"article_id": "a1", "title": "London response update", "snippet": "London officials briefed", "source": "s", "published_at": "2026-04-10T00:00:00Z"},
        {"article_id": "a2", "title": "Paris transport disruption", "snippet": "Parisians report delays", "source": "s", "published_at": "2026-04-10T00:00:00Z"},
        {"article_id": "a3", "title": "Tokyo market response", "snippet": "Tokyo traders react quickly", "source": "s", "published_at": "2026-04-10T00:00:00Z"},
    ]

    geo = workflow._extract_geospatial_entities(canonical)

    assert len(geo["entities"]) >= 3
    assert len(geo["map_markers"]) >= 3
    assert all(marker["location_label"] for marker in geo["map_markers"])
    assert all(entity["location_type"] in {"event_location", "mentioned_location", "source_location"} for entity in geo["entities"])


def test_timeline_multi_day_and_unknown_handling() -> None:
    normalized = workflow.normalize_articles(
        [
            {"article_id": "a1", "title": "One", "url": "https://a1", "published_at": "2026-04-10T01:00:00Z", "source": "reddit"},
            {"article_id": "a2", "title": "Two", "url": "https://a2", "published_at": "20260412093000", "source": "gdelt"},
            {"article_id": "a3", "title": "Three", "url": "https://a3", "published_at": "not-a-date", "source": "google_news"},
        ]
    )
    counts = aggregate_daily_counts(normalized["canonical_articles"])
    by_day = {row["day"]: row["article_count"] for row in counts}
    counts_with_undated = aggregate_daily_counts(normalized["canonical_articles"], include_undated=True)
    by_day_with_undated = {row["day"]: row["article_count"] for row in counts_with_undated}

    assert by_day["2026-04-10"] == 1
    assert by_day["2026-04-12"] == 1
    assert "unknown" not in by_day
    assert by_day_with_undated["unknown"] == 1


def test_reddit_fallback_triggers_on_empty_primary(monkeypatch: pytest.MonkeyPatch) -> None:
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
        def get(self, url, params=None, headers=None, timeout=20):
            if "search.json" in url:
                return MockResponse(status_code=200, json_payload={"data": {"children": []}})
            return MockResponse(
                status_code=200,
                text="<rss><channel><item><title>X</title><link>https://example.com/x</link><pubDate>Thu, 16 Apr 2026 10:00:00 +0000</pubDate></item></channel></rss>",
            )

    result = workflow.fetch_reddit(
        session=MockSession(),
        source={"id": "reddit", "label": "Reddit", "endpoint": "https://reddit.com/search.json", "rss_fallback": "https://reddit.com/search.rss"},
        run_input=RunInput(topic="ai", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17)),
        max_records=10,
    )

    assert result.status == "success"
    assert result.metadata["used_rss_fallback"] is True
    assert result.metadata["fallback_reason"] == "empty_primary_result"
    assert result.metadata["fallback_result_count"] == 1


def test_gdelt_transparent_failure_and_success(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockResponse:
        def __init__(self, status_code=200, payload=None):
            self.status_code = status_code
            self._payload = payload or {}
            self.text = json.dumps(self._payload)

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise workflow.requests.HTTPError(f"status={self.status_code}")

    class FailingSession:
        def get(self, url, params=None, headers=None, timeout=20):
            return MockResponse(status_code=503, payload={"status": "error"})

    failed = workflow.fetch_gdelt(
        session=FailingSession(),
        source={"id": "gdelt", "label": "GDELT", "endpoint": "https://gdelt"},
        run_input=RunInput(topic="energy", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17)),
        max_records=20,
    )
    assert failed.status == "failed"
    assert failed.metadata["http_status"] == 503
    assert failed.metadata["result_state"] == "failed"
    assert failed.metadata["attempted"] is True
    assert failed.metadata["failed"] is True
    assert failed.metadata["error_detail"]
    assert failed.error

    class SuccessSession:
        def get(self, url, params=None, headers=None, timeout=20):
            return MockResponse(
                status_code=200,
                payload={"articles": [{"title": "A", "url": "https://example.com/a", "seendate": "20260410120000", "domain": "example.com"}]},
            )

    success = workflow.fetch_gdelt(
        session=SuccessSession(),
        source={"id": "gdelt", "label": "GDELT", "endpoint": "https://gdelt"},
        run_input=RunInput(topic="energy", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17)),
        max_records=20,
    )
    assert success.status == "success"
    assert len(success.articles) == 1
    assert success.metadata["http_status"] == 200
    assert success.metadata["result_state"] == "partial"
    assert success.metadata["result_count"] == 1
    assert success.metadata["succeeded"] is True


def test_validation_stops_on_undated_timeline_and_required_gdelt_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="integrity", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))
    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [{"article_id": "a1", "title": "A", "url": "https://x", "published_at": "unknown-value", "source": "reddit"}],
        "hits_count": 1,
        "source_runs": [
            {"source_id": "reddit", "status": "success", "metadata": {}, "warnings": []},
            {"source_id": "gdelt", "status": "failed", "metadata": {"http_status": 500}, "warnings": [], "error": "boom"},
        ],
        "sources_attempted": ["reddit", "gdelt"],
        "sources_succeeded": ["reddit"],
        "sources_failed": ["gdelt"],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })
    result = run_workflow(run_input)
    failed_rules = {event["rule_id"] for event in result["stages"]["validation"]["events"] if event["status"] == "fail"}
    assert "FM-013-required-gdelt-source" in failed_rules
    assert "FM-014-unknown-date-peak" in failed_rules


def test_unknown_dates_do_not_override_known_peak(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="integrity", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))
    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {"article_id": "a1", "title": "A", "url": "https://x1", "published_at": "2026-04-10T01:00:00Z", "source": "reddit"},
            {"article_id": "a2", "title": "B", "url": "https://x2", "published_at": "2026-04-10T02:00:00Z", "source": "reddit"},
            {"article_id": "a3", "title": "C", "url": "https://x3", "published_at": "bad-date", "source": "reddit"},
            {"article_id": "a4", "title": "D", "url": "https://x4", "published_at": "also-bad", "source": "reddit"},
        ],
        "hits_count": 4,
        "source_runs": [{"source_id": "reddit", "status": "success", "metadata": {}, "warnings": []}],
        "sources_attempted": ["reddit"],
        "sources_succeeded": ["reddit"],
        "sources_failed": [],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })
    result = run_workflow(run_input)
    assert result["stages"]["aggregation"]["peak_day"] == "2026-04-10"
    assert result["stages"]["aggregation"]["dated_article_count"] == 2
    assert result["stages"]["aggregation"]["undated_article_count"] == 2
    assert result["stages"]["aggregation"]["primary_peak_excludes_unknown"] is True


def test_event_lifecycle_model_fields_present() -> None:
    canonical = workflow.normalize_articles(
        [
            {"article_id": "a1", "title": "Artemis II launch update", "url": "https://a1", "published_at": "2026-04-01T01:00:00Z", "source": "s1"},
            {"article_id": "a2", "title": "Artemis II lunar flyby complete", "url": "https://a2", "published_at": "2026-04-06T01:00:00Z", "source": "s2"},
            {"article_id": "a3", "title": "Artemis II mission ends safely", "url": "https://a3", "published_at": "2026-04-10T01:00:00Z", "source": "s3"},
        ]
    )["canonical_articles"]
    clusters = workflow._build_clusters(canonical)["clusters"]
    filtered, _, _ = workflow._filter_clusters_by_relevance(clusters, canonical, "Artemis II")
    lifecycle_clusters, _, _ = workflow._build_event_lifecycle_models(filtered, canonical)
    assert lifecycle_clusters
    required = {"event_id", "first_seen_date", "peak_date", "last_seen_date", "lifecycle_stage"}
    assert required.issubset(lifecycle_clusters[0].keys())


def test_temporal_anomaly_detection_for_late_coverage_spike() -> None:
    timeline = [
        {"day": "2026-04-01", "event_signal": 3, "coverage_volume": 4, "source_bias_detected": False},
        {"day": "2026-04-12", "event_signal": 1, "coverage_volume": 20, "source_bias_detected": True},
    ]
    clusters = [
        {"lifecycle_stage": "post-event coverage", "first_seen_date": "2026-04-01", "peak_date": "2026-04-06", "last_seen_date": "2026-04-12"}
    ]
    anomaly = workflow._detect_temporal_anomaly(timeline, clusters)
    assert anomaly["temporal_anomaly"] is True
    assert "coverage volume increases" in anomaly["anomaly_explanation"]


def test_event_signal_timeline_uses_cluster_first_seen_not_coverage_volume() -> None:
    canonical = workflow.normalize_articles(
        [
            {"article_id": "a1", "title": "Artemis II launch", "url": "https://a1", "published_at": "2026-04-01T00:00:00Z", "source": "s1"},
            {"article_id": "a2", "title": "Artemis II launch recap", "url": "https://a2", "published_at": "2026-04-10T00:00:00Z", "source": "s1"},
            {"article_id": "a3", "title": "Artemis II launch recap duplicate", "url": "https://a3", "published_at": "2026-04-10T01:00:00Z", "source": "s2"},
        ]
    )["canonical_articles"]
    base_clusters = workflow._build_clusters(canonical)["clusters"]
    filtered, _, _ = workflow._filter_clusters_by_relevance(base_clusters, canonical, "Artemis II")
    lifecycle_clusters, _, _ = workflow._build_event_lifecycle_models(filtered, canonical)
    timeline = workflow._build_event_signal_timeline(canonical, canonical, lifecycle_clusters)
    by_day = {row["day"]: row for row in timeline}
    assert by_day["2026-04-01"]["event_signal"] >= 1
    assert by_day["2026-04-10"]["coverage_volume"] >= by_day["2026-04-01"]["coverage_volume"]


def test_source_dominance_detection_threshold() -> None:
    raw = [
        {"article_id": "r1", "title": "A", "published_at": "2026-04-01T00:00:00Z", "source": "dominant"},
        {"article_id": "r2", "title": "B", "published_at": "2026-04-01T01:00:00Z", "source": "dominant"},
        {"article_id": "r3", "title": "C", "published_at": "2026-04-01T02:00:00Z", "source": "dominant"},
        {"article_id": "r4", "title": "D", "published_at": "2026-04-01T03:00:00Z", "source": "other"},
    ]
    canonical = [{"article_id": row["article_id"], "timeline_date_used": "2026-04-01", "source": row["source"]} for row in raw]
    clusters = [{"event_id": "event:1", "first_seen_date": "2026-04-01"}]
    timeline = workflow._build_event_signal_timeline(raw, canonical, clusters, source_bias_threshold=0.7)
    assert timeline[0]["source_bias_detected"] is True
    assert timeline[0]["dominant_source"] == "dominant"


def test_cluster_relevance_filter_excludes_irrelevant_cluster() -> None:
    canonical = workflow.normalize_articles(
        [
            {"article_id": "a1", "title": "Artemis II mission launch", "url": "https://a1", "published_at": "2026-04-01T00:00:00Z", "source": "s1"},
            {"article_id": "b1", "title": "Unrelated soccer transfer market", "url": "https://b1", "published_at": "2026-04-01T00:00:00Z", "source": "s2"},
        ]
    )["canonical_articles"]
    clusters = workflow._build_clusters(canonical)["clusters"]
    filtered, _, excluded = workflow._filter_clusters_by_relevance(clusters, canonical, "Artemis II")
    assert filtered
    assert excluded
    assert all(item["cluster_relevance_score"] < 0.12 for item in excluded)


def test_plot_payload_validity_contract() -> None:
    payload = workflow._build_plot_payload(
        [
            {"day": "2026-04-01", "event_signal": 2, "coverage_volume": 5},
            {"day": "2026-04-02", "event_signal": 1, "coverage_volume": 2},
        ]
    )
    assert payload["plot_valid"] is True
    assert payload["error"] is None
    assert payload["x"] == ["2026-04-01", "2026-04-02"]


def test_source_settings_disable_source_and_required_credentials_skip(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="settings", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))
    monkeypatch.delenv("TWITTER_BEARER_TOKEN", raising=False)
    monkeypatch.setattr(
        workflow,
        "_load_all_source_configs",
        lambda: [
            {"id": "reddit", "label": "Reddit", "enabled": True, "auth_mode": "no_key"},
            {"id": "twitter", "label": "Twitter", "enabled": True, "auth_mode": "required_key", "credential_env": "TWITTER_BEARER_TOKEN"},
        ],
    )
    monkeypatch.setattr(
        workflow,
        "SOURCE_ADAPTER_REGISTRY",
        {
            "reddit": lambda s, c, r, m: _ok_result("reddit", "A", "https://example.com/a", "2026-04-10T10:00:00Z"),
            "twitter": lambda s, c, r, m: _ok_result("twitter", "B", "https://example.com/b", "2026-04-10T11:00:00Z"),
        },
    )

    ingestion = ingest_articles(
        run_input,
        source_settings={
            "sources": {
                "reddit": {"enabled": False, "credential": ""},
                "twitter": {"enabled": True, "credential": ""},
            }
        },
    )

    assert ingestion["sources_attempted"] == ["twitter"]
    assert ingestion["sources_skipped"] == ["twitter"]
    assert ingestion["sources_failed"] == []
    twitter_run = ingestion["source_runs"][0]
    assert twitter_run["status"] == "skipped"
    assert "missing_required_credentials" in twitter_run["warnings"]


def test_validation_tightens_on_excessive_undated_articles(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="undated", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))
    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {"article_id": "a1", "title": "A", "url": "https://x1", "published_at": "bad-1", "source": "reddit"},
            {"article_id": "a2", "title": "B", "url": "https://x2", "published_at": "bad-2", "source": "reddit"},
            {"article_id": "a3", "title": "C", "url": "https://x3", "published_at": "2026-04-11T00:00:00Z", "source": "reddit"},
        ],
        "hits_count": 3,
        "source_runs": [{"source_id": "reddit", "status": "success", "metadata": {}, "warnings": []}],
        "sources_attempted": ["reddit"],
        "sources_succeeded": ["reddit"],
        "sources_failed": [],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })
    result = run_workflow(run_input)
    failed_rules = {event["rule_id"] for event in result["stages"]["validation"]["events"] if event["status"] == "fail"}
    assert "FM-016-excessive-undated-articles" in failed_rules


def test_normalization_parses_rfc2822_dates_and_derives_day() -> None:
    normalized = normalize_articles(
        [
            {
                "article_id": "rfc:1",
                "title": "RFC date",
                "url": "https://example.com/rfc",
                "published_at": "Sun, 19 Apr 2026 09:24:52 GMT",
                "source": "google_news",
            }
        ]
    )
    article = normalized["canonical_articles"][0]
    assert article["date_status"] == "parsed"
    assert article["published_at_parsed"] == "2026-04-19T09:24:52+00:00"
    assert article["published_day"] == "2026-04-19"
    assert article["date_parse_format_used"] == "rfc2822"
    assert article["date_source_field"] == "published_at"
    assert article["date_parse_error"] is None


def test_normalization_parses_iso8601_dates() -> None:
    normalized = normalize_articles(
        [
            {
                "article_id": "iso:1",
                "title": "ISO date",
                "url": "https://example.com/iso",
                "published_at": "2026-04-19T09:24:52Z",
                "source": "google_news",
            }
        ]
    )
    article = normalized["canonical_articles"][0]
    assert article["date_status"] == "parsed"
    assert article["published_day"] == "2026-04-19"
    assert article["date_parse_format_used"] == "iso8601"


def test_normalization_distinguishes_missing_vs_parse_failed_and_fallback() -> None:
    normalized = normalize_articles(
        [
            {"article_id": "a1", "title": "Missing", "url": "https://a1", "published_at": "", "source": "reddit"},
            {"article_id": "a2", "title": "Failed", "url": "https://a2", "published_at": "not-a-date", "source": "reddit"},
            {
                "article_id": "a3",
                "title": "Fallback",
                "url": "https://a3",
                "published_at": "",
                "created_at": "2026-04-12T05:00:00Z",
                "source": "reddit",
            },
        ]
    )
    by_id = {article["article_id"]: article for article in normalized["canonical_articles"]}
    assert by_id["a1"]["date_status"] == "missing"
    assert by_id["a1"]["date_parse_error"] == "missing_published_at"
    assert by_id["a2"]["date_status"] == "parse_failed"
    assert "unrecognized_date_format" in str(by_id["a2"]["date_parse_error"])
    assert by_id["a3"]["date_status"] == "fallback_derived"
    assert by_id["a3"]["date_source_field"] == "created_at"
    assert by_id["a3"]["published_day"] == "2026-04-12"


def test_run_workflow_emits_source_level_date_quality_telemetry(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="dates", start_date=date(2026, 4, 1), end_date=date(2026, 4, 17))
    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {"article_id": "a1", "title": "A", "url": "https://x1", "published_at": "2026-04-10T00:00:00Z", "source": "reddit"},
            {"article_id": "a2", "title": "B", "url": "https://x2", "published_at": "bad-date", "source": "reddit"},
            {"article_id": "a3", "title": "C", "url": "https://x3", "published_at": "", "source": "google_news"},
        ],
        "hits_count": 3,
        "source_runs": [
            {"source_id": "reddit", "status": "success", "metadata": {}, "warnings": []},
            {"source_id": "google_news", "status": "success", "metadata": {}, "warnings": []},
        ],
        "sources_attempted": ["reddit", "google_news"],
        "sources_succeeded": ["reddit", "google_news"],
        "sources_failed": [],
        "telemetry": {"ingestion_duplicate_ratio": 0.0, "duplicate_map": []},
    })
    result = run_workflow(run_input)
    telemetry = result["stages"]["aggregation"]["source_date_quality"]
    assert telemetry["reddit"]["total_articles"] == 2
    assert telemetry["reddit"]["parsed_dates"] == 1
    assert telemetry["reddit"]["parse_failures"] == 1
    assert telemetry["reddit"]["missing_dates"] == 0
    assert telemetry["reddit"]["percent_undated"] == 0.5
    assert telemetry["google_news"]["missing_dates"] == 1


def test_source_settings_ui_payload_wiring() -> None:
    from gr_app import _build_source_settings_payload

    payload = _build_source_settings_payload(
        True, "", True, "", True, "", True, "", True, "", True, "token-123"
    )
    assert payload["sources"]["gdelt"]["enabled"] is True
    assert payload["sources"]["gdelt"]["credential"] == ""
    assert payload["sources"]["twitter"]["credential"] == "token-123"


def test_timeline_defaults_to_canonical_not_raw(monkeypatch: pytest.MonkeyPatch) -> None:
    run_input = RunInput(topic="dup spike", start_date=date(2026, 4, 1), end_date=date(2026, 4, 20))
    monkeypatch.setattr(workflow, "ingest_articles", lambda _: {
        "raw_hits": [
            {"article_id": "r1", "title": "Same", "url": "https://example.com/a?utm_source=x", "published_at": "2026-04-20T01:00:00Z", "source": "google_news"},
            {"article_id": "r2", "title": "Same", "url": "https://example.com/a?utm_source=y", "published_at": "2026-04-20T01:01:00Z", "source": "google_news"},
            {"article_id": "r3", "title": "Same", "url": "https://example.com/a", "published_at": "2026-04-20T01:02:00Z", "source": "reddit"},
        ],
        "deduplicated_hits": [
            {"article_id": "c1", "title": "Same", "url": "https://example.com/a", "published_at": "2026-04-20T01:00:00Z", "source": "google_news"}
        ],
        "hits_count": 1,
        "source_runs": [{"source_id": "google_news", "status": "success", "metadata": {}, "warnings": []}],
        "sources_attempted": ["google_news"],
        "sources_succeeded": ["google_news"],
        "sources_failed": [],
        "telemetry": {"ingestion_duplicate_ratio": 0.67, "duplicate_map": [], "raw_retrieved_count": 3, "deduplicated_count": 1},
    })

    result = run_workflow(run_input)
    day = result["stages"]["aggregation"]["daily_counts"][0]
    assert day["canonical_count"] == 1
    assert day["raw_retrieved_count"] == 3
    assert day["duplicate_ratio"] == pytest.approx(2 / 3, abs=0.001)


def test_source_day_breakdown_and_duplicate_ratio() -> None:
    rows = workflow._build_timeline_breakdown(
        raw_articles=[
            {"article_id": "r1", "title": "A", "url": "https://example.com/a", "published_at": "2026-04-20T00:00:00Z", "source": "google_news"},
            {"article_id": "r2", "title": "A", "url": "https://example.com/a?utm_source=x", "published_at": "2026-04-20T00:05:00Z", "source": "google_news"},
            {"article_id": "r3", "title": "B", "url": "https://example.com/b", "published_at": "2026-04-20T00:10:00Z", "source": "reddit"},
        ],
        canonical_articles=[
            {"article_id": "c1", "title": "A", "url": "https://example.com/a", "timeline_date_used": "2026-04-20", "source": "google_news"},
            {"article_id": "c2", "title": "B", "url": "https://example.com/b", "timeline_date_used": "2026-04-20", "source": "reddit"},
        ],
    )
    assert len(rows) == 1
    row = rows[0]
    assert row["dominant_source"] == "google_news"
    assert row["duplicate_ratio"] == pytest.approx(1 / 3, abs=0.001)
    by_source = {item["source"]: item for item in row["source_breakdown"]}
    assert by_source["google_news"]["duplicate_ratio"] == pytest.approx(0.5, abs=0.001)
    assert by_source["reddit"]["duplicate_ratio"] == 0.0


def test_timeline_date_used_prefers_publication_not_retrieval() -> None:
    normalized = workflow.normalize_articles(
        [
            {
                "article_id": "ddg:1",
                "title": "Search result",
                "url": "https://example.com/search",
                "published_at": None,
                "retrieved_at": "2026-04-20T10:00:00Z",
                "source": "web_duckduckgo",
            }
        ]
    )
    article = normalized["canonical_articles"][0]
    assert article["retrieved_at"] == "2026-04-20T10:00:00Z"
    assert article["timeline_date_used"] == "unknown"
    assert article["date_status"] == "missing"


def test_google_news_canonicalization_unwraps_target_url() -> None:
    google_redirect = "https://news.google.com/rss/articles/CBMiQWh0dHBzOi8vbmV3cy5leGFtcGxlLmNvbS9zdG9yeS_SAQA?oc=5&url=https%3A%2F%2Fexample.com%2Fstory%3Futm_source%3Drss"
    canonical = workflow._canonicalize_url(google_redirect)
    assert canonical == "https://example.com/story"
