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

## Change rules
- Do not rewrite the whole repository when only a few files need to change.
- Keep structure clear and durable.
- Prefer markdown operating manuals before automation details.
- Record assumptions and unresolved questions explicitly.
