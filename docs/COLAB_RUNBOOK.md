# COLAB_RUNBOOK

## Purpose
Run the Gradio analyst review dashboard in Google Colab with backend artifact-driven panels.

## Launch in Colab
1. Open `notebooks/news_discovery_colab.ipynb`.
2. Run setup/install cells.
3. Confirm launch cell runs Gradio app with `share=True`.
4. Open generated public Gradio URL.

## Analyst Execution Flow (UI-Only)
1. Set `Topic`, `Start date`, and `End date` in Control Panel.
2. (Optional) keep default `Dark` theme or switch to `Light`.
3. Click **Run Workflow**.
4. Review **Run Summary & Warnings**:
   - run id
   - date range
   - source totals
   - article totals
   - cluster totals
   - geospatial totals
   - analyst warnings / partial failures

5. Review dashboard regions:
   - **Timeline panel**: daily counts, trend summary, peak drill-down
   - **Geospatial panel**: markers, confidence/ambiguity cues, location drill-down
   - **Cluster explorer**: cluster summary, details, membership, diversity/duplicate indicators
   - **Citation / Evidence explorer**: citation index, citation rows, bundle rows
   - **Validation panels**: ingestion, normalization, aggregation, cluster, geospatial, warning payloads

## Colab Validation Checklist
- Run summary numbers align with payload data.
- Timeline drill-down links peak day to clusters/articles.
- Map drill-down links location to clusters/articles.
- Cluster membership references real article IDs.
- Citation/evidence records are artifact-backed.
- Warnings are explicit for missing or partial outputs.

## Known Colab Constraints
- First run can be slower due to cold start.
- External source availability/rate limiting may produce partial source failures.
- Geospatial panel may legitimately remain empty when no location-bearing entities are extracted.
- Browser rendering differences may affect map interactivity but should not affect payload traceability.
