# Implementation Plan: No-Code, UI-First News Intelligence System

## 1) Scope and Intent
This document converts the approved design package into a practical implementation plan for a real application. It defines build sequence, execution boundaries (no-code vs minimal-code), UI-driven validation, and operational readiness checkpoints without implementing full application code.

## 2) Repository Review Summary (Completed Before Planning)
Reviewed source-of-truth design docs:
- `docs/PRODUCT_REQUIREMENTS.md`
- `docs/UI_SPEC.md`
- `docs/WORKFLOWS.md`
- `docs/TEST_PLAN.md`
- `docs/ARTIFACTS.md`
- `docs/ROUTING_RULES.md`
- `docs/EVALUATION.md`

### Confirmed requirements carried into this plan
- End-to-end analyst workflow must run from UI only.
- No-code orchestration is default; custom code is last resort.
- Every stage must expose inputs, outputs, validations, lineage, and status.
- Partial source failure must degrade gracefully, not silently fail.
- Final report publication requires citation completeness.

### Identified gaps/ambiguities to resolve during execution
1. No-code platform and UI stack are not yet selected.
2. Source portfolio (licensed APIs + public feeds) is undefined.
3. Threshold defaults (dedupe, clustering cohesion, trend sensitivity, citation gate) are not finalized.
4. Strict vs permissive publication policy default is undecided.
5. Storage pattern for immutable artifacts and larger evidence bundles is undecided.

## 3) Guiding Implementation Principles
1. UI-first delivery order: expose analyst controls and stage visibility early.
2. No-code-first execution: implement orchestration and connectors before writing code.
3. Stage-contract enforcement: each phase maps to stage I/O contracts already defined.
4. Incremental production hardening: each phase must be executable and testable in the UI before moving forward.
5. Traceability by default: all outputs must remain evidence-linked and auditable.

## 4) Buildable Phases (Execution Plan)

## Phase 1: UI Shell + Workflow Trigger
**Goal:** Launch runs from UI and show orchestration lifecycle.

**Inputs**
- Topic
- Date window (1-30 days ending at current date)
- Optional advanced settings profile

**Outputs**
- Run Manifest artifact
- Run status timeline (queued/running/completed/partial/failed)
- Stage list scaffold with empty placeholders

**No-code implementation**
- Build run intake form, validation rules, and submit action.
- Configure orchestrator trigger (webhook/API call) for run creation.
- Store run metadata in managed data store.

**Minimal-code (if unavoidable)**
- Thin schema validator service only if no-code form validation cannot enforce date-window and required fields consistently.

**UI components**
- Run Builder
- Run Monitor (status-only baseline)
- Basic Stage Detail shell

**Validation steps (UI executable)**
1. Empty topic blocks submission.
2. Invalid date-window blocks submission.
3. Valid request creates run with immutable run ID.
4. Status transitions visible in Run Monitor.

**Exit criteria**
- Analyst can start a real run and observe lifecycle without CLI.

---

## Phase 2: Multi-Source Ingestion
**Goal:** Retrieve current items from mixed source types with failover.

**Inputs**
- Run Manifest
- Source catalog
- Credential availability state

**Outputs**
- Source Plan artifact
- Raw Retrieval Bundle artifact
- Source-level success/failure logs

**No-code implementation**
- Configure source connectors (API-key + non-key).
- Add routing with retries/backoff and fallback ordering.
- Capture request/response metadata and error details.

**Minimal-code (if unavoidable)**
- Adapter for any required source lacking stable connector.
- Lightweight parser for non-standard payload shape.

**UI components**
- Source ingestion summary widget
- Retrieval log table (source, status, errors)
- Stage Detail for Source Discovery and Retrieval

**Validation steps (UI executable)**
1. Mixed source classes appear in source plan.
2. One-source outage produces partial-success, not run termination.
3. All-source outage terminates with remediation guidance.

**Exit criteria**
- At least one source class can fail while run remains observable and policy-compliant.

---

## Phase 3: Normalization + Deduplication
**Goal:** Produce canonical records and duplicate lineage map.

**Inputs**
- Raw Retrieval Bundle

**Outputs**
- Canonical Article Set
- Deduplication Map
- Data quality metrics (schema completeness, duplicate ratio)

**No-code implementation**
- Mapping/transformation nodes for canonical schema.
- Rules for URL/content/meta similarity dedupe.
- Branching for schema-failure thresholds.

**Minimal-code (if unavoidable)**
- Custom near-duplicate scoring function if platform dedupe quality is insufficient.

**UI components**
- Normalization quality card
- Dedupe log panel showing canonical record + merged IDs + rationale

**Validation steps (UI executable)**
1. Missing required fields are flagged, not hidden.
2. Known duplicate examples collapse correctly with lineage preserved.
3. Distinct records remain separate.

**Exit criteria**
- Analysts can inspect dedupe decisions and trace merged items.

---

## Phase 4: Clustering + Temporal Analysis
**Goal:** Turn deduped records into event groups and timeline insights.

**Inputs**
- Canonical deduped records
- Publish timestamps

**Outputs**
- Event Group Set
- Timeline Metrics Set
- Peak/spike/trend annotations with thresholds logged

**No-code implementation**
- Configure event grouping primitives and threshold profiles.
- Configure time-bucket aggregation and rule-based trend labeling.
- Persist confidence and rationale per event/insight.

**Minimal-code (if unavoidable)**
- Specialized clustering primitive for domain-specific cohesion scoring.

