---
name: job-listing-evaluation-skill
description: Thin evaluator skill for the job-search plugin. Use when one evaluator agent should read one listing plus one profile and write one evaluation JSON artifact.
---

# Job Listing Evaluation Skill

This skill is now thin.

## Evaluator responsibilities

The evaluator agent should:
- read one candidate profile
- read one listing JSON file
- decide keep or drop
- assign a 0-100 score
- provide concise reasoning
- write one JSON artifact for that listing

## Required artifact

Write one JSON file per evaluated listing under:
- `runtime-data/evaluations/<runId>/<listingId>.json`

Optional failure artifact:
- `runtime-data/evaluations/<runId>/<listingId>.error.json`
