# Data Pipeline Specification

## 1) Purpose
Specify real execution data flow, artifact transitions, persistence expectations, and failure handling from intake through final report publication.

## 2) Pipeline Topology
- Orchestrator executes stage contracts defined in `docs/WORKFLOWS.md`.
- Each stage produces immutable output artifacts and validation results.
- Downstream stages consume prior artifact IDs (not transient in-memory-only payloads).
- Parallel branches allowed after clustering (temporal, geospatial, narrative) with synchronized evidence packaging.

## 3) Stage Data Flow and Artifact Transitions

| Stage | Input Artifacts | Output Artifacts | Required Metadata |
|---|---|---|---|
| 0 Intake | UI request payload | Run Manifest | run_id, stage_id, timestamps, operator |
| 1 Source Discovery | Run Manifest + source catalog + credential state | Source Plan | source class mix, fallback order, availability snapshot |
| 2 Retrieval | Source Plan | Raw Retrieval Bundle + retrieval logs | request metadata, response metadata, source errors |
| 3 Normalization | Raw Retrieval Bundle | Canonical Article Set | schema version, normalization flags |
| 4 Deduplication | Canonical Article Set | Deduplication Map + deduped canonical set | merge rationale, confidence, lineage links |
| 5 Event Clustering | Deduped set | Event Group Set | membership scores, cohesion metrics |
| 6 Temporal | Event Group Set + timestamps | Timeline Metrics Set | bucket config, threshold params, marker rationale |
| 7 Geospatial | Event Group Set / canonical text | Geospatial Entity Set | entity confidence, resolution status |
| 8 Narrative | Event Group Set + source metadata | Narrative Matrix | contradiction/support tags, evidence refs |
| 9 Evidence Packaging | Stages 5-8 outputs | Citation Graph + evidence index | claim IDs, citation completeness metrics |
| 10 Report | Citation Graph + summary artifacts | Report Package | section checks, publish status |
| 11 Critic | Report Package + validations | Critic Log + revised report versions | iteration number, delta summary, blockers |

## 4) Artifact State Model
Each artifact has lifecycle states:
1. **draft** (during stage execution)
2. **validated** (passes required checks)
3. **degraded** (usable with warnings)
4. **blocked** (failed critical checks)
5. **finalized** (immutable and consumable downstream)

Rules:
- Only `validated`, `degraded`, or `finalized` outputs may flow downstream.
- `blocked` artifacts stop dependent stages unless policy allows degraded bypass.
- Critic revisions create new version IDs; prior versions remain retrievable.

## 5) Persistence Expectations

## Mandatory persistence fields
- run_id
- stage_id
- artifact_id
- parent_artifact_ids
- created_at / finalized_at timestamps
- validation_status and check results
- confidence summary
- actor (system/agent/admin)

## Storage behavior
- Raw and derived artifacts are immutable post-finalization.
- Stage reruns append new artifact versions; no destructive overwrite.
- UI retrieves artifacts by ID for drill-down and audit.

## Retention baseline
- Raw retrieval bundles retained per policy for auditability.
- Derived artifacts retained for at least one full regression cycle plus audit period.
- Export packages retain referenceable lineage manifest.

## 6) Failure Handling Specification

## Intake failure
- Behavior: fail-fast with UI guidance; no downstream artifact creation.

## Source/retrieval partial failure
- Behavior: continue if minimum viable sources met.
- Output: degraded Source Health status propagated downstream.

## Critical schema failure (normalization)
- Behavior: block downstream and surface flagged record diagnostics.

## Dedupe/clustering quality warning
- Behavior: allow one bounded retry with adjusted threshold profile.

## Branch failure (temporal/geospatial/narrative)
- Behavior: continue with degraded branch markers and confidence downgrade.

## Citation completeness failure
- Behavior: block report publish until remediated.

## Critic loop exhaustion
- Behavior: finalize with unresolved blockers under permissive mode or block publish under strict mode.

## 7) Observability and UI Traceability Requirements
- Each stage emits execution metrics: start/end time, duration, retry count, error count.
- Each validation rule emits pass/warn/fail status with remediation hint.
- Every UI insight must include linked artifact IDs and evidence references.
- Audit timeline must show actor, action, timestamp, and affected artifact IDs.

## 8) No-Code vs Minimal-Code in Pipeline Execution

## No-code responsibilities
- Orchestration flow control, retries, conditionals, and stage transitions.
- Transform/mapping steps and artifact metadata writes.
- Validation rule execution and status propagation.

## Minimal-code (only if necessary)
- Unsupported transformation primitives at scale.
- Specialized scoring functions for dedupe/clustering not available natively.
- High-volume evidence serialization helper.

## 9) Assumptions
1. Data store supports immutable, versioned records and indexed retrieval by run/stage/artifact ID.
2. Orchestrator supports parallel branch execution and merge synchronization.
3. UI can request and render large artifact lists with pagination.

## 10) Unresolved Decisions
1. Final storage technology and partitioning strategy.
2. Exact degraded-mode propagation rules for downstream confidence impact.
3. Maximum artifact payload size per stage and chunking policy.

## 11) Risks/Blockers
- Artifact volume growth may affect stage latency and UI responsiveness.
- Incomplete metadata capture can break traceability guarantees.
- Weak merge logic at branch synchronization can produce inconsistent report inputs.
