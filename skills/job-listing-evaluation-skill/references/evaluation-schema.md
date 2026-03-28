# Evaluation Schema

Use this schema when evaluating a collected job listing against a candidate profile.

## Scoring model

Use **one score system everywhere**:
- `score` is the final 0-100 fit score.
- Optional dimension scores should also be 0-100.
- Do not mix 0-5 and 0-100 in the same evaluation output.

## Evaluation dimensions

Suggested dimensions, each on a 0-100 scale:

1. **roleFamilyAlignment**
   - 100: same target family
   - 60: adjacent but plausible
   - 0: clearly different family

2. **seniorityFit**
   - 100: explicitly aligned
   - 60: slightly above or ambiguous
   - 0: clearly too senior or managerial

3. **experienceFit**
   - 100: years/requirements match
   - 60: stretch but plausible
   - 0: clearly above profile

4. **skillsStackFit**
   - 100: strong overlap with proven stack
   - 60: partial overlap, learnable gap
   - 0: mostly unrelated stack

5. **domainCompanyFit**
   - 100: preferred company or strong domain match
   - 60: neutral
   - 0: domain strongly conflicts with candidate direction

6. **locationWorkModeFit**
   - 100: fits stated constraints
   - 60: partially fits or unclear
   - 0: clearly conflicts

7. **practicalConstraints**
   - 100: no obvious blockers
   - 60: one mild unknown
   - 0: obvious blocker such as authorization, language, relocation, or schedule mismatch

## Decision guidance

- `keep`: usually `score >= 70` and no hard blocker
- `drop`: any hard blocker, obvious seniority mismatch, clear role-family mismatch, or `score < 60`
- Borderline cases: prefer `drop` if the mismatch would predictably waste the candidate's time

## Output shape

Write one JSON object per evaluated listing to the evaluator's assigned output path.

```json
{
  "listingId": "job-001",
  "runId": "2026-03-28-sample-profile",
  "profilePath": "/absolute/path/to/profile.md",
  "listingPath": "/absolute/path/to/runtime-data/search-runs/2026-03-28-sample-profile/listings/job-001.json",
  "decision": "keep",
  "score": 84,
  "reasoning": "Matches backend/software target family, junior level is aligned, and the stack overlap looks interview-viable.",
  "dimensions": {
    "roleFamilyAlignment": 95,
    "seniorityFit": 95,
    "experienceFit": 80,
    "skillsStackFit": 82,
    "domainCompanyFit": 65,
    "locationWorkModeFit": 95,
    "practicalConstraints": 75
  },
  "flags": [],
  "evaluatedAt": "2026-03-28T17:00:00+01:00"
}
```

Canonical path:
- `runtime-data/evaluations/<runId>/<listingId>.json`

Optional failure artifact:
- `runtime-data/evaluations/<runId>/<listingId>.error.json`

## Required reasoning style

- Keep it short.
- Reference evidence from the listing or profile.
- Return `reasoning` as a concise string, not a markdown block.
- Prefer concrete mismatch labels in `flags` such as:
  - `seniority-mismatch`
  - `experience-mismatch`
  - `role-family-mismatch`
  - `location-mismatch`
  - `work-mode-mismatch`
  - `authorization-risk`
  - `stack-gap`
  - `managerial-role`
