from __future__ import annotations

import json
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

    fig = _timeline_figure(aggregation.get("daily_counts", []))
    status = f"Completed: {result.get('run_id', 'unknown-run-id')}"

    return (
        status,
        _pretty_json(meta),
        _pretty_json(ingestion),
        _pretty_json(normalization),
        _pretty_json(aggregation),
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

        run_button.click(
            fn=run_ui_workflow,
            inputs=[topic, start_date, end_date],
            outputs=[status, meta, ingestion, normalization, aggregation, timeline_plot],
        )

    return demo


def main() -> None:
    demo = build_app()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=True)


if __name__ == "__main__":
    main()
