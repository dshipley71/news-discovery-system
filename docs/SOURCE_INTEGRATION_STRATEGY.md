# Source Integration Strategy

## 1) Purpose
Define a real, no-code-first strategy for integrating mixed news sources (API and non-API), handling optional credentials, maintaining source diversity, and degrading safely when failures occur.

## 2) Source Categories and Handling

## A) API-key sources
Examples: licensed news APIs, premium aggregators, enterprise feeds.

**Strategy**
- Store keys in admin-managed secret vault.
- Orchestrator injects credentials at runtime only.
- Track per-source quotas, rate limits, and error classes.

**UI visibility**
- Analysts see source health/status and coverage metrics, not raw keys.

## B) Non-key sources
Examples: RSS feeds, public endpoints allowed by policy.

**Strategy**
- Configure policy-compliant connectors and fetch intervals.
- Normalize feed metadata to canonical source identity.
- Apply stricter provenance checks where source metadata quality varies.

**UI visibility**
- Analysts can inspect source origin, fetch timestamp, and reliability tier.

## C) Semi-structured or heterogeneous sources
Examples: provider-specific payloads with inconsistent field schemas.

**Strategy**
- Use no-code mapping templates for common shapes.
- Add lightweight adapter only when mapping cannot be handled by platform transformations.

## 3) No-Code First Implementation Pattern
1. Source catalog table (source_id, class, region, language, reliability tier, credential mode, active flag).
2. Discovery workflow node resolves run profile -> eligible source set.
3. Retrieval workflow runs sources in configurable parallel batches.
4. Retry/backoff policy applied per source.
5. Fallback ordering applies if primary sources fail.
6. Retrieval results and errors persisted per source attempt.

## 4) Optional API Key Handling
- Keys are optional per source; system must support mixed-key runs.
- Missing key for a key-required source should:
  1. mark source as unavailable,
  2. log actionable warning,
  3. continue with eligible alternatives.
- Admin UI must expose key status (configured/missing/expired) without revealing secret values.

## 5) Fallback and Failure Behavior

## Source-level failures
- Timeout, quota exceeded, auth failure, malformed response.
- Action: bounded retries -> fallback source -> partial-success warning.

## Stage-level failure rule
- If minimum viable source threshold is met: continue.
- If below threshold: fail run with remediation guidance.

## Degraded output handling
- Carry source coverage score into downstream confidence calculations.
- Mark timeline/map/narrative outputs with coverage caveats when source diversity is low.

## 6) Source Diversity Strategy

## Diversity dimensions
- Source ownership/publisher variety.
- Geographic variety.
- Political/editorial variety where relevant.
- Format variety (wire, local, specialty, international).

## Operational policy
- Require minimum number of independent source families for high-confidence claims.
- Prevent single-source dominance in claim confidence unless explicitly labeled low-confidence.
- Track concentration metric (% of items from top N sources) and display in UI.

## 7) Governance and Compliance
- Respect source terms/licensing and retention limits.
- Preserve retrieval metadata for audit.
- Maintain blocklist/allowlist controls in admin settings.
- Record all source configuration changes in immutable audit log.

## 8) Minimal-Code Boundaries for Source Integration
Use custom code only for:
1. Unsupported provider authentication handshake.
2. Non-standard response parsing impossible in no-code transforms.
3. Signature verification for secure enterprise feeds.

Each custom adapter must include:
- reason for existence,
- owner,
- test case references,
- replacement plan if native connector becomes available.

## 9) Stage Inputs/Outputs for Source Integration

**Inputs**
- Topic/date run manifest
- Source profile (region/language/priority)
- Credential status snapshot

**Outputs**
- Source Plan artifact
- Raw Retrieval Bundle artifact
- Source Health summary artifact

## 10) Assumptions
1. At least one API-key and one non-key source are available for initial deployment.
2. Credential vault integration is available in selected no-code platform.
3. Source policy/legal review process exists.

## 11) Unresolved Decisions
1. Initial prioritized source list by region/language.
2. Minimum viable source threshold value.
3. Source reliability tier model and who maintains it.

## 12) Risks/Blockers
- Source licensing delays or API contract limits.
- Connector instability for high-volume retrieval windows.
- Regional/language coverage gaps that bias findings.
