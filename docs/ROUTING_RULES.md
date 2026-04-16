# Routing Rules and Orchestration Policies

## 1) Purpose
Define deterministic routing for workflow execution, retries, fallbacks, and escalation across stages.

## 2) Global Routing Rules
- R-1: All runs begin with Intake validation.
- R-2: Invalid intake terminates run before source calls.
- R-3: Partial source failure does not terminate run unless minimum viable source threshold is unmet.
- R-4: Critical validation failure at any stage routes to either bounded retry or stop with reason.
- R-5: Final report publication is blocked if citation completeness check fails.

## 3) Retry and Fallback Policy
- Source call retries: bounded exponential backoff with max attempts set by admin.
- Stage retries: maximum 1 automatic retry per stage unless explicitly rerun by operator.
- Fallback order: use source plan priority with non-key fallback when key source unavailable.

## 4) Stage Routing Matrix
## Intake
- Pass -> Source Discovery
- Fail -> End (user correction required)

## Source Discovery
- >= minimum viable sources -> Retrieval
- < minimum viable sources -> End (insufficient sources)

## Retrieval
- Partial success -> Normalization (with warning)
- Total failure -> End (retrieval failed)

## Normalization
- Pass -> Deduplication
- Critical schema failure -> End or manual review route

## Deduplication
- Pass -> Event Clustering
- Quality warning -> Event Clustering with caution flag

## Event Clustering
- Pass -> Temporal + Geospatial (parallel permitted)
- Low cohesion -> one retry with adjusted thresholds

## Temporal/Geospatial/Narrative
- Complete -> Evidence Packaging
- One branch degraded -> continue with branch-specific low-confidence label

## Evidence Packaging
- Citation pass -> Report Composition
- Citation fail -> Critic Loop or stop (based on policy)

## Report Composition
- Pass -> Critic Loop
- Fail -> Critic Loop

## Critic Loop
- Critical issues resolved or max iterations reached -> Finalize with status

## 5) Critic Loop Policy
- Max refinement count: default 2.
- Critic can request targeted stage rerun only for impacted stages.
- If unresolved critical issue remains after max iterations:
  - Publish blocked for strict mode.
  - Conditional publish with blocker banner for permissive mode.

## 6) Handling Required Edge Conditions
## Sparse coverage
- Route to completion with low-confidence advisory.

## Noisy coverage
- Route through stricter dedupe/clustering profile, then continue.

## Contradictory coverage
- Route to narrative contradiction workflow; disable forced consensus summary.

## Breaking-news spike
- Route adds “developing story” advisory and suggests refresh run.

## 7) Human-in-the-Loop Routing (optional)
- Manual approval gates can be inserted after:
  - Retrieval
  - Evidence Packaging
  - Critic Loop
- Default first-phase recommendation: no manual gates, full automation with transparent logs.

## 8) Assumptions
- Orchestrator supports conditional branching, retries, and parallel branches.
- Admin can configure thresholds and policy mode (strict/permissive).

## 9) Open Decisions
1. Minimum viable source threshold values.
2. Strict vs permissive publish policy default.
3. Automatic refresh cadence for spike topics.