**UI components**
- Events Table
- Timeline tab with markers
- Stage Detail for clustering and temporal analytics

**Validation steps (UI executable)**
1. Each article is assigned or explicitly unassigned.
2. Cluster cohesion metric displayed and validated.
3. Timeline markers include linked evidence IDs.

**Exit criteria**
- Analyst can verify why an event exists and why a trend marker appears.

---

## Phase 5: Geospatial Visualization
**Goal:** Extract/resolve locations and present map-first evidence exploration.

**Inputs**
- Clustered articles
- Location entities and confidence

**Outputs**
- Geospatial Entity Set
- Resolved/ambiguous location annotations
- Map-ready layer dataset

**No-code implementation**
- Entity extraction and geocoding connectors/workflow nodes.
- Resolution fallback chain (provider A -> provider B -> unresolved).
- Confidence and ambiguity flags persisted.

**Minimal-code (if unavoidable)**
- Small disambiguation helper for ambiguous place names not resolved by available connectors.

**UI components**
- Map tab with filters (event/source/date/confidence)
- Drill-down card with claim/citation links

**Validation steps (UI executable)**
1. Explicit place mentions map successfully with citation links.
2. Ambiguous entities are visibly flagged.
3. Provider failure degrades gracefully with advisory.

**Exit criteria**
- Analysts can interpret map outputs and uncertainty clearly.

---

## Phase 6: Report Generation + Evidence Packaging
**Goal:** Publish evidence-backed report outputs and export bundles.

**Inputs**
- Event, timeline, map, narrative outputs
- Citation Graph

**Outputs**
- Report Package (UI view + export variants)
- Citation appendix
- Evidence bundle index

**No-code implementation**
- Templated report composition workflow.
- Export tasks for PDF/HTML/JSON.
- Citation completeness gate prior to publish.

**Minimal-code (if unavoidable)**
- Evidence graph serialization utility for large bundles.

**UI components**
- Report Viewer and Export panel
- Citation explorer panel

**Validation steps (UI executable)**
1. Every report claim has at least one citation.
2. Missing citation blocks publish.
3. Exports include required sections and lineage manifest.

**Exit criteria**
- Analysts can publish/export reports with verifiable evidence traceability.

---

## Phase 7: Validation + Critic Loop Operationalization
**Goal:** Make quality evaluation and refinement loop visible and repeatable in UI.

**Inputs**
- Report draft
- Validation failures/warnings
- Critique policy (max iterations, strict/permissive)

**Outputs**
- Critic Log with iteration deltas
- Refined report versions
- Final gate decision with blockers if unresolved

**No-code implementation**
- UI Test Console wiring to stage and end-to-end test profiles.
- Policy-driven critic routing and bounded reruns.
- KPI telemetry capture and dashboard surfaces.

**Minimal-code (if unavoidable)**
- None expected initially; only if no-code platform cannot represent critic delta tracking.

**UI components**
- Test Console
- Critic iteration diff panel
- Final quality gate status panel

**Validation steps (UI executable)**
1. Failed quality gate triggers critic iteration.
2. Iteration count and changes are inspectable.
3. Max-iteration behavior follows strict/permissive policy.

**Exit criteria**
- Quality assurance is reproducible, observable, and non-technical-user operable.

## 5) No-Code vs Minimal-Code Boundary Policy

## No-code must handle by default
- Workflow orchestration, branching, retries, and scheduling.
- Source connectors where available.
- Field mapping/transformation for canonical schema.
- Stage status, validation display, and artifact metadata storage.
- UI actions for run start/rerun, stage inspection, and exports.

## Minimal-code allowed only when blocked
Allowed categories (must include written rationale and owner):
1. Missing connector adapter.
2. Dedupe/clustering primitive unavailable in no-code toolset.
3. Evidence bundle serialization utility for scale/performance.
4. Provider-specific geospatial disambiguation helper.

## Guardrails
- Each custom module must remain isolated, documented, and replaceable.
- No custom module may bypass artifact IDs, timestamps, or citation linkage.
- Prefer managed platform features even if less elegant, unless they fail quality gates.

## 6) Cross-Phase Milestones and Readiness Gates
- **M1 (after Phase 2):** Real ingestion with partial-failure handling visible in UI.
- **M2 (after Phase 4):** Event + timeline insights inspectable with evidence links.
- **M3 (after Phase 6):** Publishable report with citation gate and export.
- **M4 (after Phase 7):** UI-driven validation and critic loop operational.

## 7) Assumptions
1. Team has access to one enterprise no-code orchestrator and one UI platform.
2. At least two heterogeneous news source classes are contractually accessible.
3. Data store can preserve immutable run/stage artifacts and lineage metadata.
4. Admin role can manage credential vault and policy thresholds.

## 8) Unresolved Decisions
1. Final orchestrator vendor and deployment topology.
2. Initial source portfolio and legal/policy limits per source.
3. Threshold defaults for dedupe/clustering/trend detection and citation gating.
4. Strict vs permissive publish mode default.
5. Retention schedule and archive format for large evidence bundles.

## 9) Key Risks and Blockers
- **Source licensing delay:** blocks representative ingestion testing.
- **Connector mismatch:** may force more custom adapters than desired.
- **Ambiguous geo resolution quality:** risks analyst trust if uncertainty UX is weak.
- **Citation gate strictness misconfiguration:** may block useful reports or allow weak ones.
- **Artifact store scalability:** can become bottleneck for full evidence retention.
