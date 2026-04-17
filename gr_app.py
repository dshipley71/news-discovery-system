from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from src.news_app.workflow import RunInput, run_workflow


DARK_LIGHT_CSS = """
:root {
  --nd-bg: #0f172a;
  --nd-bg-panel: #111827;
  --nd-border: #334155;
  --nd-text: #e5e7eb;
  --nd-muted: #93c5fd;
}
.gradio-container {
  background: var(--nd-bg) !important;
  color: var(--nd-text) !important;
}
.nd-panel {
  border: 1px solid var(--nd-border);
  border-radius: 10px;
  padding: 10px;
  background: var(--nd-bg-panel);
}
.nd-kicker {
  color: var(--nd-muted);
  font-size: 0.95rem;
  margin-bottom: 4px;
}
body.nd-light {
  --nd-bg: #f3f4f6;
  --nd-bg-panel: #ffffff;
  --nd-border: #cbd5e1;
  --nd-text: #111827;
  --nd-muted: #1d4ed8;
}
"""


def _validate_inputs(topic: str, start_date: str, end_date: str) -> tuple[str, date, date]:
    topic = str(topic or "").strip()
    if not topic:
        raise ValueError("Topic is required.")

    start_date = str(start_date or "").strip()
    end_date = str(end_date or "").strip()

    if not start_date or not end_date:
        raise ValueError("Start date and end date are required.")

    try:
        start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError as exc:
        raise ValueError("Dates must be in YYYY-MM-DD format.") from exc

    if start_date_obj > end_date_obj:
        raise ValueError("Start date must be on or before end date.")

    if (end_date_obj - start_date_obj).days > 30:
        raise ValueError("Date range must be 30 days or less.")

    if end_date_obj > datetime.now(timezone.utc).date():
        raise ValueError("End date cannot be in the future.")

    return topic, start_date_obj, end_date_obj


def _pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _timeline_figure(daily_counts: list[dict[str, Any]]) -> Any:
    fig, ax = plt.subplots(figsize=(10, 4))

    if not daily_counts:
        ax.text(0.5, 0.5, "No timeline data returned.", ha="center", va="center")
        ax.set_title("Daily Article Counts")
        ax.set_xlabel("Date")
        ax.set_ylabel("Articles")
        fig.tight_layout()
        return fig

    days = [point.get("day") for point in daily_counts]
    counts = [int(point.get("article_count", 0)) for point in daily_counts]

    ax.plot(days, counts, marker="o", color="#60a5fa")
    peak_count = max(counts)
    peak_indexes = [idx for idx, count in enumerate(counts) if count == peak_count]
    for idx in peak_indexes:
        ax.annotate(
            f"Peak {peak_count}",
            (days[idx], counts[idx]),
            textcoords="offset points",
            xytext=(0, 10),
            ha="center",
            color="#facc15",
        )

    ax.set_title("Daily Article Counts")
    ax.set_xlabel("Date")
    ax.set_ylabel("Articles")
    ax.grid(alpha=0.25)
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


def _build_timeline_summary(daily_counts: list[dict[str, Any]]) -> str:
    if not daily_counts:
        return "No timeline data returned; unable to identify spikes or trend direction."

    total_articles = sum(int(point.get("article_count", 0)) for point in daily_counts)
    peak_day = max(daily_counts, key=lambda point: int(point.get("article_count", 0)))
    first_count = int(daily_counts[0].get("article_count", 0))
    last_count = int(daily_counts[-1].get("article_count", 0))
    direction = "increasing" if last_count > first_count else "decreasing" if last_count < first_count else "flat"
    return (
        f"{len(daily_counts)} active day(s), {total_articles} total article instances, "
        f"peak on {peak_day.get('day')} ({peak_day.get('article_count')} articles), "
        f"overall pattern appears {direction}."
    )


