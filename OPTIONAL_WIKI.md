# OPTIONAL_WIKI.md

## Status
Optional. Off by default.

## Only activate when a user explicitly requests:
- a wiki
- persistent topic pages
- cumulative tracking
- cross-run memory
- knowledge base updates

## Purpose
The wiki layer converts validated run outputs into durable pages:
- topic pages
- entity pages
- event pages
- timeline pages
- run summary pages

## Rules
- do not use silently
- do not overwrite prior knowledge without change tracking
- preserve citations and uncertainty
- run lint checks on the wiki layer when it is used

## Difference from the Main System
Main system:
- answers what happened in this run

Optional wiki:
- answers what is known overall across runs
