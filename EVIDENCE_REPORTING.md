# EVIDENCE_REPORTING.md

## Evidence Levels

### Level 1 — Reference
Store:
- URL
- title
- source
- date
- short excerpt

### Level 2 — Snapshot
Store:
- structured summary
- key claims
- entities
- sentiment
- cluster ID

### Level 3 — Full Content
Store selectively:
- full article text or extended excerpt
- metadata
- justification

## Evidence Rules
- deduplicate before escalation
- only cluster-relevant items move beyond Level 1
- only top-value items should reach Level 3
- full-content retention must be justified

## Required Artifacts
- run_brief.md
- source_ledger.md
- article_registry.md
- deduplication_log.md
- cluster_registry.md
- temporal_dataset.md
- geospatial_dataset.md
- sentiment_analysis_memo.md
- narrative_comparison_memo.md
- citation_index.md
- final_report.md

## Reporting Requirements
The final report should include:
- topic
- date window
- source summary
- timeline interpretation
- peak analysis
- trend analysis
- geospatial insights
- sentiment analysis
- narrative comparison
- limitations
- citation appendix

## Citation Rules
All major claims must map:
claim → cluster → article(s) → source(s)

Labels:
- supported
- inferred
- speculative

## Limitations
Always disclose:
- sparse coverage
- source dominance
- syndication inflation
- uncertainty
- unresolved conflicts