def _build_map_plot(map_rows: list[dict[str, Any]]) -> go.Figure:
    if not map_rows:
        fig = go.Figure()
        fig.add_annotation(
            text="No geospatial output returned for this run.",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font={"size": 15, "color": "#e5e7eb"},
        )
        fig.update_layout(
            template="plotly_dark",
            paper_bgcolor="#111827",
            plot_bgcolor="#111827",
            geo={"showframe": False, "showcoastlines": True, "projection_type": "equirectangular"},
            margin={"l": 10, "r": 10, "t": 40, "b": 10},
            title="Geospatial Activity Map",
        )
        return fig

    frame = {
        "location_label": [row["location_label"] for row in map_rows],
        "latitude": [row["latitude"] for row in map_rows],
        "longitude": [row["longitude"] for row in map_rows],
        "article_count": [row["article_count"] for row in map_rows],
        "intensity": [row["intensity"] for row in map_rows],
        "avg_confidence": [row["avg_confidence"] for row in map_rows],
        "ambiguous_locations": [row["ambiguous_locations"] for row in map_rows],
    }

    fig = px.scatter_geo(
        frame,
        lat="latitude",
        lon="longitude",
        hover_name="location_label",
        size="article_count",
        color="intensity",
        hover_data={
            "article_count": True,
            "avg_confidence": True,
            "ambiguous_locations": True,
            "latitude": False,
            "longitude": False,
        },
        title="Geospatial Activity Map",
        color_discrete_map={"low": "#60a5fa", "medium": "#f59e0b", "high": "#f43f5e"},
    )
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="#111827",
        margin={"l": 10, "r": 10, "t": 40, "b": 10},
    )
    return fig


def _build_cluster_views(result: dict[str, Any]) -> dict[str, Any]:
    artifacts = result.get("artifacts", {})
    stages = result.get("stages", {})
    clusters = artifacts.get("cluster_artifact") or stages.get("clustering", {}).get("clusters", [])
    canonical_articles = artifacts.get("deduplicated_article_set") or stages.get("normalization", {}).get("canonical_articles", [])
    citations = artifacts.get("citation_index", {}).get("citations") or stages.get("citation_traceability", {}).get("citations", [])

    articles_by_id = {article.get("article_id"): article for article in canonical_articles if article.get("article_id")}
    duplicate_map = artifacts.get("canonical_lineage_duplicate_map") or []
    duplicate_impacted: set[str] = set()
    for group in duplicate_map:
        article_ids = group.get("article_ids") or []
        if int(group.get("duplicate_count", 0)) > 0:
            duplicate_impacted.update(article_ids)

    citation_by_article = {citation.get("article_id"): citation for citation in citations if citation.get("article_id")}

    cluster_rows: list[list[Any]] = []
    cluster_lookup: dict[str, Any] = {}
    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        if not cluster_id:
            continue
        article_ids = cluster.get("article_ids") or []
        members = [articles_by_id[article_id] for article_id in article_ids if article_id in articles_by_id]
        source_counts: dict[str, int] = {}
        for article in members:
            source = article.get("source") or "unknown"
            source_counts[source] = source_counts.get(source, 0) + 1

        article_count = len(article_ids)
        distinct_sources = int(cluster.get("source_diversity") or len(source_counts))
        duplicate_count = sum(1 for article_id in article_ids if article_id in duplicate_impacted)
        duplicate_ratio = round((duplicate_count / article_count), 3) if article_count else 0.0
        top_source_ratio = 0.0
        top_source = "unknown"
        if source_counts and article_count:
            top_source, top_count = max(source_counts.items(), key=lambda item: item[1])
            top_source_ratio = round(top_count / article_count, 3)

        detail_articles = []
        for article in members:
            citation = citation_by_article.get(article.get("article_id"), {})
            detail_articles.append(
                {
                    "article_id": article.get("article_id"),
                    "title": article.get("title"),
                    "source": article.get("source"),
                    "published_at": article.get("published_at"),
                    "url": article.get("url"),
                    "claim_classification": citation.get("claim_classification"),
                    "duplicate_flag": article.get("article_id") in duplicate_impacted,
                }
            )

        cluster_lookup[cluster_id] = {
            "cluster_id": cluster_id,
            "cluster_label": cluster.get("cluster_label"),
            "article_count": article_count,
            "duplicate_count": duplicate_count,
            "duplicate_ratio": duplicate_ratio,
            "duplicate_heavy": duplicate_ratio >= 0.5,
            "source_diversity": distinct_sources,
            "source_bias": {
                "top_source": top_source,
                "top_source_ratio": top_source_ratio,
            },
            "cluster_confidence": cluster.get("cluster_confidence"),
            "temporal_span": cluster.get("temporal_span"),
            "heuristic": cluster.get("heuristic"),
            "articles": detail_articles,
        }

        cluster_rows.append(
            [
                cluster_id,
                cluster.get("cluster_label"),
                article_count,
                distinct_sources,
                duplicate_count,
                duplicate_ratio,
                top_source_ratio,
                duplicate_ratio >= 0.5,
            ]
        )

    cluster_choices = sorted(cluster_lookup.keys())
    return {
        "cluster_rows": cluster_rows,
        "cluster_lookup": cluster_lookup,
        "cluster_choices": cluster_choices,
    }


