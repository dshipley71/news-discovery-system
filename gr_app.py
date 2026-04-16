from __future__ import annotations

import json
import re
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go

from src.news_app.workflow import RunInput, run_workflow


DARK_CSS = """
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


def _timeline_figure(daily_counts: list[dict[str, Any]]):
    fig, ax = plt.subplots(figsize=(10, 4))

    if not daily_counts:
        ax.text(0.5, 0.5, "No timeline data returned.", ha="center", va="center")
        ax.set_title("Daily Article Counts")
        ax.set_xlabel("Date")
        ax.set_ylabel("Articles")
        fig.tight_layout()
        return fig

    days = [point["day"] for point in daily_counts]
    counts = [point["article_count"] for point in daily_counts]

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

    total_articles = sum(point.get("article_count", 0) for point in daily_counts)
    peak_day = max(daily_counts, key=lambda point: point.get("article_count", 0))
    first_count = daily_counts[0].get("article_count", 0)
    last_count = daily_counts[-1].get("article_count", 0)
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
        "uncertainty": [row["uncertainty"] for row in map_rows],
        "ambiguous_locations": [row["ambiguous_locations"] for row in map_rows],
        "cluster_ids": [", ".join(row["cluster_ids"]) if row["cluster_ids"] else "None" for row in map_rows],
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
            "uncertainty": True,
            "ambiguous_locations": True,
            "cluster_ids": True,
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


def _extract_map_rows(result: dict[str, Any], canonical_articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    stages = result.get("stages", {})
    aggregation = stages.get("aggregation", {})
    markers = aggregation.get("geospatial", {}).get("map_markers", [])

    rows: list[dict[str, Any]] = []
    for marker in markers:
        lat = marker.get("latitude") or marker.get("lat")
        lon = marker.get("longitude") or marker.get("lon")
        if lat is None or lon is None:
            continue

        article_ids = marker.get("article_ids", [])
        article_count = marker.get("unique_article_count") or marker.get("article_count") or len(article_ids)
        if article_count >= 8:
            intensity = "high"
        elif article_count >= 4:
            intensity = "medium"
        else:
            intensity = "low"

        avg_conf = marker.get("avg_confidence")
        uncertainty = round(max(0.0, 1.0 - float(avg_conf)), 3) if avg_conf is not None else 0.5

        rows.append(
            {
                "location_label": marker.get("location_label", "unknown"),
                "latitude": float(lat),
                "longitude": float(lon),
                "article_count": int(article_count),
                "intensity": marker.get("intensity") or intensity,
                "uncertainty": marker.get("uncertainty") or uncertainty,
                "ambiguous_locations": int(marker.get("ambiguous_count") or marker.get("ambiguous_locations") or 0),
                "cluster_ids": marker.get("cluster_ids") or [],
            }
        )

    if rows:
        return rows

    # Graceful fallback for partial upstream outputs where normalized articles may already include coordinates.
    for article in canonical_articles:
        lat = article.get("latitude")
        lon = article.get("longitude")
        if lat is None or lon is None:
            continue
        rows.append(
            {
                "location_label": article.get("location", "article-location"),
                "latitude": float(lat),
                "longitude": float(lon),
                "article_count": 1,
                "intensity": "low",
                "uncertainty": article.get("uncertainty", 0.5),
                "ambiguous_locations": int(article.get("ambiguity_flag", False)),
                "cluster_ids": article.get("cluster_ids") or [],
            }
        )

    if not rows:
        return []

    grouped: dict[tuple[float, float, str], dict[str, Any]] = {}
    for row in rows:
        key = (row["latitude"], row["longitude"], row["location_label"])
        current = grouped.setdefault(
            key,
            {
                "location_label": row["location_label"],
                "latitude": row["latitude"],
                "longitude": row["longitude"],
                "article_count": 0,
                "uncertainty_total": 0.0,
                "uncertainty_count": 0,
                "ambiguous_locations": 0,
                "cluster_ids": set(),
            },
        )
        current["article_count"] += row["article_count"]
        current["uncertainty_total"] += float(row["uncertainty"])
        current["uncertainty_count"] += 1
        current["ambiguous_locations"] += row["ambiguous_locations"]
        current["cluster_ids"].update(row["cluster_ids"])

    normalized_rows: list[dict[str, Any]] = []
    for current in grouped.values():
        article_count = current["article_count"]
        intensity = "high" if article_count >= 8 else "medium" if article_count >= 4 else "low"
        normalized_rows.append(
            {
                "location_label": current["location_label"],
                "latitude": current["latitude"],
                "longitude": current["longitude"],
                "article_count": article_count,
                "intensity": intensity,
                "uncertainty": round(current["uncertainty_total"] / max(1, current["uncertainty_count"]), 3),
                "ambiguous_locations": current["ambiguous_locations"],
                "cluster_ids": sorted(current["cluster_ids"]),
            }
        )
    return normalized_rows


def _pretty_json(data: Any) -> str:
    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


def _normalize_title_key(title: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", " ", str(title or "").lower()).strip()
    return re.sub(r"\s+", " ", cleaned)


def _derive_cluster_and_citation_views(
    canonical_articles: list[dict[str, Any]],
) -> dict[str, Any]:
    if not canonical_articles:
        return {
            "cluster_rows": [],
            "cluster_choices": [],
            "cluster_lookup": {},
            "citation_rows": [],
            "citation_index": {
                "citation_count": 0,
                "claim_classification_counts": {
                    "supported": 0,
                    "inferred": 0,
                    "speculative": 0,
                },
                "by_source": {},
            },
            "evidence_bundle_rows": [],
        }

    duplicate_key_counts: dict[str, int] = {}
    for article in canonical_articles:
        duplicate_key = _normalize_title_key(article.get("title", ""))
        duplicate_key_counts[duplicate_key] = duplicate_key_counts.get(duplicate_key, 0) + 1

    clusters: dict[str, dict[str, Any]] = {}
    citation_rows: list[list[Any]] = []
    source_totals: dict[str, int] = {}
    class_counts = {"supported": 0, "inferred": 0, "speculative": 0}
    evidence_bundle_rows: list[list[Any]] = []

    for article in canonical_articles:
        published_raw = str(article.get("published_at", ""))
        try:
            day = datetime.fromisoformat(published_raw.replace("Z", "+00:00")).date().isoformat()
        except ValueError:
            day = "unknown"

        cluster_id = f"cluster:{day}"
        cluster = clusters.setdefault(
            cluster_id,
            {
                "cluster_id": cluster_id,
                "cluster_label": f"Stories for {day}",
                "article_ids": [],
                "articles": [],
                "source_counts": {},
                "duplicate_count": 0,
            },
        )

        article_id = article.get("article_id")
        source = article.get("source", "unknown")
        duplicate_key = _normalize_title_key(article.get("title", ""))
        duplicate_flag = duplicate_key_counts.get(duplicate_key, 0) > 1

        cluster["article_ids"].append(article_id)
        cluster["articles"].append(
            {
                "article_id": article_id,
                "title": article.get("title"),
                "source": source,
                "published_at": published_raw,
                "url": article.get("url"),
                "duplicate_flag": duplicate_flag,
            }
        )
        cluster["source_counts"][source] = cluster["source_counts"].get(source, 0) + 1
        cluster["duplicate_count"] += int(duplicate_flag)

        source_totals[source] = source_totals.get(source, 0) + 1

        claim_classification = article.get("claim_classification")
        if claim_classification not in {"supported", "inferred", "speculative"}:
            if duplicate_flag:
                claim_classification = "inferred"
            elif article.get("url"):
                claim_classification = "supported"
            else:
                claim_classification = "speculative"

        class_counts[claim_classification] = class_counts.get(claim_classification, 0) + 1
        citation_id = f"cite:{article_id}"
        citation_rows.append(
            [
                citation_id,
                article_id,
                cluster_id,
                source,
                article.get("published_at"),
                article.get("url"),
                claim_classification,
                duplicate_flag,
            ]
        )
        evidence_bundle_rows.append(
            [
                f"bundle:{cluster_id}",
                "cluster_support",
                cluster_id,
                article_id,
                citation_id,
                article.get("source"),
            ]
        )

    cluster_rows: list[list[Any]] = []
    cluster_lookup: dict[str, Any] = {}
    sorted_cluster_ids = sorted(clusters.keys())
    for cluster_id in sorted_cluster_ids:
        cluster = clusters[cluster_id]
        article_count = len(cluster["article_ids"])
        distinct_sources = len(cluster["source_counts"])
        top_source = max(
            cluster["source_counts"].items(),
            key=lambda item: item[1],
        )
        source_bias_ratio = round(top_source[1] / article_count, 3) if article_count else 0.0
        duplicate_ratio = round(cluster["duplicate_count"] / article_count, 3) if article_count else 0.0
        cluster["source_bias"] = {
            "top_source": top_source[0],
            "top_source_articles": top_source[1],
            "top_source_ratio": source_bias_ratio,
            "distinct_sources": distinct_sources,
        }
        cluster["duplicate_ratio"] = duplicate_ratio
        cluster["duplicate_heavy"] = duplicate_ratio >= 0.5
        cluster_lookup[cluster_id] = cluster
        cluster_rows.append(
            [
                cluster_id,
                cluster["cluster_label"],
                article_count,
                distinct_sources,
                cluster["duplicate_count"],
                duplicate_ratio,
                source_bias_ratio,
                cluster["duplicate_heavy"],
            ]
        )

    citation_index = {
        "citation_count": len(citation_rows),
        "claim_classification_counts": class_counts,
        "by_source": source_totals,
    }

    return {
        "cluster_rows": cluster_rows,
        "cluster_choices": sorted_cluster_ids,
        "cluster_lookup": cluster_lookup,
        "citation_rows": citation_rows,
        "citation_index": citation_index,
        "evidence_bundle_rows": evidence_bundle_rows,
    }


def _get_cluster_detail(
    cluster_id: str,
    cluster_lookup_json: str,
) -> tuple[str, list[list[Any]]]:
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
            article.get("duplicate_flag"),
            article.get("url"),
        ]
        for article in cluster.get("articles", [])
    ]
    detail = {
        "cluster_id": cluster.get("cluster_id"),
        "cluster_label": cluster.get("cluster_label"),
        "article_count": len(cluster.get("article_ids", [])),
        "duplicate_count": cluster.get("duplicate_count"),
        "duplicate_ratio": cluster.get("duplicate_ratio"),
        "duplicate_heavy": cluster.get("duplicate_heavy"),
        "source_bias": cluster.get("source_bias"),
    }
    return _pretty_json(detail), article_rows


def _build_run_summary(
    result: dict[str, Any],
    cluster_rows: list[list[Any]],
    map_rows: list[dict[str, Any]],
    citation_index: dict[str, Any],
    timeline_summary: str,
) -> tuple[str, str]:
    stages = result.get("stages", {})
    ingestion = stages.get("ingestion", {})
    normalization = stages.get("normalization", {})
    aggregation = stages.get("aggregation", {})

    cluster_total = len(cluster_rows)
    location_total = len(map_rows)
    article_total = normalization.get("valid_count", 0)

    warnings: list[str] = []
    if ingestion.get("hits_count", 0) == 0:
        warnings.append("No articles were ingested for this topic/date range.")
    if normalization.get("invalid_count", 0) > 0:
        warnings.append(
            f"{normalization.get('invalid_count')} records failed normalization validation."
        )
    if not aggregation.get("daily_counts"):
        warnings.append("Timeline data is missing; trend analysis is limited.")
    if location_total == 0:
        warnings.append("Geospatial output is not yet available for this run.")
    if cluster_total == 0:
        warnings.append("Cluster output is not yet available for this run.")
    if citation_index.get("citation_count", 0) == 0:
        warnings.append("Citation output is not yet available for this run.")

    speculative_count = citation_index.get("claim_classification_counts", {}).get("speculative", 0)
    if speculative_count > 0:
        warnings.append(
            f"{speculative_count} citation(s) are marked speculative; treat summary conclusions cautiously."
        )

    duplicate_heavy_clusters = sum(1 for row in cluster_rows if row[7])
    if duplicate_heavy_clusters > 0:
        warnings.append(
            f"{duplicate_heavy_clusters} duplicate-heavy cluster(s) detected; validate spike claims with source diversity."
        )

    warning_text = "\n".join([f"- {line}" for line in warnings]) if warnings else "- No warnings."
    summary = (
        f"### Run Summary\n"
        f"- **Status:** Completed\n"
        f"- **Run ID:** `{result.get('run_id', 'unknown-run-id')}`\n"
        f"- **Date range:** `{result.get('input', {}).get('start_date')} → {result.get('input', {}).get('end_date')}`\n"
        f"- **Article total:** `{article_total}`\n"
        f"- **Cluster total:** `{cluster_total}`\n"
        f"- **Location total:** `{location_total}`\n"
        f"- **Timeline trend:** {timeline_summary}\n\n"
        f"### Analyst Warnings\n{warning_text}"
    )
    return summary, warning_text


def run_ui_workflow(topic: str, start_date: str, end_date: str):
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
        empty_fig = _timeline_figure([])
        empty_map = _build_map_plot([])
        return (
            error_message,
            f"### Run Summary\n- **Status:** Failed\n\n### Analyst Warnings\n- {exc}",
            "No timeline data returned; unable to identify spikes or trend direction.",
            [],
            empty_map,
            "{}",
            "{}",
            "{}",
            "{}",
            [],
            [],
            "{}",
            [],
            gr.Dropdown(choices=[], value=None),
            "{}",
            "{}",
            [],
            empty_fig,
        )

    meta = {
        "run_id": result.get("run_id"),
        "started_at": result.get("started_at"),
        "input": result.get("input"),
    }
    stages = result.get("stages", {})
    ingestion = stages.get("ingestion", {})
    normalization = stages.get("normalization", {})
    aggregation = stages.get("aggregation", {})

    cluster_views = _derive_cluster_and_citation_views(normalization.get("canonical_articles", []))
    map_rows = _extract_map_rows(result, normalization.get("canonical_articles", []))

    timeline_summary = _build_timeline_summary(aggregation.get("daily_counts", []))
    run_summary, _ = _build_run_summary(
        result,
        cluster_views["cluster_rows"],
        map_rows,
        cluster_views["citation_index"],
        timeline_summary,
    )

    map_table_rows = [
        [
            row["location_label"],
            row["latitude"],
            row["longitude"],
            row["article_count"],
            row["intensity"],
            row["uncertainty"],
            row["ambiguous_locations"],
            ", ".join(row["cluster_ids"]) if row["cluster_ids"] else "None",
        ]
        for row in map_rows
    ]

    status = f"Completed: {result.get('run_id', 'unknown-run-id')}"

    return (
        status,
        run_summary,
        timeline_summary,
        map_table_rows,
        _build_map_plot(map_rows),
        _pretty_json(meta),
        _pretty_json(ingestion),
        _pretty_json(normalization),
        _pretty_json(aggregation),
        cluster_views["cluster_rows"],
        cluster_views["citation_rows"],
        _pretty_json(cluster_views["citation_index"]),
        cluster_views["evidence_bundle_rows"],
        gr.Dropdown(choices=cluster_views["cluster_choices"], value=None),
        _pretty_json(cluster_views["cluster_lookup"]),
        "{}",
        [],
        _timeline_figure(aggregation.get("daily_counts", [])),
    )


def build_app() -> gr.Blocks:
    today = datetime.now(timezone.utc).date()
    default_end = today
    default_start = today - timedelta(days=7)

    with gr.Blocks(title="News Discovery Analyst Dashboard", css=DARK_CSS) as demo:
        gr.Markdown(
            """
