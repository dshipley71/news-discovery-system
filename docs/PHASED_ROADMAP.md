# Phased Roadmap

## 1) Roadmap Intent
This roadmap translates design requirements into execution waves with explicit deliverables, analyst-visible outcomes, and go/no-go gates.

## 2) Phase Schedule (Sequence, Not Calendar)

| Phase | Name | Primary Deliverable | Analyst-visible outcome | Gate to next phase |
|---|---|---|---|---|
| 1 | UI Shell + Trigger | Run Builder + Run Monitor baseline | Analyst can start and track runs | Valid run created and tracked fully in UI |
| 2 | Multi-Source Ingestion | Source discovery/retrieval with fallback | Analyst sees per-source retrieval success/failure | Partial-failure handling proven |
| 3 | Normalize + Deduplicate | Canonical article set + lineage map | Analyst inspects dedupe reasons and quality metrics | Canonical schema and lineage quality pass |
| 4 | Cluster + Temporal | Event groups + timeline insights | Analyst validates event grouping and trend markers | Cohesion and timeline checks pass |
| 5 | Geospatial | Map-ready location artifacts | Analyst can drill from map marker to evidence | Ambiguity handling and map confidence verified |
| 6 | Reporting | Report package + exports + citation appendix | Analyst can review and export evidence-backed report | Citation completeness gate enforced |
| 7 | Validation + Critic | UI test console + bounded refinement loop | Analyst can execute validation profiles and review revisions | KPI baseline and critic policy pass |

## 3) Phase Details

## Phase 1 — UI Shell + Trigger
### Build focus
- Implement intake UX and validation constraints.
- Wire run creation to orchestrator trigger.
- Show real-time stage status scaffold.

### No-code first
- Form validation, run record persistence, webhook trigger.

### Minimal-code fallback
- Intake validation microservice if no-code rules are insufficient.

### Analyst acceptance checks
- Can launch run with topic/date only.
- Receives immediate run ID and status updates.

---

## Phase 2 — Multi-Source Ingestion
### Build focus
- Configure source catalog and runtime source planning.
- Implement retries/backoff/fallback chain.
- Persist retrieval metadata and errors.

### No-code first
- Connector orchestration and routing policy execution.

### Minimal-code fallback
- Adapter for unsupported sources.

### Analyst acceptance checks
- Source-level table shows attempted/succeeded/failed sources.
- Partial failure still yields downstream continuation warning.

---

## Phase 3 — Normalize + Deduplicate
### Build focus
- Canonical schema mapping.
- Duplicate collapse with rationale and lineage.

### No-code first
- Transform nodes and rules-based dedupe flow.

### Minimal-code fallback
- Similarity function module if needed for near-duplicate precision.

### Analyst acceptance checks
- Deduplication log is human-inspectable.
- Canonical records preserve provenance.

---

## Phase 4 — Cluster + Temporal
### Build focus
- Event grouping with confidence scoring.
- Timeline aggregation and trend detection rules.

### No-code first
- Built-in grouping/aggregation and threshold policies.

### Minimal-code fallback
- Specialized clustering routine if platform output is inadequate.

### Analyst acceptance checks
- Events table and timeline both link back to evidence.
- Peaks/spikes/trends include rationale metadata.

---

## Phase 5 — Geospatial
### Build focus
- Place extraction and coordinate/region resolution.
- Ambiguity and uncertainty surfacing.

### No-code first
- Geocoding connectors and fallback route logic.

### Minimal-code fallback
- Disambiguation helper for unresolved high-frequency place names.

### Analyst acceptance checks
- Map marker click reveals claim + source + citation.
- Ambiguous entities are visibly labeled.

---

## Phase 6 — Reporting
### Build focus
- Report composition templates.
- Citation graph integration and export generation.

### No-code first
- Template assembly, section checks, export flows.

### Minimal-code fallback
- Evidence serialization helper for large bundles.

### Analyst acceptance checks
- Publish blocked if citation completeness fails.
- Export package includes report + citation appendix + lineage manifest.

---

## Phase 7 — Validation + Critic
### Build focus
- Stage and E2E test profile execution in UI.
- Critic loop with bounded iterations and visible deltas.
- KPI dashboard for readiness scoring.

### No-code first
- Test catalog orchestration, policy routing, KPI aggregations.

### Minimal-code fallback
- Optional delta-comparison helper only if native diffing is unavailable.

### Analyst acceptance checks
- Non-technical user can run test profiles and interpret pass/fail.
- Critic revisions are versioned and auditable.

## 4) Dependencies Across Phases
- Phase 2 depends on Phase 1 run creation and status framework.
- Phase 3 depends on stable retrieval metadata from Phase 2.
- Phase 4/5 depend on canonical and deduped outputs from Phase 3.
- Phase 6 depends on citation-capable outputs from Phases 4/5.
- Phase 7 depends on all prior phases being UI-observable.

## 5) Readiness Checklist Per Phase
For each phase before advancing:
1. Stage is executable from UI.
2. Stage output is inspectable from UI.
3. Stage validation results are visible from UI.
4. Artifacts are persisted with IDs/timestamps/provenance.
5. Regression checks for completed phases still pass.

## 6) Assumptions
- Roadmap is executed by small iterative releases.
- Each phase is reviewed with analyst sign-off before progression.

## 7) Unresolved Roadmap Decisions
1. Whether to run Phase 4 and 5 in strict sequence or parallel development tracks.
2. Minimum KPI threshold required to proceed from pilot to production.
3. Ownership split between platform configuration and minimal-code modules.

## 8) Risks/Blockers
- Delayed source contracts can stall Phase 2 and downstream phases.
- Insufficient no-code connector support can increase custom workload.
- Weak early observability can hide stage failures and delay remediation.