def _build_citation_views(result: dict[str, Any]) -> tuple[list[list[Any]], dict[str, Any], list[list[Any]]]:
    artifacts = result.get("artifacts", {})
    stages = result.get("stages", {})
    citation_index = artifacts.get("citation_index") or stages.get("citation_traceability", {})
    evidence = artifacts.get("evidence_bundles") or stages.get("evidence", {})

    citations = citation_index.get("citations", [])
    citation_rows = [
        [
            citation.get("citation_id"),
            citation.get("article_id"),
            citation.get("cluster_id"),
            citation.get("source"),
            citation.get("published_at"),
            citation.get("url"),
            citation.get("claim_classification"),
            citation.get("title"),
        ]
        for citation in citations
    ]

    evidence_bundle_rows: list[list[Any]] = []
    for bundle in evidence.get("cluster_to_articles", []):
        for article_id in bundle.get("article_ids", []):
            evidence_bundle_rows.append(
                [
                    bundle.get("bundle_id"),
                    "cluster_to_articles",
                    bundle.get("cluster_id"),
                    article_id,
                    ", ".join(bundle.get("citation_ids", [])) or None,
                ]
            )
    for bundle in evidence.get("peak_to_clusters_articles", []):
        for cluster_info in bundle.get("clusters", []):
            for article_id in cluster_info.get("article_ids", []):
                evidence_bundle_rows.append(
                    [
                        bundle.get("bundle_id"),
                        "peak_to_clusters_articles",
                        bundle.get("peak_day"),
                        article_id,
                        cluster_info.get("cluster_id"),
                    ]
                )
    for bundle in evidence.get("location_to_clusters_articles", []):
        for article_id in bundle.get("article_ids", []):
            evidence_bundle_rows.append(
                [
                    bundle.get("bundle_id"),
                    "location_to_clusters_articles",
                    bundle.get("location_label"),
                    article_id,
                    ", ".join(bundle.get("cluster_ids", [])),
                ]
            )

    return citation_rows, citation_index, evidence_bundle_rows


def _build_timeline_drilldown(result: dict[str, Any]) -> tuple[list[list[Any]], dict[str, Any], list[str]]:
    evidence = result.get("artifacts", {}).get("evidence_bundles") or result.get("stages", {}).get("evidence", {})
    peak_bundles = evidence.get("peak_to_clusters_articles", [])
    peak_rows: list[list[Any]] = []
    peak_lookup: dict[str, Any] = {}
    for bundle in peak_bundles:
        peak_day = bundle.get("peak_day")
        clusters = bundle.get("clusters", [])
        cluster_ids = sorted([cluster.get("cluster_id") for cluster in clusters if cluster.get("cluster_id")])
        article_ids = sorted({aid for cluster in clusters for aid in (cluster.get("article_ids") or [])})
        if not peak_day:
            continue
        peak_rows.append([peak_day, bundle.get("peak_article_count"), ", ".join(cluster_ids), ", ".join(article_ids)])
        peak_lookup[peak_day] = {
            "peak_day": peak_day,
            "peak_article_count": bundle.get("peak_article_count"),
            "clusters": clusters,
            "cluster_ids": cluster_ids,
            "article_ids": article_ids,
            "bundle_id": bundle.get("bundle_id"),
        }
    return peak_rows, peak_lookup, sorted(peak_lookup.keys())


