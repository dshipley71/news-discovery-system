from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta, timezone
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt

from src.news_app.workflow import RunInput, run_workflow


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

    ax.plot(days, counts, marker="o")
    ax.set_title("Daily Article Counts")
    ax.set_xlabel("Date")
    ax.set_ylabel("Articles")
    ax.tick_params(axis="x", rotation=45)
    fig.tight_layout()
    return fig


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

        if duplicate_flag:
            claim_classification = "inferred"
        elif source == "hackernews":
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
        return (
            error_message,
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

    fig = _timeline_figure(aggregation.get("daily_counts", []))
    status = f"Completed: {result.get('run_id', 'unknown-run-id')}"

    return (
        status,
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
        fig,
    )


def build_app() -> gr.Blocks:
    today = datetime.now(timezone.utc).date()
    default_end = today
    default_start = today - timedelta(days=7)

    with gr.Blocks(title="News Discovery MVP") as demo:
        gr.Markdown(
            """
# News Discovery MVP (Vertical Slice)

UI intake → real ingestion → normalization → daily timeline.
            """.strip()
        )

        with gr.Row():
            topic = gr.Textbox(
                label="Topic",
                placeholder="e.g., semiconductor",
                scale=2,
            )
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

        run_button = gr.Button("Run Workflow")
        status = gr.Textbox(label="Status", interactive=False)

        with gr.Accordion("Run Metadata", open=True):
            meta = gr.Code(label="Run Metadata", language="json")

        with gr.Accordion("Step 1: Ingestion Validation", open=False):
            ingestion = gr.Code(label="Ingestion Output", language="json")

        with gr.Accordion("Step 2: Normalization Validation", open=False):
            normalization = gr.Code(label="Normalization Output", language="json")

        with gr.Accordion("Step 3: Aggregation + Timeline Validation", open=True):
            timeline_plot = gr.Plot(label="Daily Article Counts")
            aggregation = gr.Code(label="Aggregation Output", language="json")

        with gr.Accordion("Step 4: Cluster + Citation Explorer", open=True):
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
            cluster_lookup = gr.Textbox(
                label="Cluster Lookup (internal)",
                value="{}",
                visible=False,
            )
            cluster_detail = gr.Code(label="Cluster Detail Panel", language="json")
            cluster_articles = gr.Dataframe(
                headers=[
                    "article_id",
                    "title",
                    "source",
                    "published_at",
                    "duplicate_flag",
                    "url",
                ],
                datatype=["str", "str", "str", "str", "bool", "str"],
                label="Article List per Cluster",
                interactive=False,
            )
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
                headers=[
                    "bundle_id",
                    "bundle_type",
                    "bundle_subject_id",
                    "article_id",
                    "citation_id",
                    "source",
                ],
                datatype=["str", "str", "str", "str", "str", "str"],
                label="Evidence Bundle View",
                interactive=False,
            )

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
