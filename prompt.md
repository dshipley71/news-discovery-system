Write a complete, production-quality AGENTS.md pattern for a no-source-code, agent-driven news intelligence system.

Goal:
Create an AGENTS.md framework that defines how one or more agents should search current news sources for a user-specified topic, analyze coverage over time, generate timeline plots of article volume, identify trends and peaks, and produce an extensive written report explaining the likely causes of those trends or peaks.

This must be a pattern only.
Do NOT generate source code.
Do NOT generate implementation files other than AGENTS.md-style pattern files and any closely related markdown pattern files if needed.
Do NOT include pseudocode that looks like executable code.
Do NOT rely on any specific library, framework, API, or vendor.
Do NOT copy from any reference project.

Use the following only as conceptual inspiration for the kind of structured, schema-driven, agent-operating-manual approach I want:
A repo pattern in which an AI agent follows a schema/manual file to ingest sources, build structured outputs, maintain repeatable workflows, and produce durable markdown artifacts. The reference point is similar in spirit to a schema-first operating manual that tells the AI how to behave, what artifacts to create, and how to maintain them over time. Do not reproduce that project’s structure literally, and do not mention or depend on it in the generated pattern. The intended output here is for current news intelligence, not wiki generation. The reference project uses a schema/manual file to direct AI behavior and organizes raw inputs and generated markdown outputs into a persistent knowledge workflow. :contentReference[oaicite:0]{index=0}

Requirements:
1. The AGENTS.md pattern must be designed for current-news research on a user-specified subject.
2. The time window must be configurable by the user from 1 day up to 30 days, ending at the present day.
3. The system must search across multiple news sources.
4. The pattern should support either:
   - one agent per source, or
   - one agent handling multiple sources,
   and it should explain the tradeoffs between those designs.
5. The pattern must define agent roles, responsibilities, handoffs, inputs, outputs, validation rules, and stopping conditions.
6. The pattern must define a workflow that:
   - accepts a user topic and date range
   - gathers articles from multiple news sources
   - normalizes article metadata
   - deduplicates and clusters related coverage
   - aggregates article counts by time
   - generates timeline plots versus article counts
   - identifies peaks, surges, and persistent trends
   - analyzes the likely drivers behind those peaks/trends
   - produces an extensive final report
7. The pattern must explicitly address source reliability, duplication, recency, conflicting narratives, and uncertainty.
8. The pattern must include reporting standards so the final narrative distinguishes:
   - confirmed observations
   - plausible inferences
   - unresolved uncertainty
9. The pattern must define how to handle sparse coverage, noisy coverage, contradictory coverage, and breaking-news spikes.
10. The pattern must be implementation-agnostic and remain useful regardless of the eventual tech stack.

Deliverable format:
Produce the output as a well-structured markdown pattern package with the following sections.

A. AGENTS.md
Include:
- purpose
- scope
- system philosophy
- operating constraints
- agent roster
- agent responsibilities
- inputs and outputs per agent
- orchestration flow
- routing rules
- decision rules
- artifact definitions
- quality standards
- failure modes
- validation checklist
- extensibility guidance

B. Optional companion markdown pattern files if helpful
You may add markdown-only companion pattern files such as:
- WORKFLOWS.md
- OUTPUTS.md
- ARTIFACTS.md
- EVALUATION.md
- ROUTING_RULES.md
But only if they improve clarity.
These must also be patterns only, with no code.

Design expectations:
- The pattern should feel “enterprise-grade.”
- It should be specific enough that another AI system could use it as an operating manual.
- It should emphasize repeatability, auditability, and clean separation of responsibilities.
- It should define durable output artifacts in markdown form.
- It should define a standard reporting artifact for each run.

The pattern must include, at minimum, these agent concepts:
1. User Intent / Query Agent
   Interprets the topic, time range, and reporting objective.
2. Source Discovery or Source Routing Agent
   Decides which news sources to search.
3. Per-Source Collection Agents or a Source Collection Layer
   Collects candidate articles and metadata from each source.
4. Normalization and Deduplication Agent
   Standardizes metadata and removes duplicates/reposts/syndications.
5. Temporal Analytics Agent
   Builds the article-count timeline and identifies peaks, bursts, and trend intervals.
6. Trend Interpretation Agent
   Explains likely causes of peaks or sustained changes in coverage.
7. Report Synthesis Agent
   Produces the final extensive report with evidence-based reasoning.
8. Quality / Critic Agent
   Checks consistency, unsupported claims, and reporting completeness.

The pattern must define standard artifacts such as:
- run brief
- source ledger
- normalized article registry
- duplicate/syndication log
- temporal summary
- peak analysis memo
- trend analysis memo
- final report
- confidence and limitations note