def _build_map_rows(result: dict[str, Any]) -> tuple[list[dict[str, Any]], list[list[Any]], dict[str, Any], list[str]]:
    stages = result.get("stages", {})
    artifacts = result.get("artifacts", {})
    evidence = artifacts.get("evidence_bundles") or stages.get("evidence", {})

    marker_rows = (
        artifacts.get("geospatial_entities_markers", {}).get("map_markers")
        or stages.get("geospatial", {}).get("map_markers")
        or stages.get("aggregation", {}).get("geospatial", {}).get("map_markers")
        or []
    )

    location_bundle_by_label = {
        bundle.get("location_label"): bundle
        for bundle in evidence.get("location_to_clusters_articles", [])
        if bundle.get("location_label")
    }

    rows: list[dict[str, Any]] = []
    location_lookup: dict[str, Any] = {}
    for marker in marker_rows:
        article_count = int(marker.get("unique_article_count") or len(marker.get("article_ids", [])))
        intensity = "high" if article_count >= 8 else "medium" if article_count >= 4 else "low"
        label = marker.get("location_label", "unknown")
        bundle = location_bundle_by_label.get(label, {})

        row = {
            "location_label": label,
            "latitude": marker.get("latitude"),
            "longitude": marker.get("longitude"),
            "article_count": article_count,
            "intensity": marker.get("intensity") or intensity,
            "avg_confidence": marker.get("avg_confidence"),
            "ambiguous_locations": marker.get("ambiguous_count", 0),
            "cluster_ids": sorted(bundle.get("cluster_ids", [])),
        }
        rows.append(row)
        location_lookup[label] = {
            "location_label": label,
            "location_ids": bundle.get("location_ids", marker.get("location_ids", [])),
            "cluster_ids": sorted(bundle.get("cluster_ids", [])),
            "article_ids": bundle.get("article_ids", marker.get("article_ids", [])),
            "bundle_id": bundle.get("bundle_id"),
            "avg_confidence": marker.get("avg_confidence"),
            "ambiguous_locations": marker.get("ambiguous_count", 0),
        }

    map_table_rows = [
        [
            row["location_label"],
            row["latitude"],
            row["longitude"],
            row["article_count"],
            row["intensity"],
            row["avg_confidence"],
            row["ambiguous_locations"],
            ", ".join(row["cluster_ids"]) if row["cluster_ids"] else "None",
        ]
        for row in rows
    ]

    map_bundle_rows = [
        [
            label,
            ", ".join(detail.get("location_ids", [])),
            ", ".join(detail.get("cluster_ids", [])),
            ", ".join(detail.get("article_ids", [])),
            detail.get("avg_confidence"),
            detail.get("ambiguous_locations"),
        ]
        for label, detail in sorted(location_lookup.items(), key=lambda item: item[0])
    ]

    return rows, map_table_rows, map_bundle_rows, location_lookup, sorted(location_lookup.keys())


def _get_cluster_detail(cluster_id: str, cluster_lookup_json: str) -> tuple[str, list[list[Any]]]:
    if not cluster_lookup_json or cluster_lookup_json == "{}":
        return "{}", []
    cluster_lookup = json.loads(cluster_lookup_json)
    cluster = cluster_lookup.get(cluster_id)
    if not cluster:
        return "{}", []

    article_rows = [
        [
            article.get("article_id"),
            article.get("title"),
            article.get("source"),
            article.get("published_at"),
            article.get("claim_classification"),
            article.get("duplicate_flag"),
            article.get("url"),
        ]
        for article in cluster.get("articles", [])
    ]
    return _pretty_json(cluster), article_rows


def _get_peak_detail(peak_day: str, peak_lookup_json: str) -> str:
    if not peak_lookup_json or peak_lookup_json == "{}":
        return "{}"
    peak_lookup = json.loads(peak_lookup_json)
    detail = peak_lookup.get(peak_day)
    if not detail:
        return "{}"
    return _pretty_json(detail)


def _get_location_detail(location_label: str, location_lookup_json: str) -> str:
    if not location_lookup_json or location_lookup_json == "{}":
        return "{}"
    location_lookup = json.loads(location_lookup_json)
    detail = location_lookup.get(location_label)
    if not detail:
        return "{}"
    return _pretty_json(detail)


