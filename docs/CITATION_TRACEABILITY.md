# Citation Traceability Specification (Current Dashboard)

## 1) Purpose
Define how the Gradio analyst dashboard exposes citation/evidence linkage from real workflow outputs.

## 2) Source of Truth
Citation records in current UI are derived from `normalization.canonical_articles[]` within a single run payload.

No simulated citation entries are allowed.

## 3) Citation Record Fields (Current UI)
Each citation row includes:
- `citation_id`
- `article_id`
- `cluster_id`
- `source`
- `publication_date`
- `url` (nullable when unavailable)
- `claim_classification` (`supported|inferred|speculative`)
- `duplicate_flag`

Classification behavior:
- use upstream `claim_classification` when present,
- else derive deterministically from available metadata so analysts can distinguish evidence confidence levels.

## 4) Evidence Bundle Linkage
The UI emits evidence bundle rows for analyst drill-down:
- `bundle_id`
- `bundle_type` (`cluster_support` in current implementation)
- `bundle_subject_id` (cluster ID)
- `article_id`
- `citation_id`
- `source`

This provides explicit UI-level lineage for cluster-level inspection.

## 5) Required Analyst Drill Paths (Current)
Supported paths:
1. `cluster_id -> cluster article membership -> article_id`
2. `cluster_id -> citation rows -> citation_id -> article_id`
3. `citation index counts -> citation row verification`

When data is unavailable, UI must show explicit empty/no-data state rather than hidden failure.

## 6) Publication Readiness Signal (UI)
The run summary warning area should flag:
- missing citation output,
- speculative citation counts,
- duplicate-heavy clusters that can weaken claim confidence.

These warnings are advisory for analyst review and do not yet implement a hard publish gate.

## 7) Next Improvement
Promote `claim_linkage[]` to a first-class workflow artifact so dashboard citations can resolve from claim statement -> citation -> article deterministically without UI-only derivation.
