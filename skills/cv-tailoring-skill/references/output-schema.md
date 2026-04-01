# CV Tailoring Output Schema

Use this shape for structured output:

```json
{
  "tailored_cv": {
    "summary": "string",
    "highlighted_experience": ["string"],
    "source_preservation_note": "string"
  },
  "match_score": {
    "score": 0,
    "matched_keywords": ["string"],
    "missing_keywords": ["string"],
    "method": "string"
  },
  "gap_analysis": {
    "strengths": ["string"],
    "gaps": ["string"],
    "notes": ["string"]
  },
  "keyword_pool": ["string"]
}
```

Rules:
- `tailored_cv` must stay grounded in the provided source profile.
- `match_score.score` is a lightweight heuristic, not a hiring recommendation.
- `gap_analysis.gaps` should reflect unsupported job requirements.
- Do not treat missing keywords as proof of inability; they only show absent evidence in the provided input.
