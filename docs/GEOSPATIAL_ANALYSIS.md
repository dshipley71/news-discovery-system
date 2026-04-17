# Geospatial Analysis Operating Manual

## Purpose
Define the implemented backend geospatial stage and artifacts for analyst inspection.

## Stage Placement
Implemented order in `run_workflow`:

**Normalization -> Clustering -> Citation -> Geospatial -> Evidence -> Warnings -> Aggregation**

(Geospatial markers are also mirrored into aggregation for UI compatibility.)

## Geospatial Entity Contract
Each entity in `stages.geospatial.entities[]` includes:
- `location_id`
- `article_id`
- `location_key`
- `city`
- `region_or_state`
- `country`
- `latitude`
- `longitude`
- `confidence`
- `extraction_method` (`explicit` currently implemented)
- `ambiguity_flag`
- `ambiguity_notes`
- `evidence_text`
- `evidence_linkage` (includes article reference)

## Marker Contract
Each marker in `stages.geospatial.map_markers[]` includes:
- `location_label`
- location fields (`city`, `region_or_state`, `country`, coordinates)
- `article_ids` (unique, deduplicated)
- `unique_article_count`
- `avg_confidence`
- `ambiguous_count`
- `location_ids`
- `evidence_linkage`

## Duplicate Inflation Guard
Marker counts are based on unique canonical article IDs so duplicate variants do not inflate map activity.

## Explicit vs Inferred
- **Explicit:** implemented via deterministic text matching against the location lexicon.
- **Inferred:** not broadly implemented yet; reserved for future resolver expansion.

## Ambiguity Handling
Ambiguous locations are flagged in entity and marker artifacts and feed warning generation.

## Deferred
- Expanded resolver/geocoder coverage.
- Rich inferred-location strategy beyond explicit lexical matches.
