---
name: job-listing-evaluation-skill
description: Thin evaluator skill for the job-search plugin. Use when one evaluator agent should read one listing plus one profile and write one evaluation JSON artifact.
---

# Job Listing Evaluation Skill

This skill is now thin.

## Evaluator responsibilities

The evaluator agent should:
- read one candidate profile from the provided `profilePath`
- read one listing JSON file
- decide `keep`, `maybe`, or `drop`
- assign normalized dimension scores
- derive a final normalized 0-100 score from those dimensions
- provide concise reasoning
- write one JSON artifact for that listing

## Required artifact

Write one JSON file per evaluated listing under the plugin's OpenClaw state storage:
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`

Optional failure artifact:
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.error.json`

## Required output schema

`dimensions` are required, not optional.
The final `score` must be normalized to 0-100 and must be consistent with the dimension scores.

Required JSON shape:

```json
{
  "listingId": "string",
  "decision": "keep|maybe|drop",
  "score": 78,
  "reasoning": "Concise explanation.",
  "dimensions": {
    "roleFit": 85,
    "seniorityFit": 90,
    "locationFit": 70,
    "domainFit": 80,
    "skillsFit": 65
  }
}
```

## Dimension guidance

Use normalized 0-100 scores for each dimension:
- `roleFit` — how well the role matches software/backend/full-stack targets
- `seniorityFit` — how well the role matches entry-level/junior profile level
- `locationFit` — how well the role matches Istanbul / Turkey / remote-Turkey constraints
- `domainFit` — how well the industry/company context matches banking-tech / fintech / software preferences
- `skillsFit` — how well the required stack matches the candidate's actual skills and experience

The final `score` should be a sensible aggregate of these dimensions, not an arbitrary number.
