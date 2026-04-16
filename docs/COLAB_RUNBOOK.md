# COLAB_RUNBOOK

## Purpose
Run the analyst dashboard in Google Colab using the repository workflow and Gradio launch with `share=True`.

## Launch (Colab)
1. Open `notebooks/news_discovery_colab.ipynb`.
2. Run setup/install cells.
3. Ensure the launch cell runs `demo.launch(share=True, inline=False, debug=True)`.
4. Open the public Gradio URL.

## Analyst Workflow in Colab UI
1. Enter `topic`, `start_date`, `end_date`.
2. Click **Run Workflow**.
3. Review **Workflow Status** and **Run Summary**.
4. Inspect:
   - Timeline plot + trend summary,
   - Geospatial map + marker table,
   - Cluster summary/detail + membership,
   - Citation index/records + evidence bundle,
   - Raw stage outputs in validation accordion.

## Expected Behavior
- Dashboard remains fully usable from browser (no CLI needed for analysts).
- If workflow lacks geospatial/cluster/citation data for a run, panels show explicit no-data/empty states and warnings.
- Input validation failures are shown immediately in status/summary.

## Validation Checks for Colab
- Confirm run summary includes run ID and counts.
- Confirm timeline values match `aggregation.daily_counts`.
- Confirm cluster and citation tables reference real article IDs from normalization output.
- Confirm map panel only shows markers when coordinate-bearing records are present.

## Known Colab Constraints
- First launch may be slower due to environment cold start.
- External source/network availability affects ingestion results.
- Geospatial panel may be empty when upstream artifacts do not include coordinates.
