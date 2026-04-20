# AGENTS.md

## Purpose
This repository defines and incrementally builds a real, production-capable, no-code, UI-first news intelligence application for analysts.

## Non-negotiable rules
- This is a real application, not a simulated demo.
- Prefer no-code or low-code orchestration.
- Minimize handwritten code wherever possible.
- The entire analyst workflow must be executable from the front end.
- Do not require command-line usage for the analyst experience.
- Preserve traceability, citations, validation, and auditability.
- Favor small, reviewable changes over broad refactors.
- Do not introduce unnecessary frameworks or implementation detail in planning documents.
- Do not invent fake integrations, fake outputs, or fake test results.
- Keep all planning documents operational and specific.

## Working style
- Start with documentation and operating manuals before implementation.
- For larger tasks, produce a short plan first.
- Reuse repository guidance rather than repeating instructions.
- Prefer explicit assumptions over hidden assumptions.
- Distinguish confirmed requirements from inferred design choices.

## Project priorities
1. Analyst-first UI
2. Real workflow execution
3. Step-by-step testability
4. Evidence traceability
5. Minimal-code architecture
6. Clean handoffs between workflow stages

## First-phase deliverables
- AGENTS.md
- docs/PRODUCT_REQUIREMENTS.md
- docs/UI_SPEC.md
- docs/WORKFLOWS.md
- docs/TEST_PLAN.md
- docs/ARTIFACTS.md
- docs/ROUTING_RULES.md
- docs/EVALUATION.md

## Design principles
- UI-first
- no-code-first
- multi-source
- evidence-backed
- geospatially aware
- temporally analytical
- suitable for non-technical analysts

## Constraints for implementation planning
- Some news sources may require API keys; others may not.
- The architecture must tolerate mixed source types.
- The analyst should only need to provide topic and date range, with optional advanced settings.
- Outputs must include timeline plots, maps, tables, citations, and a final report.
- Every major stage must be inspectable and testable from the UI.

## Operating mode for this repository
- Treat documentation as the source of truth for system behavior until automation is implemented.
- Prefer no-code orchestration platforms (workflow builders, connectors, schedulers, data prep tools) before introducing custom services.
- Any unavoidable code must be small, isolated, and documented with clear reason for existence.
- Every workflow stage must produce inspectable artifacts with IDs, timestamps, and provenance.
- Every decision that affects analyst outputs must be reviewable in the UI.

## Review Logging and Analyst Output Requirements
- Every user-triggered query MUST produce a structured review artifact.
- Every review artifact MUST include:
  - query metadata
  - source-level retrieval summary
  - date integrity summary
  - timeline summary
  - cluster summary
  - geospatial summary
  - validation and warning outputs
  - analyst-facing summary
- Every review artifact MUST exist in two formats:
  - structured JSON (machine-readable)
  - markdown summary (human-readable, copyable)
- Every review artifact MUST be derived only from backend workflow outputs:
  - no UI-generated or inferred values
  - no simulated or placeholder data

## Timeline and Event Signal Rules
- The default timeline MUST NOT be raw article count.
- The system MUST distinguish event signal from coverage volume.
- The system SHOULD prefer cluster-based signal and canonical/deduplicated counts.
- The system MUST flag temporal anomalies and late spikes inconsistent with event lifecycle.

## Source Transparency Requirements
- All sources MUST report:
  - status (`succeeded`, `failed`, `skipped`, `empty`, `partial`)
  - article count
  - fallback usage, if applicable
  - error details, if available
- Sources MUST be classified as one of:
  - aggregator
  - primary publisher
  - event database
  - social
  - specialist
  - public discussion
- Missing credentials MUST produce an explicit `skipped` state and MUST NOT fail silently.

## Deterministic and Testable Outputs
- All review artifacts MUST be deterministic for a given input.
- No randomness or non-reproducible logic is allowed in timeline generation, clustering, or source summaries.
- All major outputs MUST have test coverage for:
  - review log artifact generation
  - timeline summary generation
  - source status reporting
  - validation gates

## Geospatial and Future Enrichment
- Location types MUST be explicit:
  - `event_location`
  - `source_location`
  - `mentioned_location`
- Default map behavior MUST use `event_location`.
- The system MUST support future enrichment hooks:
  - `geocode_status`
  - `extraction_method`
  - `enrichment_needed`
- External enrichment (including LLMs) MUST be optional, auditable, and MUST NOT replace deterministic logic.

## Analyst-Focused Design Principles
- The system MUST prioritize:
  - correctness over volume
  - transparency over abstraction
  - traceability over convenience
- Outputs MUST allow analysts to answer:
  - what happened
  - when it happened
  - where it happened
  - which sources support it
  - how reliable the signal is
- The system MUST NOT:
  - hide uncertainty
  - merge unrelated events silently
  - inflate signal due to duplicates or source bias

## Change rules
- Do not rewrite the whole repository when only a few files need to change.
- Keep structure clear and durable.
- Prefer markdown operating manuals before automation details.
- Record assumptions and unresolved questions explicitly.
