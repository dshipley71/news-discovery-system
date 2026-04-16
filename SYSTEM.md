# SYSTEM.md

## Purpose
Define the main operating model for the no-source-code news intelligence system.

## Required Inputs
- topic
- date window in days

## Default Mode
- wiki off
- bounded run
- evidence-backed markdown outputs
- editable artifact workspace

## Agent Model
1. User Intent Agent
2. Source Routing Agent
3. Source Collection Layer
4. Normalization & Deduplication Agent
5. Clustering Agent
6. Temporal Analytics Agent
7. Geospatial Analysis Agent
8. Sentiment/Tone Agent
9. Narrative Analysis Agent
10. Report Synthesis Agent
11. Critic / Quality Agent

## Workflow
1. Capture topic and days
2. Route source strategy
3. Collect candidate articles
4. Normalize metadata
5. Deduplicate
6. Create event clusters
7. Run temporal analysis
8. Run geospatial analysis
9. Run sentiment/tone analysis
10. Compare narratives
11. Build citations
12. Draft final report
13. Check quality gates

## Routing Rules
- prefer source diversity
- avoid single-source dominance
- deduplicate before analysis
- keep wiki off unless explicitly requested

## Core Records
### Article Record
- id
- title
- source
- date
- url
- evidence_level
- cluster_id
- sentiment
- entities

### Cluster Record
- cluster_id
- name
- description
- key_articles
- notes

### Citation Record
- claim
- cluster
- articles
- sources
- label

## Quality Gates
A run is complete only if:
- major claims are cited
- peaks are explained
- clusters are defined
- deduplication is performed
- limitations are stated
- wiki remains off unless explicitly requested
