# Failure Modes and Trust Gates (Gradio + Colab Workflow)

## Purpose
This document defines analyst-facing failure handling for the in-repo workflow (`gr_app.py` + `src/news_app/workflow.py`) with explicit **warn vs stop** behavior.

## Severity model
- **WARN:** run continues, but analyst trust is reduced.
- **STOP:** run remains inspectable, but report publication/decision handoff is blocked.

## Failure Mode Matrix

### FM-001 Duplicate article inflation
- **Description:** Duplicate or near-duplicate stories can overstate activity.
- **How it appears here:** Multi-source ingestion can return the same URL/headline across sources; dedup telemetry includes `ingestion_duplicate_ratio` and `duplicate_map`.
- **Detection rule:**
  - WARN if `duplicate_ratio >= 0.35`.
  - STOP if `duplicate_ratio >= 0.60`.
- **Prevention rule:** Canonical dedup key by normalized URL (fallback title+day), preserve duplicate lineage map.
- **Analyst-visible UI signal:** Warning/validation event with measured duplicate ratio and remediation.
- **Fallback behavior:** Continue on canonical article set, keep duplicate lineage table inspectable.
- **Stop condition:** Severe duplicate inflation (`>= 0.60`).

### FM-002 Source-specific failure
- **Description:** One or more sources fail/skipped due to outage/auth/adapter error.
- **How it appears here:** `source_runs` include per-source status (`success`/`skipped`/`failed`), warnings, and error fields; ingestion also reports `sources_skipped` and `sources_empty`.
- **Detection rule:**
  - WARN if any source status is non-success.
  - STOP if all attempted sources are non-success.
- **Prevention rule:** Isolate source adapters, continue partial run when at least one source succeeds.
- **Analyst-visible UI signal:** Run summary shows source success/failure counts and per-source states.
- **Fallback behavior:** Use surviving sources and lower confidence.
- **Stop condition:** Zero successful sources.

### FM-012 Timeline-to-normalization mismatch
- **Description:** Aggregation totals diverge from canonical article totals, causing misleading trend summaries.
- **How it appears here:** `stages.aggregation.daily_counts` sum does not match `stages.normalization.valid_count`.
- **Detection rule:** STOP when timeline total differs from canonical valid count.
- **Prevention rule:** Robust date parsing and fallback day bucketing to avoid silent row drops.
- **Analyst-visible UI signal:** Critical validation gate with measured `timeline_total` vs `valid_count`.
- **Fallback behavior:** Keep run inspectable, but block publication until date normalization is corrected.
- **Stop condition:** Any non-zero mismatch.

### FM-003 Rate limiting and backoff behavior
- **Description:** Upstream 429s or throttling can reduce freshness and coverage.
- **How it appears here:** Source metadata captures retry behavior (`json_retried_429`, attempts).
- **Detection rule:** WARN when retry/backoff path is used by any source.
- **Prevention rule:** Per-source retry with bounded attempts, explicit metadata recording.
- **Analyst-visible UI signal:** Validation warning event includes impacted sources.
- **Fallback behavior:** Continue run with explicit rate-limit warning.
- **Stop condition:** Covered by FM-002 when throttling causes all sources to fail.

### FM-004 Empty ingestion
- **Description:** Run produces no usable canonical evidence.
- **How it appears here:** `normalization.valid_count == 0`.
- **Detection rule:** STOP when `valid_count == 0`.
- **Prevention rule:** Preserve empty-state artifacts and block confidence claims.
- **Analyst-visible UI signal:** Critical trust gate in validation stage + run summary warning.
- **Fallback behavior:** Prompt analyst to broaden query/date range.
- **Stop condition:** Always stop on empty canonical set.

### FM-005 Schema drift across sources
- **Description:** Source payload shape changes causing normalization drops.
- **How it appears here:** Growing `normalization.invalid_count`/missing required fields.
- **Detection rule:**
  - WARN if invalid ratio `>= 0.20`.
  - STOP if invalid ratio `>= 0.50`.
- **Prevention rule:** Required field checks (`title`, `published_at`, `source`) with validation issue logging.
- **Analyst-visible UI signal:** Validation event with invalid ratio/count.
- **Fallback behavior:** Continue using valid canonical subset.
- **Stop condition:** Majority invalid records.

### FM-006 Weak source diversity
- **Description:** Single-source evidence undermines corroboration.
- **How it appears here:** Canonical set has <=1 unique source.
- **Detection rule:** WARN when `unique_sources <= 1` with non-trivial evidence volume.
- **Prevention rule:** Multi-source ingestion default and diversity warning gate.
- **Analyst-visible UI signal:** `weak_source_diversity` warning and validation event.
- **Fallback behavior:** Continue as provisional intelligence only.
- **Stop condition:** None by default (warn-level trust reduction).

