---
name: job-search-skill
description: Agent-controlled job retrieval for the job-search-bot project. Use when the agent should read a candidate profile, decide the search itself, use JobSpy directly, and write only a search.json plus one JSON file per listing. Keep the flow minimal and inspectable.
---

# Job Search Skill

Start over simple.

## What the agent should do

The agent should:
- read the candidate profile
- decide what the person is looking for
- decide the queries
- decide the filters for each query
- explain the reasoning in `search.json`
- use JobSpy directly
- write one JSON file per listing

## What to write

For each run, write only:
- `runtime-data/search-runs/<runId>/search.json`
- `runtime-data/search-runs/<runId>/listings/<listingId>.json`

Optional:
- `runtime-data/search-runs/<runId>/summary.md`

## search.json shape

The file should contain:
- `profilePath`
- `candidateUnderstanding`
- `queries`

Each query should contain:
- `query`
- `reasoning`
- `filters`
- `filterReasoning`

## Rules

- The agent owns all search decisions.
- Do not use regex-based extraction as the intelligence layer.
- Default to full-time unless the profile explicitly wants internship or contract work.
- Keep the retrieval process easy to inspect.
- Do not create extra intermediate artifacts unless absolutely necessary.