# News Discovery Analyst Dashboard

Run the workflow once, then inspect timeline, map, clusters, citations, and raw artifacts from one UI.
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
            run_button = gr.Button("Run Workflow", variant="primary")

        status = gr.Textbox(label="Workflow Status", interactive=False)
        run_summary = gr.Markdown("### Run Summary\n- Awaiting workflow execution.")

        with gr.Row():
            with gr.Column(elem_classes=["nd-panel"]):
                gr.Markdown("<div class='nd-kicker'>Timeline Analysis</div>")
                timeline_plot = gr.Plot(label="Daily Article Counts")
                timeline_summary = gr.Markdown("No timeline run yet.")

            with gr.Column(elem_classes=["nd-panel"]):
                gr.Markdown("<div class='nd-kicker'>Geospatial Activity</div>")
                map_plot = gr.Plot(label="Geospatial Map")
                map_table = gr.Dataframe(
                    headers=[
                        "location_label",
                        "latitude",
                        "longitude",
                        "article_count",
                        "intensity",
                        "uncertainty",
                        "ambiguous_locations",
                        "cluster_ids",
                    ],
                    datatype=["str", "number", "number", "number", "str", "number", "number", "str"],
                    label="Geospatial Marker Table",
                    interactive=False,
                )

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
                cluster_selector = gr.Dropdown(
                    label="Cluster Detail Selector",
                    choices=[],
                    value=None,
                    interactive=True,
                )
                cluster_lookup = gr.Textbox(label="Cluster Lookup (internal)", value="{}", visible=False)
                cluster_detail = gr.Code(label="Cluster Detail", language="json")
                cluster_articles = gr.Dataframe(
                    headers=["article_id", "title", "source", "published_at", "duplicate_flag", "url"],
                    datatype=["str", "str", "str", "str", "bool", "str"],
                    label="Cluster Article Membership",
                    interactive=False,
                )

            with gr.Column(elem_classes=["nd-panel"]):
                gr.Markdown("<div class='nd-kicker'>Citation & Evidence Explorer</div>")
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
                        "duplicate_flag",
                    ],
                    datatype=["str", "str", "str", "str", "str", "str", "str", "bool"],
                    label="Citation Records",
                    interactive=False,
                )
                evidence_bundle = gr.Dataframe(
                    headers=["bundle_id", "bundle_type", "bundle_subject_id", "article_id", "citation_id", "source"],
                    datatype=["str", "str", "str", "str", "str", "str"],
                    label="Evidence Bundle View",
                    interactive=False,
                )

        with gr.Accordion("Validation & Raw Workflow Outputs", open=False):
            meta = gr.Code(label="Run Metadata", language="json")
            ingestion = gr.Code(label="Ingestion Output", language="json")
            normalization = gr.Code(label="Normalization Output", language="json")
            aggregation = gr.Code(label="Aggregation Output", language="json")

        cluster_selector.change(
            fn=_get_cluster_detail,
            inputs=[cluster_selector, cluster_lookup],
            outputs=[cluster_detail, cluster_articles],
        )

        run_button.click(
            fn=run_ui_workflow,
            inputs=[topic, start_date, end_date],
            outputs=[
                status,
                run_summary,
                timeline_summary,
                map_table,
                map_plot,
                meta,
                ingestion,
                normalization,
                aggregation,
                cluster_summary,
                citations,
                citation_index,
                evidence_bundle,
                cluster_selector,
                cluster_lookup,
                cluster_detail,
                cluster_articles,
                timeline_plot,
            ],
        )

    return demo


def main() -> None:
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)


if __name__ == "__main__":
    main()