### FM-007 Misleading timeline spikes (duplication/batching)
- **Description:** Spikes may be ingestion artifacts, not real-world signal.
- **How it appears here:** One-day peak dominates counts while duplicate ratio is elevated.
- **Detection rule:** WARN if `peak_day_ratio >= 0.70` and duplicate ratio `>= 0.35`.
- **Prevention rule:** Build timeline from canonical deduped records and preserve peak drill-down bundles.
- **Analyst-visible UI signal:** Validation warning for spike reliability degradation.
- **Fallback behavior:** Require peak-to-cluster/article drill-down before interpretation.
- **Stop condition:** None by default (warn-level caution).

### FM-008 Low-confidence geospatial inference
- **Description:** Location extraction is ambiguous/low-confidence.
- **How it appears here:** Entities with `ambiguity_flag` or low confidence.
- **Detection rule:** WARN when all extracted geospatial entities are weak (ambiguous or <0.7 confidence).
- **Prevention rule:** Keep confidence, ambiguity notes, and evidence linkage per entity.
- **Analyst-visible UI signal:** `low_confidence_geo` warning + validation event metrics.
- **Fallback behavior:** Keep map visible, mark location conclusions as unverified.
- **Stop condition:** None by default.

### FM-009 Weak or duplicate-heavy clusters
- **Description:** Clusters with low support can mislead pattern interpretation.
- **How it appears here:** Cluster confidence <0.55 or singleton clusters dominate.
- **Detection rule:** WARN when weak cluster ratio `>= 0.75`.
- **Prevention rule:** Deterministic clustering plus confidence/diversity metadata.
- **Analyst-visible UI signal:** `weak_cluster_evidence` warning and validation event.
- **Fallback behavior:** Favor article-level and citation-level review over cluster conclusions.
- **Stop condition:** None by default unless combined with other STOP gates.

### FM-010 Missing or weak citation support
- **Description:** Claims without source traceability reduce trust.
- **How it appears here:** Citation count below canonical article count or high inferred/speculative share.
- **Detection rule:**
  - STOP if `citation_count < canonical_articles`.
  - WARN if inferred+speculative citation share `>= 0.40`.
- **Prevention rule:** Citation index generated for every canonical article with claim classification.
- **Analyst-visible UI signal:** Validation gate events + citation panel counts.
- **Fallback behavior:** Block publication when citation coverage is incomplete.
- **Stop condition:** Incomplete citation coverage.

### FM-011 Silent UI degradation when artifacts are missing
- **Description:** UI falls back to partial defaults without explicit critical signal.
- **How it appears here:** Missing required artifact keys can cause degraded panels.
- **Detection rule:** STOP when required artifacts are absent.
- **Prevention rule:** Enforce artifact contract keys and validation checks per run.
- **Analyst-visible UI signal:** Critical validation failure naming missing artifact keys.
- **Fallback behavior:** Keep run inspectable but prevent trust escalation/publication.
- **Stop condition:** Any required artifact missing.

## Required analyst-visible outputs
For every WARN/STOP event, show in UI:
1. rule ID,
2. measured values,
3. threshold,
4. remediation/fallback,
5. stop status.

## Notes
This repository intentionally keeps controls lightweight and in-repo. No external orchestration dependency is required for trust gating.

### FM-013 Required GDELT source failure
- **Description:** GDELT is mandatory and cannot be treated as optional coverage.
- **Detection rule:** STOP when GDELT source status is not `success`.
- **Analyst-visible signal:** Validation failure includes GDELT status + error details.
- **Fallback behavior:** Keep run inspectable, block publish.

### FM-014 Unknown-date peak
- **Description:** Timeline peak on `unknown` can mislead temporal conclusions.
- **Detection rule:** STOP when peak candidates resolve to `unknown` (i.e., no known-day bucket can establish the peak).
- **Analyst-visible signal:** Validation failure includes `peak_days` and `peak_count`.
- **Fallback behavior:** Require date parsing correction before publication.

### Phase A source telemetry hardening
- Per-source runtime telemetry must provide `attempted/succeeded/failed/skipped/article_count/fallback_used`.
- `skipped` is distinct from `failed`; token-gated sources (for example X/Twitter) should not be counted as transport failures when credentials are absent.
- GDELT telemetry includes explicit result mode: `failed`, `empty`, `partial`, or `full`.

### FM-015 Missing event-location geospatial output
- **Description:** Map cannot be trusted when only source/publisher locations exist.
- **Detection rule:** STOP for non-trivial runs when `event_location` extraction is empty.
- **Analyst-visible signal:** Validation failure naming event-location coverage gap.
- **Fallback behavior:** Continue inspection but block publish claims tied to geography.