def _build_run_summary(
    result: dict[str, Any],
    cluster_rows: list[list[Any]],
    map_rows: list[dict[str, Any]],
    citation_index: dict[str, Any],
    timeline_summary: str,
) -> str:
    stages = result.get("stages", {})
    ingestion = stages.get("ingestion", {})
    normalization = stages.get("normalization", {})
    warnings = stages.get("warnings", [])
    validation = stages.get("validation", {})

    source_runs = ingestion.get("source_runs", [])
    attempted_sources = len(ingestion.get("sources_attempted", []))
    succeeded_sources = len(ingestion.get("sources_succeeded", []))
    failed_sources = len(ingestion.get("sources_failed", []))

    warning_lines: list[str] = []
    if ingestion.get("hits_count", 0) == 0:
        warning_lines.append("No articles were ingested for this topic/date range.")
    if int(normalization.get("invalid_count", 0)) > 0:
        warning_lines.append(
            f"{normalization.get('invalid_count')} records failed normalization validation."
        )
    if failed_sources > 0:
        partial_sources = [f"{run.get('source_id')}({run.get('status')})" for run in source_runs if run.get("status") != "success"]
        warning_lines.append(f"Partial source failures: {', '.join(partial_sources)}")
    if not stages.get("aggregation", {}).get("daily_counts"):
        warning_lines.append("Timeline data is missing; trend analysis is limited.")
    if len(map_rows) == 0:
        warning_lines.append("Geospatial output is not yet available for this run.")
    if len(cluster_rows) == 0:
        warning_lines.append("Cluster output is not yet available for this run.")
    if int(citation_index.get("citation_count", 0)) == 0:
        warning_lines.append("Citation output is not yet available for this run.")

    for warning in warnings:
        warning_lines.append(f"[{warning.get('warning_code', 'warning')}] {warning.get('message', 'Analyst review required.')}")
    if validation.get("stop_recommended"):
        warning_lines.append(
            f"[validation_stop] Publish blocked ({validation.get('fail_count', 0)} fail gate(s) triggered)."
        )

    warning_text = "\n".join([f"- {line}" for line in warning_lines]) if warning_lines else "- No warnings."
    return (
        f"### Run Summary & Warnings\n"
        f"- **Status:** Completed\n"
        f"- **Run ID:** `{result.get('run_id', 'unknown-run-id')}`\n"
        f"- **Date range:** `{result.get('input', {}).get('start_date')} → {result.get('input', {}).get('end_date')}`\n"
        f"- **Source totals:** `{succeeded_sources}/{attempted_sources}` succeeded, `{failed_sources}` partial/failed\n"
        f"- **Article totals:** `{normalization.get('valid_count', 0)}` valid, `{ingestion.get('hits_count', 0)}` ingested\n"
        f"- **Validation gates:** `{validation.get('warn_count', 0)}` warn, `{validation.get('fail_count', 0)}` fail, "
        f"`can_publish={validation.get('can_publish', True)}`\n"
        f"- **Cluster totals:** `{len(cluster_rows)}`\n"
        f"- **Geospatial totals:** `{len(map_rows)}` map markers\n"
        f"- **Timeline trend:** {timeline_summary}\n\n"
        f"### Analyst Warnings / Partial Failures\n{warning_text}"
    )


def run_ui_workflow(topic: str, start_date: str, end_date: str):
    empty_fig = _timeline_figure([])
    empty_map = _build_map_plot([])
    empty_dropdown = gr.Dropdown(choices=[], value=None)

    try:
        topic, start_date_obj, end_date_obj = _validate_inputs(topic, start_date, end_date)
        result = run_workflow(
            RunInput(
                topic=topic,
                start_date=start_date_obj,
                end_date=end_date_obj,
            )
        )
    except Exception as exc:
        error_message = f"Workflow execution failed: {exc}"
        return (
            error_message,
            f"### Run Summary & Warnings\n- **Status:** Failed\n\n### Analyst Warnings / Partial Failures\n- {exc}",
            "No timeline data returned; unable to identify spikes or trend direction.",
            [],
            empty_dropdown,
            "{}",
            [],
            empty_map,
            [],
            empty_dropdown,
            "{}",
            [],
            empty_dropdown,
            "{}",
            [],
            [],
            "{}",
            [],
            "{}",
            "{}",
            "{}",
            "{}",
            "{}",
            "{}",
            "{}",
            "{}",
            "{}",
            empty_fig,
        )

    stages = result.get("stages", {})
    aggregation = stages.get("aggregation", {})

    cluster_views = _build_cluster_views(result)
    citation_rows, citation_index, evidence_bundle_rows = _build_citation_views(result)
    map_rows, map_table_rows, map_bundle_rows, location_lookup, location_choices = _build_map_rows(result)
    peak_rows, peak_lookup, peak_choices = _build_timeline_drilldown(result)

    timeline_summary = _build_timeline_summary(aggregation.get("daily_counts", []))
    run_summary = _build_run_summary(result, cluster_views["cluster_rows"], map_rows, citation_index, timeline_summary)

    status = f"Completed: {result.get('run_id', 'unknown-run-id')}"

    return (
        status,
        run_summary,
        timeline_summary,
        peak_rows,
        gr.Dropdown(choices=peak_choices, value=None),
        "{}",
        map_table_rows,
        _build_map_plot(map_rows),
        map_bundle_rows,
        gr.Dropdown(choices=location_choices, value=None),
        "{}",
        cluster_views["cluster_rows"],
        gr.Dropdown(choices=cluster_views["cluster_choices"], value=None),
        "{}",
        [],
        citation_rows,
        _pretty_json(citation_index),
        evidence_bundle_rows,
        _pretty_json({"run_id": result.get("run_id"), "started_at": result.get("started_at"), "input": result.get("input")}),
        _pretty_json(stages.get("ingestion", {})),
        _pretty_json(stages.get("normalization", {})),
        _pretty_json(stages.get("aggregation", {})),
        _pretty_json(stages.get("clustering", {})),
        _pretty_json(stages.get("geospatial", {})),
        _pretty_json({"warnings": stages.get("warnings", []), "validation": stages.get("validation", {})}),
        _pretty_json(cluster_views["cluster_lookup"]),
        _pretty_json(peak_lookup),
        _pretty_json(location_lookup),
        _timeline_figure(aggregation.get("daily_counts", [])),
    )


