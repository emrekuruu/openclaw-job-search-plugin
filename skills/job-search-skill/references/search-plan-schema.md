# Search JSON Schema

The retrieval plan is a single file:

- `search.json`

The agent should write it from its own understanding of the profile.

## Shape

```json
{
  "runId": "2026-03-28-sample-software-engineer-profile",
  "createdAt": "2026-03-28T16:00:00+01:00",
  "profilePath": "/absolute/path/to/profile.md",
  "status": "draft",
  "candidateUnderstanding": {
    "seniority": "junior",
    "employmentIntent": "full-time",
    "roleFocus": ["software engineer", "backend engineer", "full stack engineer"],
    "locationIntent": ["Istanbul", "Remote Turkey"],
    "workModeIntent": ["hybrid", "remote"],
    "stackFocus": ["Java", "Spring Boot", "React", "Python"],
    "notes": "Recent graduate with internship experience; should be treated as early-career full-time, not internship-seeking."
  },
  "queries": [
    {
      "query": "Junior Software Engineer",
      "reasoning": "Primary early-career target role from the profile.",
      "filters": {
        "location": "Istanbul",
        "site_name": ["linkedin"],
        "job_type": "fulltime",
        "is_remote": false,
        "distance": 25,
        "results_wanted": 10,
        "hours_old": 720,
        "linkedin_fetch_description": true
      },
      "filterReasoning": {
        "location": "Candidate explicitly wants Istanbul roles.",
        "job_type": "Defaulted to full-time because internship was not requested.",
        "is_remote": "False because this query targets local Istanbul roles.",
        "distance": "Keep radius tight for local roles."
      }
    },
    {
      "query": "Software Engineer",
      "reasoning": "Remote Turkey variant for full-time software roles.",
      "filters": {
        "location": "Turkey",
        "site_name": ["linkedin"],
        "job_type": "fulltime",
        "is_remote": true,
        "distance": 1000,
        "results_wanted": 10,
        "hours_old": 720,
        "linkedin_fetch_description": true
      },
      "filterReasoning": {
        "location": "Use Turkey-wide location for remote roles.",
        "job_type": "Defaulted to full-time because internship was not requested.",
        "is_remote": "True because this query is explicitly the remote variant."
      }
    }
  }
}
```

## Rules

- The agent fills `candidateUnderstanding`.
- The agent writes every query.
- The agent writes every filter.
- Each query must have reasoning.
- Each filter should have reasoning when it matters.
- Scripts should execute the plan, not invent the plan.
