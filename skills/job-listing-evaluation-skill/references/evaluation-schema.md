# Evaluation Artifact Schema

Each evaluator should write one JSON file.

Canonical path:
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`

Shape:

```json
{
  "listingId": "string",
  "decision": "keep",
  "score": 84,
  "reasoning": "Strong junior backend fit with relevant Java/Spring experience; slight stretch on years requirement.",
  "dimensions": {
    "seniority": 90,
    "roleFit": 85,
    "stackFit": 78,
    "locationFit": 95
  },
  "flags": []
}
```

Failure artifact shape:

```json
{
  "listingId": "string",
  "error": "string",
  "details": "optional string"
}
```
