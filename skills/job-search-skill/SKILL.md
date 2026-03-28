---
name: job-search-skill
description: Minimal agent-controlled job retrieval for the job-search-bot project. Use when an agent should read a candidate profile, decide the search queries and filters from its own understanding, write a simple search.json plan, run JobSpy searches, and save one JSON file per listing. Do not use regex-driven profile extraction or overbuilt intermediate processing. Keep the flow simple and inspectable.
---

# Job Search Skill

Run a simple retrieval flow.

## Philosophy

The agent should control the search.

Do not hide profile understanding inside regex-heavy scripts.
Do not generate a maze of intermediate artifacts.
Do not pretend the scripts are doing the thinking.

The agent should:
- read the profile
- decide what the candidate is looking for
- decide queries
- decide filters
- explain why each query exists
- explain why each filter was chosen

The scripts should only:
- create a blank `search.json`
- run JobSpy using the agent-authored queries and filters
- write one JSON file per listing
- render a readable summary

## Required artifacts

Each run should only need:
- `search.json`
- `listings/`

`search.json` should contain:
- profile path
- candidate understanding
- one entry per query
- reasoning for each query
- filters for each query
- reasoning for each filter

`listings/` should contain:
- one JSON file per retrieved listing

## Workflow

Use these scripts:

```bash
<pythonPath> skills/job-search-skill/scripts/prepare_search_run.py
# agent edits search.json
<pythonPath> skills/job-search-skill/scripts/search_backend_jobspy.py
<pythonPath> skills/job-search-skill/scripts/normalize_jobs.py
<pythonPath> skills/job-search-skill/scripts/render_search_summary.py
```

## Rules

1. Default to full-time unless the profile explicitly asks for internship or contract work.
2. Let the agent decide all queries and filters.
3. Keep each query explicit and justified.
4. Keep filters per-query, not hidden globally.
5. Keep the artifact structure minimal and easy to inspect.
6. Fail clearly if `search.json` is empty or malformed.
