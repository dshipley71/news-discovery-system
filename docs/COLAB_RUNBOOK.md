# COLAB_RUNBOOK

## Purpose
This runbook explains how to run the News Discovery workflow in Google Colab using `notebooks/news_discovery_colab.ipynb`, launch Gradio with `share=True`, and validate each analyst-facing stage from the UI.

## What this notebook runs
The notebook reuses the existing repository workflow (`run_workflow`) and adds a UI-level geospatial rendering layer:

1. Ingestion (real API pull)
2. Normalization (canonical articles + validation issues)
3. Aggregation (daily counts)
4. Timeline plot
5. Geospatial extraction + map markers rendered in Gradio

No simulated data is introduced.

---

## Run instructions (Google Colab)

1. Open `notebooks/news_discovery_colab.ipynb` in Google Colab.
2. Run all cells top-to-bottom in order.
3. In the **Project load** cell:
   - set `REPO_URL` to your repository URL (first run in clean runtime only).
4. Run the final launch cell.
5. Open the public Gradio URL printed by `demo.launch(share=True, inline=False, debug=True)`.

---

## UI inputs and outputs

### Inputs
- `topic`
- `start_date (YYYY-MM-DD)`
- `end_date (YYYY-MM-DD)`

### Outputs
- `ingestion JSON`
- `normalization JSON`
- `aggregation JSON` (includes geospatial substructure)
- `timeline plot`
- `geospatial map`

---

## Validation steps (analyst)

### 1) Ingestion success
- Confirm `ingestion JSON.hits_count > 0` for active topics.
- Confirm `ingestion JSON.raw_hits` is populated.

### 2) Location extraction correctness
- Open `aggregation JSON.geospatial.location_entities`.
- Verify records include:
  - `article_id`
  - `latitude` / `longitude`
  - `confidence_score`
  - `evidence_text_span`
  - `ambiguity_flag`

### 3) Aggregation correctness
- Verify `aggregation JSON.daily_counts` aligns with normalized article publish dates.
- Verify `aggregation JSON.geospatial.map_markers` groups article IDs by resolved location.

### 4) Timeline accuracy
- Confirm each plotted point equals the corresponding `daily_counts[].article_count` value.

### 5) Map correctness
- Confirm markers render in the Gradio map panel.
- Confirm marker popup displays:
  - intensity band
  - uncertainty score
  - article links
  - cluster IDs when present (or `None` when unavailable)

---

## Geospatial behavior in this notebook
- Location candidates are extracted from article titles (real normalization output).
- Candidates are geocoded using `geopy` (`Nominatim`).
- Marker intensity is derived from unique article count per grouped location.
- Uncertainty is represented as `1 - avg_confidence`.
- Ambiguity is highlighted with marker outline styling and ambiguity counters.

---

## Limitations
1. Geocoding quality depends on public geocoder response quality and rate limits.
2. Title-only location extraction can miss locations present only in body text.
3. Cluster links are shown only if cluster IDs exist in upstream records.
4. First run in Colab can be slower due to dependency install and cold geocoder cache.

---

## Recommended next step
Move the notebook geospatial extraction logic into a reusable repository workflow stage (e.g., `src/news_app/geospatial.py`) so local app and Colab app share one audited implementation path.
