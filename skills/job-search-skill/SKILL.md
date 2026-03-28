---
name: job-search-skill
description: Thin agent-facing job search skill for the job-search plugin. Use when the agent should read a candidate profile, decide candidate understanding and search queries, and then call the plugin tools to prepare and run a job-search retrieval.
---

# Job Search Skill

This skill is now thin.

## Agent responsibilities

The agent should:
- read the candidate profile
- decide candidate understanding
- decide search queries
- decide per-query filters
- explain the reasoning clearly
- call the plugin tools instead of owning deterministic workflow mechanics itself

## Plugin tools

Use plugin tools for the deterministic steps:
- `job_search_prepare_run`
- `job_search_run_retrieval`
- `job_search_spawn_evaluators`
- `job_search_export_run`
- `job_search_full_run`

## Retrieval philosophy

- default to full-time unless the profile explicitly asks for internship or contract work
- the agent owns the search reasoning
- the plugin owns the run mechanics and artifact writing