def build_app() -> gr.Blocks:
    today = datetime.now(timezone.utc).date()
    default_end = today
    default_start = today - timedelta(days=7)

    # with gr.Blocks(title="News Discovery Analyst Dashboard", css=DARK_LIGHT_CSS) as demo:
    with gr.Blocks(title="News Discovery Analyst Dashboard") as demo:
        gr.Markdown(
            """
# News Discovery Analyst Dashboard

Run once and review run summary, timeline, map, clusters, citations, and validation payloads from real backend artifacts.
            """.strip()
        )

        with gr.Row(elem_classes=["nd-panel"]):
            topic = gr.Textbox(label="Topic", placeholder="e.g., semiconductor", scale=3)
            start_date = gr.Textbox(
                label="Start date (YYYY-MM-DD)",
                value=str(default_start),
                placeholder="YYYY-MM-DD",
            )
            end_date = gr.Textbox(
                label="End date (YYYY-MM-DD)",
                value=str(default_end),
                placeholder="YYYY-MM-DD",
            )
            theme_selector = gr.Radio(
                label="Theme",
                choices=["Dark", "Light"],
                value="Dark",
                info="Dark is the analyst default.",
            )
            run_button = gr.Button("Run Workflow", variant="primary")

        status = gr.Textbox(label="Workflow Status", interactive=False)
        run_summary = gr.Markdown("### Run Summary & Warnings\n- Awaiting workflow execution.")

        with gr.Row():
            with gr.Column(elem_classes=["nd-panel"]):
                gr.Markdown("<div class='nd-kicker'>Timeline Panel</div>")
                timeline_plot = gr.Plot(label="Daily Article Counts")
                timeline_summary = gr.Markdown("No timeline run yet.")
                timeline_peak_table = gr.Dataframe(
                    headers=["peak_day", "peak_article_count", "cluster_ids", "article_ids"],
                    datatype=["str", "number", "str", "str"],
                    label="Peak → Cluster → Article Drill-down",
                    interactive=False,
                )
                peak_selector = gr.Dropdown(label="Peak Day Detail", choices=[], value=None, interactive=True)
                peak_detail = gr.Code(label="Peak Detail", language="json")

            with gr.Column(elem_classes=["nd-panel"]):
                gr.Markdown("<div class='nd-kicker'>Geospatial Map Panel</div>")
                map_plot = gr.Plot(label="Geospatial Map")
                map_table = gr.Dataframe(
                    headers=[
                        "location_label",
                        "latitude",
                        "longitude",
                        "article_count",
                        "intensity",
                        "avg_confidence",
                        "ambiguous_locations",
                        "cluster_ids",
                    ],
                    datatype=["str", "number", "number", "number", "str", "number", "number", "str"],
                    label="Geospatial Marker Table",
                    interactive=False,
                )
                map_bundle_table = gr.Dataframe(
                    headers=["location_label", "location_ids", "cluster_ids", "article_ids", "avg_confidence", "ambiguous_locations"],
                    datatype=["str", "str", "str", "str", "number", "number"],
                    label="Location → Cluster → Article Drill-down",
                    interactive=False,
                )
                location_selector = gr.Dropdown(label="Location Detail", choices=[], value=None, interactive=True)
                location_detail = gr.Code(label="Location Detail", language="json")

        with gr.Row():
            with gr.Column(elem_classes=["nd-panel"]):
                gr.Markdown("<div class='nd-kicker'>Cluster Explorer</div>")
                cluster_summary = gr.Dataframe(
                    headers=[
                        "cluster_id",
                        "cluster_label",
                        "article_count",
                        "distinct_sources",
                        "duplicate_articles",
                        "duplicate_ratio",
                        "top_source_ratio",
                        "duplicate_heavy",
                    ],
                    datatype=["str", "str", "number", "number", "number", "number", "number", "bool"],
                    label="Cluster Summary Table",
                    interactive=False,
                )
                cluster_selector = gr.Dropdown(label="Cluster Detail Selector", choices=[], value=None, interactive=True)
                cluster_detail = gr.Code(label="Cluster Detail", language="json")
                cluster_articles = gr.Dataframe(
                    headers=["article_id", "title", "source", "published_at", "claim_classification", "duplicate_flag", "url"],
                    datatype=["str", "str", "str", "str", "str", "bool", "str"],
                    label="Cluster Article Membership",
                    interactive=False,
                )

            with gr.Column(elem_classes=["nd-panel"]):
                gr.Markdown("<div class='nd-kicker'>Citation / Evidence Explorer</div>")
                citation_index = gr.Code(label="Citation Index", language="json")
                citations = gr.Dataframe(
                    headers=[
                        "citation_id",
                        "article_id",
                        "cluster_id",
                        "source",
                        "publication_date",
                        "url",
                        "claim_classification",
                        "title",
                    ],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "str"],
                    label="Citation Records",
                    interactive=False,
                )
                evidence_bundle = gr.Dataframe(
                    headers=["bundle_id", "bundle_type", "bundle_subject", "article_id", "linked_ids"],
                    datatype=["str", "str", "str", "str", "str"],
                    label="Evidence Bundle View",
                    interactive=False,
                )

        with gr.Accordion("Validation Panels", open=False):
            meta = gr.Code(label="Run Metadata", language="json")
            ingestion = gr.Code(label="Ingestion Payload", language="json")
            normalization = gr.Code(label="Normalization Payload", language="json")
            aggregation = gr.Code(label="Aggregation Payload", language="json")
            cluster_payload = gr.Code(label="Cluster Payload", language="json")
            geospatial_payload = gr.Code(label="Geospatial Payload", language="json")
            warning_payload = gr.Code(label="Warning Payload", language="json")

        cluster_lookup = gr.Textbox(value="{}", visible=False)
        peak_lookup = gr.Textbox(value="{}", visible=False)
        location_lookup = gr.Textbox(value="{}", visible=False)

        theme_selector.change(
            fn=lambda theme: None,
            inputs=[theme_selector],
            outputs=[],
            js="""
            (theme) => {
              const body = document.body;
              if (theme === 'Light') {
                body.classList.add('nd-light');
              } else {
                body.classList.remove('nd-light');
              }
              return [];
            }
            """,
        )

        cluster_selector.change(
            fn=_get_cluster_detail,
            inputs=[cluster_selector, cluster_lookup],
            outputs=[cluster_detail, cluster_articles],
        )
        peak_selector.change(
            fn=_get_peak_detail,
            inputs=[peak_selector, peak_lookup],
            outputs=[peak_detail],
        )
        location_selector.change(
            fn=_get_location_detail,
            inputs=[location_selector, location_lookup],
            outputs=[location_detail],
        )

        run_button.click(
            fn=run_ui_workflow,
            inputs=[topic, start_date, end_date],
            outputs=[
                status,
                run_summary,
                timeline_summary,
                timeline_peak_table,
                peak_selector,
                peak_detail,
                map_table,
                map_plot,
                map_bundle_table,
                location_selector,
                location_detail,
                cluster_summary,
                cluster_selector,
                cluster_detail,
                cluster_articles,
                citations,
                citation_index,
                evidence_bundle,
                meta,
                ingestion,
                normalization,
                aggregation,
                cluster_payload,
                geospatial_payload,
                warning_payload,
                cluster_lookup,
                peak_lookup,
                location_lookup,
                timeline_plot,
            ],
        )

    return demo


def main() -> None:
    demo = build_app()
    # demo.launch(server_name="0.0.0.0", server_port=7860, share=True)
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=True,
        debug=True,
        inline=False,
        css=DARK_CSS,
    )


if __name__ == "__main__":
    main()
