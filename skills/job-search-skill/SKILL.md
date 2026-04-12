---
name: job-search-skill
description: Run the retrieval side of the job-search workflow through skill-owned scripts and references. Use when the agent should read a candidate profile, decide candidate understanding and search queries, prepare a run through the thin plugin, then execute JobSpy retrieval through the skill's Python script instead of plugin-internal process logic.
---

# Job Search Skill

This skill owns retrieval logic and query planning.

## Use this skill for

- reading the candidate profile
- deciding candidate understanding
- deciding search queries and retrieval filters
- preparing a run with the thin plugin
- executing JobSpy retrieval through the skill script
- summarizing retrieval outcomes and artifact paths

## Read first

Before preparing run queries, read:
- `references/query-schema.md`

If environment readiness is unclear, use:
- `../environment-check/SKILL.md` (`environment-check`)

## Split of responsibilities

### Thin plugin owns
- run creation
- state-dir artifact layout
- resume path helpers
- resume import
- resume rendering
- export / aggregation

### This skill owns
- retrieval-specific reasoning
- query/filter planning
- running the Python JobSpy script
- interpreting retrieval results

## Scripts

Use:
- `scripts/prepare_run.py`
- `scripts/run_jobspy_search.py`

`prepare_run.py` creates the state-backed run layout and writes `search.json`.

`run_jobspy_search.py` reads that `search.json`, executes retrieval, writes listing artifacts, updates `search.json`, and prints the final `searchPath`.

## Expected workflow

1. Read the candidate profile.
2. Build candidate understanding and search queries.
3. Run `scripts/prepare_run.py` with a small JSON payload containing `profilePath`, optional `runId`, `candidateUnderstanding`, and `queries`.
4. Run `scripts/run_jobspy_search.py` with the correct environment.
5. Read the updated `search.json`.
6. Continue with evaluation and resume-generation skills.

## Notes

- retrieval artifacts live under the OpenClaw state dir, not the repo
- prefer bounded, high-quality queries over noisy broad retrieval
- default to full-time unless the profile clearly asks for something else
- if retrieval fails, surface actionable setup guidance rather than opaque Python tracebacks