The pattern must define what the final report should contain:
- user topic and date window
- sources searched
- summary of total coverage volume
- daily timeline interpretation
- identified peaks and why they likely occurred
- identified sustained trends and why they likely occurred
- notable article clusters or narrative themes
- cross-source comparisons
- uncertainty and limitations
- executive summary
- detailed analytical narrative
- appendix of evidence references

The pattern must define rules for temporal analysis, including:
- daily aggregation minimum
- optional hourly aggregation when appropriate
- how to define a peak
- how to define a trend
- how to distinguish isolated spikes from sustained momentum
- how to treat weekends, publication batching, and breaking-news bursts
- how to compare source-specific spikes versus cross-source spikes

The pattern must define reasoning safeguards:
- do not confuse article volume with real-world importance
- do not over-attribute causation without evidence
- clearly separate observed timing correlation from causal explanation
- identify when peaks may be caused by wire-service syndication or reposting
- identify when peaks may be caused by a single major triggering event
- identify when trends may reflect slow-burn developments rather than one event

The pattern must define source strategy:
- heterogeneous source coverage
- source-specific bias awareness
- mainstream vs niche source balance
- local vs national vs international coverage when relevant
- trade press vs general press when relevant
- how to note when one source dominates the signal

The pattern must define user-configurable inputs:
- topic
- date window (1–30 days up to present)
- optional geography
- optional source preferences
- optional exclusion terms
- optional granularity preference
- optional report depth

The pattern must define output quality levels:
- quick brief
- standard report
- extensive report

The pattern must end with:
1. a concise recommended default multi-agent layout
2. an alternative simpler single-orchestrator layout
3. a short explanation of when to choose each

Writing style requirements:
- crisp, operational, and directive
- markdown only
- no code
- no placeholders like “TODO”
- no generic fluff
- no references to implementation details
- no copying from reference repos
- no mention of any programming language
- no mention of package installation
- no diagrams required, but structural tables are allowed

Important:
The pattern should be tailored specifically for a news-search-and-temporal-analysis system, not a generic research agent and not a wiki builder.

Additional Required Enhancements:

1. Geospatial Analysis Layer
The pattern must include extraction and aggregation of geographic information from articles.

Define:
- location extraction (city, region, country)
- aggregation of article counts by location
- activity intensity scoring
- clustering of nearby locations when appropriate

Define a required “Geospatial Map Artifact” that includes:
- a heat-style or marker-based map
- color-coded intensity levels (low → high)
- marker size based on article volume
- optional differentiation by event cluster or source

Define a clear legend standard explaining:
- color meaning (activity intensity)
- marker size meaning (volume)
- marker type meaning (event type or cluster)

2. Citation and Evidence Framework
The pattern must enforce strict citation and traceability rules.

Define:
- all major claims must be supported by one or more citations
- citations must link back to normalized article records
- clustering must preserve source attribution

Define required artifacts:
- citation index
- evidence bundles per identified peak or trend
- source traceability mapping (claim → cluster → articles)

Require explicit distinction between:
- directly supported claims
- inferred conclusions
- speculative explanations

3. Event Clustering Requirement
The pattern must include grouping of related articles into event clusters.

Define:
- clustering of articles into coherent events/topics
- assignment of cluster identifiers
- linking of clusters to timeline peaks

4. Narrative Comparison Layer
The pattern must detect and report differences across sources.

Define:
- identification of agreement vs divergence across sources
- detection of conflicting narratives or framing differences

Include a required report section:
- “Cross-Source Narrative Comparison”

5. Confidence Scoring
The pattern must define a confidence scoring system.

Apply scoring to:
- peak explanations
- trend interpretations
- cluster significance

Factors may include:
- number of independent sources
- source diversity
- temporal consistency
- duplication vs original reporting

6. Source Weighting and Deduplication
The pattern must include:
- identification of syndicated content
- reduction of duplicate influence
- weighting of sources to avoid bias

7. Temporal Resolution and Smoothing
The pattern must define:
- default daily aggregation
- optional hourly aggregation for high-activity periods
- smoothing techniques (e.g., rolling averages)
- rules for distinguishing spikes vs sustained trends

8. Iterative Refinement Loop
The pattern must allow a critic agent to trigger limited reprocessing.

Allow:
- query refinement
- source expansion
- re-clustering

Limit:
- maximum number of refinement cycles

9. Visualization Artifacts
The pattern must require the following outputs:
- timeline plot of article counts
- annotated peaks and trends
- geospatial activity map
- cluster summary table
