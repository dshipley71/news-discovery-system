# ANALYSIS.md

## Temporal Analysis
- default aggregation: daily
- optional hourly overlay for the highest-activity period
- explain peaks using clusters, not raw counts
- distinguish isolated spikes, bursts, sustained trends, and anomalies

## Geospatial Analysis
- extract city, region, and country when available
- represent activity nodes and impact locations
- do not imply unrelated physical incidents
- recommended map conventions:
  - color = intensity
  - size = volume
  - optional symbol = cluster/type
  - legend required

## Sentiment / Tone Analysis
Required labels:
- positive
- negative
- neutral
- mixed

Optional dimensions:
- conflict
- fear
- uncertainty
- optimism

Rules:
- sentiment does not equal truth
- compare tone across sources, clusters, and time
- highlight tone shifts during peaks

## Narrative Analysis
Identify:
- agreement
- divergence
- conflicting claims
- framing differences

Required output:
- narrative comparison memo
