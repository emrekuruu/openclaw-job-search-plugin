# Evaluation Artifact Schema

Each evaluator should write one JSON file.

Canonical path:
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`

Canonical shape:

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

Rules:

- `dimensions` are required, not optional
- every dimension score must be normalized to `0-100`
- final `score` must be normalized to `0-100`
- `decision` must be exactly one of `keep`, `maybe`, or `drop`
- the final `score` should be consistent with the dimension scores

Failure artifact shape:

```json
{
  "listingId": "string",
  "error": "string",
  "details": "optional string"
}
```
