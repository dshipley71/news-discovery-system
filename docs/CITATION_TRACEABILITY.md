# Citation Traceability Specification

## 1) Purpose
Define the canonical citation model and deterministic linkage rules so every analytical claim, cluster insight, map/location insight, and timeline peak can be traced to real retrieved articles.

## 2) Scope
This specification governs:
- citation records created from normalized article data,
- claim-to-evidence linkage,
- cluster/peak/location evidence bundle linkage,
- publication gates for citation completeness.

No simulated citations are permitted. Every citation record must originate from a retrieved and normalized article artifact.

## 3) Canonical Citation Schema
Each citation record MUST include:
- `citation_id` (stable ID)
- `article_id` (foreign key to canonical article)
- `source` (publisher/source name)
- `url` (canonical or resolved source URL)
- `publication_date` (ISO-8601 date/time from source metadata)
- `claim_linkage[]` (list of claim IDs this article supports/challenges)

Recommended metadata fields:
- `retrieved_at`
- `source_record_id` (provider-native ID when available)
- `excerpt_ref` (text span pointer or content hash)
- `stance` (`supports` | `contradicts` | `context`)
- `confidence_contribution`

## 4) Claim Linkage Rules
1. `claim_linkage[]` cannot be empty for citations included in publishable outputs.
2. Every `claim_id` in `claim_linkage[]` must resolve to a claim node in the current run.
3. Claim-level statements in reports must reference one or more citation IDs.
4. Contradiction claims require at least two independent citations from distinct sources.
5. Removing a citation from a claim requires re-validation of claim confidence and publication gate status.

## 5) Traceability Paths (Required)
The system must support these drill paths end-to-end:
- `claim -> citation_id -> article_id -> raw retrieval metadata`
- `cluster_id -> article_ids[] -> citation_ids[]`
- `peak_id -> cluster_ids[] -> article_ids[] -> citation_ids[]`
- `location_group_id -> cluster_ids[] -> article_ids[] -> citation_ids[]`

If any path segment is broken, mark the dependent insight as non-publishable.

## 6) Citation Completeness Gates
- **Pass:** 100% of publishable claims resolve to >=1 valid citation.
- **Warn:** internal exploratory views may show partial linkage, but must be visibly labeled non-publishable.
- **Fail:** any publish attempt with orphan claims (claim without citation) is blocked.

## 7) Assumptions
- Canonical article IDs are immutable within a run.
- Source metadata includes either a direct URL or a resolvable locator.
- Claim nodes are versioned and auditable.

## 8) Open Decisions
1. Exact storage strategy for `excerpt_ref` (inline snippet vs external object store pointer).
2. Whether citation style formatting (APA/Chicago/etc.) is generated at export time or persisted as artifact fields.
