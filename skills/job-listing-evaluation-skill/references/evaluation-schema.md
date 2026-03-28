# Evaluation Schema

Use this schema when evaluating collected job listings against a candidate profile.

## Evaluation dimensions

Score each dimension on a 0-5 scale.

1. **Role-family alignment**
   - 5: same target family
   - 3: adjacent but plausible
   - 0: clearly different family

2. **Seniority fit**
   - 5: explicitly aligned
   - 3: slightly above or ambiguous
   - 0: clearly too senior or managerial

3. **Experience fit**
   - 5: years/requirements match
   - 3: stretch but plausible
   - 0: clearly above profile

4. **Skills/stack fit**
   - 5: strong overlap with proven stack
   - 3: partial overlap, learnable gap
   - 0: mostly unrelated stack

5. **Domain/company fit**
   - 5: preferred company or strong domain match
   - 3: neutral
   - 0: domain strongly conflicts with candidate direction

6. **Location/work-mode fit**
   - 5: fits stated constraints
   - 3: partially fits or unclear
   - 0: clearly conflicts

7. **Practical constraints**
   - 5: no obvious blockers
   - 3: one mild unknown
   - 0: obvious blocker such as authorization, language, relocation, or schedule mismatch

## Decision guidance

- `keep`: usually total score >= 24 and no zero in a critical dimension
- `drop`: any hard blocker, obvious seniority mismatch, clear role-family mismatch, or total score < 20
- Borderline cases: prefer `drop` if the mismatch would predictably waste the candidate's time

## Output shape

```json
{
  "candidateSummary": {
    "targetRoleFamily": ["software engineer", "backend engineer"],
    "seniority": "junior",
    "experienceYears": 2,
    "locations": ["Istanbul"],
    "workModes": ["hybrid", "remote"]
  },
  "evaluations": [
    {
      "listingId": "job-001",
      "title": "Junior Backend Engineer",
      "company": "Example Co",
      "decision": "keep",
      "score": 29,
      "dimensions": {
        "roleFamilyAlignment": 5,
        "seniorityFit": 5,
        "experienceFit": 4,
        "skillsStackFit": 4,
        "domainCompanyFit": 3,
        "locationWorkModeFit": 5,
        "practicalConstraints": 3
      },
      "reasoning": [
        "Matches backend/software target family.",
        "Junior title aligns with candidate seniority.",
        "Stack overlap is strong enough for interview viability."
      ],
      "flags": []
    },
    {
      "listingId": "job-002",
      "title": "Senior Engineering Manager",
      "company": "Example Co",
      "decision": "drop",
      "score": 4,
      "dimensions": {
        "roleFamilyAlignment": 1,
        "seniorityFit": 0,
        "experienceFit": 0,
        "skillsStackFit": 1,
        "domainCompanyFit": 1,
        "locationWorkModeFit": 1,
        "practicalConstraints": 0
      },
      "reasoning": [
        "Managerial leadership role is outside the target IC path.",
        "Required seniority is far above the candidate profile."
      ],
      "flags": ["seniority-mismatch", "managerial-role"]
    }
  ]
}
```

## Required reasoning style

- Keep it short.
- Reference evidence from the listing or profile.
- Prefer concrete mismatch labels in `flags` such as:
  - `seniority-mismatch`
  - `experience-mismatch`
  - `role-family-mismatch`
  - `location-mismatch`
  - `work-mode-mismatch`
  - `authorization-risk`
  - `stack-gap`
  - `managerial-role`
