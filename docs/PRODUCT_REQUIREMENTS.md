# Product Requirements: UI-First News Intelligence System

## 1) Objective
Deliver a production-capable, no-code-first news intelligence application that a non-technical analyst can operate entirely through the UI by entering only:
1. Topic
2. Date range (1-30 days, end date fixed to present day)

The system must automate sourcing, normalization, deduplication, event clustering, trend detection, geospatial analysis, narrative comparison, evidence packaging, and final report generation.

## 2) Users and Roles
### Primary user
- **Analyst (non-technical):** runs end-to-end workflow, inspects intermediate artifacts, validates outputs, and exports reports.

### Operational roles (post-implementation)
- **Admin:** manages source credentials, governance, retention, and quality thresholds.
- **Reviewer (optional):** validates high-impact outputs and audit trails.

## 3) Functional Requirements
### FR-1 Input capture (UI-only)
- Required fields:
  - Topic (text)
  - Date range length (integer 1-30), ending at now
- Optional advanced controls (collapsed by default):
  - Region focus
  - Language preference
  - Source mix/priority profile
  - Strictness profile (precision vs recall)

### FR-2 Source acquisition
- Must query multiple current-news source types:
  - API-key sources
  - Non-key sources (RSS/public feeds/web endpoints permitted by policy)
- Must support partial source failure while continuing run.
- Must log source-level request metadata and outcomes.

### FR-3 Data normalization and deduplication
- Normalize to canonical article schema.
- Deduplicate near-identical coverage across publishers and wire republishing.
- Preserve duplicate lineage (which records collapsed into canonical record).

### FR-4 Event grouping
- Cluster related coverage into event groups.
- Assign event IDs and article membership confidence.
- Expose group summaries with linked evidence.

### FR-5 Temporal analytics
- Generate article-count timeline at minimum daily granularity.
- Identify:
  - Peaks
  - Spikes (rapid change)
  - Sustained trends (multi-day elevated coverage)
- Provide confidence and rationale for each detection.

### FR-6 Geospatial analytics
- Extract place references with confidence and source evidence.
- Resolve ambiguous locations where feasible.
- Provide map visualization with layer toggles and drill-down to evidence.

### FR-7 Narrative comparison
- Compare framing across sources and event groups.
- Surface agreements, contradictions, and unique claims.
- Tag claims with supporting citations.

### FR-8 Evidence and citations
- Every generated statement in summaries and report must map to evidence bundle IDs.
- Citations must include source, URL (if available), publish timestamp, retrieval timestamp, and snippet/hash reference.

### FR-9 Final report
- Produce analyst-ready report in UI with export options (e.g., PDF/HTML/JSON package).
- Report sections: executive summary, key events, timeline findings, geospatial findings, narrative comparison, uncertainty notes, citation appendix.

### FR-10 Stage-by-stage testability
- UI must support explicit execution and inspection of each stage.
- Analyst can rerun individual stage(s) with bounded reprocessing rules.

## 4) Non-Functional Requirements
### NFR-1 Traceability and audit
- Immutable run ID and stage IDs.
- Complete lineage from final claim to raw source item.

### NFR-2 Reliability
- Graceful degradation with source outages.
- Explicit run status model (queued/running/partial-success/failed/completed).

### NFR-3 Performance targets (initial)
- 30-day run should complete within operationally acceptable SLA defined by deployment profile.
- Each stage must expose elapsed time and bottlenecks in UI.

### NFR-4 Security and compliance
- API keys never exposed to analysts.
- Role-based access for admin operations.
- Source usage policy checks and retention controls.

### NFR-5 Maintainability
- No-code orchestration-first implementation.
- Minimal custom code constrained to adapters unavailable in no-code connectors.

## 5) Architecture Options
### Option A: Multi-agent architecture (primary)
- Independent specialized agents coordinated by workflow orchestrator.
- Better modularity, inspection, and targeted reruns.

### Option B: Single-orchestrator pipeline (fallback)
- One orchestrator service executes all stages with internal modules.
- Lower operational overhead; reduced granularity and flexibility.

Detailed stage contracts are defined in `docs/WORKFLOWS.md`.

## 6) Quality and Validation Requirements
- Confidence scoring required at article, event, trend, geospatial, and report-claim levels.
- Source weighting profile applied during synthesis.
- Must handle:
  - Sparse coverage
  - Noisy coverage
  - Contradictory coverage
  - Breaking-news spikes
- Iterative critic loop required with max refinement count (default: 2, configurable by admin).

## 7) Out of Scope (this phase)
- Full automation code implementation.
- Production infrastructure provisioning scripts.
- Custom ML model training pipeline.

## 8) Assumptions
- Organization can provision at least two source categories (key + non-key).
- No-code platform supports scheduled and on-demand workflows with API/webhook connectors.
- UI framework can host interactive timeline and map components.

## 9) Open Decisions Before Implementation
1. No-code orchestration platform selection.
2. Initial source portfolio and licensing constraints.
3. Canonical confidence formula calibration.
4. Preferred geocoding/provider stack and fallback strategy.
5. Report export format priorities and retention policy.
