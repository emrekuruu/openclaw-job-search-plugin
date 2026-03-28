---
name: job-search-skill
description: Thin agent-facing job search skill for the job-search plugin. Use when the agent should read a candidate profile, decide candidate understanding and search queries, and then call the plugin tools. JobSpy retrieval itself lives in this skill's Python script, while the plugin owns orchestration/state/export.
---

# Job Search Skill

This skill is thin, but it still owns the JobSpy-specific retrieval worker.

## Agent responsibilities

The agent should:
- read the caller-provided candidate profile
- decide candidate understanding
- decide search queries
- decide per-query filters
- explain the reasoning clearly
- call the plugin tools instead of owning deterministic workflow mechanics itself

## Split of responsibilities

### Plugin owns
- run creation
- state-dir artifact layout
- evaluator fanout
- export / aggregation
- runtime worker readiness checks and actionable failure messages

### This skill owns
- the JobSpy retrieval worker script
- retrieval-specific guidance
- cooperating with plugin-created `search.json`

## Retrieval script

JobSpy stays here:
- `skills/job-search-skill/scripts/run_jobspy_search.py`

The plugin calls this Python script to execute retrieval against the current state-backed run.

## Python environment

The retrieval worker depends on the plugin repo's Python environment defined in `pyproject.toml`.

Recommended setup:

```bash
uv sync
```

The plugin prefers `JOB_SEARCH_PYTHON` when set, otherwise `.venv/bin/python3`, then `python3`.
If imports are missing, the plugin now fails early with setup guidance instead of surfacing an opaque runtime crash from the worker.

## Retrieval philosophy

- default to full-time unless the profile explicitly asks for internship or contract work
- the agent owns the search reasoning
- the plugin owns orchestration and artifact layout
- runtime artifacts live under the OpenClaw state dir, not in the repo checkout
