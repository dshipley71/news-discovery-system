# Failure Modes for Gradio Analyst Workflow

## 1) Purpose
This document defines Gradio-specific and workflow-specific failure modes that can mislead analysts, plus required behavior to prevent silent failures.

## 2) Reliability Principles
- No stage may fail silently.
- Every warning/failure must be visible in the Gradio UI with reason, metric, threshold, and next action.
- Every publishable insight must remain traceable to source evidence and citations.

## 3) Failure Mode Matrix (Required)

| Failure mode | Description | Detection method | Prevention rule | UI validation signal | Fallback behavior |
|---|---|---|---|---|---|
| Duplicate article inflation | Same story appears multiple times (wire syndication, retries, URL variants) and inflates counts/trends/clusters. | Duplicate ratio; URL canonicalization collisions; near-duplicate text hash families; same-source/time burst checks. | Deduplicate before clustering/timeline; enforce unique `article_id` counts for map/timeline/cluster evidence. | Stage badge: `WARN_DUPLICATES`/`FAIL_DUPLICATES`; show duplicate ratio, affected clusters, and affected timeline bins. | Mark run as partial-confidence, suppress publish-grade spike claims, keep duplicate lineage table for analyst review. |
| Empty ingestion | Retrieval completes but returns zero usable articles. | `retrieved_count == 0` and source attempts > 0; all payloads empty/filtered. | Block downstream stages when no valid articles remain after normalization. | Blocking banner: `No articles ingested`; show source attempts, date window, query terms. | Offer guided rerun: broaden date range, broaden source profile, or adjust topic terms. |
| Schema drift | Source payload fields/types change and canonical mapper no longer matches reliably. | Required-field completeness drop; type mismatch count; unexpected new/missing keys. | Enforce canonical schema contract and quarantine non-conforming records. | `SCHEMA_DRIFT` warning/fail card with field-level error counts and examples. | Continue only if completeness stays above warning threshold; otherwise stop and request connector mapping update. |
| Incorrect date parsing | Bad/ambiguous dates produce wrong timeline placement or out-of-range events. | Parse failure rate; out-of-window timestamps; impossible future/past bucket anomalies. | Use strict parser policy (timezone-aware, explicit locale policy); reject invalid timeline dates. | `DATE_PARSE_ISSUE` card with invalid-date count and impacted records link. | Exclude invalid timestamps from analytics, keep invalid-date audit bucket, block publish if coverage below threshold. |
| Broken UI state | Gradio state desync causes stale run IDs, stuck stages, or controls showing wrong status. | Missing/changed run ID between callbacks; stage heartbeat timeout; UI state != backend state checksum. | Require authoritative backend run state; never finalize UI from local state only. | Status rail shows `STATE_DESYNC` and disables publish/export actions. | Auto-refresh from backend snapshot; allow analyst to rebind to latest valid run; fail safely if unresolved. |
| Incorrect geospatial inference | Wrong place resolved (e.g., Paris, TX vs Paris, FR), fabricated coordinates, or unsupported inference presented as fact. | Low-confidence resolver output; ambiguity flags; country/region conflict checks; geo-evidence mismatch rate. | Require evidence span + confidence + method (`explicit`/`inferred`) for each location claim. | Map marker warning icon and `LOW_GEO_CONFIDENCE` panel with ambiguous locations list. | Suppress high-confidence geo claims; keep uncertain locations as inspectable artifacts only. |
| Weak clustering | Clusters formed from sparse/noisy overlap and presented as robust events. | Low cohesion/separation metrics; low unique-article count; high top-source concentration. | Enforce minimum evidence and cluster confidence thresholds; flag exploratory-only clusters. | Cluster table column flags: `weak_cluster`, `top_source_ratio`, `duplicate_ratio`. | Keep weak clusters visible for exploration but block publish-grade conclusions from them. |
| Missing citations | Claims cannot be traced to source articles/URLs/publication metadata. | Claim-to-citation coverage check; orphan claim count; citation schema validation. | 100% citation linkage required for publish mode. | `CITATION_GAP` blocking banner; claim list with unresolved citation links. | Enter review-only mode; disable export/publish until citation gaps are resolved. |
| Misleading timeline spikes | Spikes driven by syndication bursts/backfills/timezone bucketing instead of real event intensity. | Spike source-concentration check; duplicate-family contribution check; backfill ingestion timestamp mismatch. | Require corroboration from diverse sources and publish-time buckets in canonical timezone. | Timeline spike tooltip includes confidence, source diversity, duplicate share, and anomaly flag. | Re-label as low-confidence anomaly; prevent strong narrative claims unless corroborated. |

## 4) System Stop vs Warn Policy
- **Stop (hard fail):** empty ingestion, broken run-state integrity, missing citations in publish mode, severe schema/date failure below threshold.
- **Warn (continue with limits):** partial source loss, moderate duplicate risk, low geospatial confidence, weak clusters, anomaly-classified spikes.

## 5) What Analysts Must See at Each Stage
At each stage, the UI must show:
1. Inputs used (topic, date range, source profile, run ID).
2. Validation checks run (pass/warn/fail).
3. Metrics vs thresholds.
4. Impacted artifacts (cluster IDs, location IDs, timeline bins, citation IDs).
5. Next recommended action.

## 6) How Analysts Detect Bad Data
Analysts detect bad data via visible counters and drill-down links:
- duplicate ratio and duplicate family table,
- invalid-date and out-of-window counts,
- source success/failure matrix,
- map ambiguity/low-confidence markers,
- weak-cluster/source-concentration columns,
- claim-to-citation coverage gauge.

## 7) No-Silent-Failure Requirement
If a stage errors, times out, or yields a degraded state, UI must immediately surface:
- failure code,
- plain-language impact,
- blocked downstream actions,
- remediation path (rerun, widen scope, update mapping, escalate).

## 8) Remaining Open Items
1. Final numeric thresholds by environment.
2. Strict-mode policy for partial runs.
3. Alert routing (in-app only vs in-app + external notifications).
