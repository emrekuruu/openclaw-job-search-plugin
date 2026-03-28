---
name: job-search-skill
description: Minimal agent-controlled job retrieval for the job-search-bot project. Use when the agent should read a candidate profile, decide the search itself, write a simple search.json plan, use JobSpy directly through the bundled runner script, and save one JSON file per listing. Keep the flow minimal, clean, and inspectable.
---

# Job Search Skill

Keep this simple.

## What the agent does

The agent should:
- read the stable repo-owned candidate profile
- understand the candidate from the profile itself
- decide the queries
- decide the filters for each query
- explain the reasoning in `search.json`
- run JobSpy using the bundled script
- inspect the listing JSON outputs

Do not push candidate understanding into regex-heavy scripts.
The agent owns the search decisions.

## Required artifacts

For each run, keep only:
- `runtime-data/search-runs/<runId>/search.json`
- `runtime-data/search-runs/<runId>/listings/<listingId>.json`

That is the core retrieval output.

Optional:
- `runtime-data/search-runs/<runId>/summary.md`

## Required `search.json` shape

The file should contain:
- `profilePath`
- `candidateUnderstanding`
- `queries`

Each query should contain:
- `query`
- `reasoning`
- `filters`
- `filterReasoning`

Example shape:

```json
{
  "runId": "2026-03-28-sample-profile",
  "profilePath": "/absolute/path/to/profile.md",
  "candidateUnderstanding": {
    "seniority": "junior",
    "employmentIntent": "full-time",
    "roleFocus": ["software engineer", "backend engineer"],
    "notes": "Recent graduate with internship background, but seeking full-time roles."
  },
  "queries": [
    {
      "query": "Junior Software Engineer",
      "reasoning": "Primary early-career target from the profile.",
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
        "location": "Candidate explicitly prefers Istanbul.",
        "job_type": "Default to full-time because internship is not requested.",
        "is_remote": "False because this query targets local roles."
      }
    }
  ]
}
```

## Script

Use:

```bash
<pythonPath> skills/job-search-skill/scripts/run_jobspy_search.py
```

The script should:
- read the latest `search.json`
- run the agent-authored queries with JobSpy
- write one JSON file per listing into `listings/` with deterministic collision-safe filenames
- update `search.json` with execution details

## Rules

1. The agent owns all search decisions.
2. Default to full-time unless the profile explicitly wants internship or contract work.
3. Keep each query explicit and justified.
4. Keep filters per-query, not hidden globally.
5. Keep the artifact structure minimal.
6. Fail clearly if `search.json` is missing or malformed.
7. Do not add extra intermediate files unless they are truly necessary.
