---
name: job-search-skill
description: Run single-pass job discovery as an agent-facing orchestration skill for the job-search-bot project. Use when an agent needs to invoke the project’s own runtime, Python environment, config, and output directories to collect live jobs from a configured candidate profile. Do not use for ranking, applications, resume tailoring, tracking, or interview preparation. Fail clearly if the project runtime or live backend is unavailable.
---

# Job Search Skill

Use this skill to run **Step 1: discovery and collection** for the `job-search-bot` project.

This skill is **project-centric**.
It does not pretend to be the entire runtime system. Instead, it tells the agent how to invoke the real project runtime cleanly.

## What this skill does

This skill:

- reads the project runtime configuration from `config/runtime.json`
- uses the project Python runtime defined there
- reads the configured profile path
- prepares a search run
- runs a live JobSpy-backed backend search
- saves raw backend results
- normalizes results into the project schema
- renders a human-readable run summary

This skill does **not** yet do:

- ranking/scoring
- resume tailoring
- cover letters
- applications
- lifecycle tracking
- interview preparation

## Project runtime requirements

The project runtime configuration should exist at:

- `config/runtime.json`

That config should define at least:

- `projectRoot`
- `pythonPath`
- `outputBase`
- `defaultProfile`
- `searchDefaultsPath`

The Python runtime defined by `pythonPath` must have the required packages installed, including:

- `python-jobspy`
- `pandas`
- `pydantic`

If the runtime config, Python path, or live backend is unavailable, fail clearly.
Do not silently produce fallback data.

## Default project runtime paths

Current project defaults:

- runtime config: `config/runtime.json`
- search defaults: `config/search-defaults.json`
- runtime data base: `runtime-data/`
- default profile: `runtime-data/profiles/sample-software-engineer-profile.md`

## Single-pass workflow

### 1. Confirm project runtime

Read `config/runtime.json`.

Check that the configured Python interpreter exists and can import `jobspy`.

### 2. Use the configured profile path

Use `defaultProfile` unless the task explicitly asks for another profile path.

### 3. Run the project workflow

Use the configured Python interpreter to run these scripts from the project root:

```bash
<pythonPath> skills/job-search-skill/scripts/prepare_search_run.py
<pythonPath> skills/job-search-skill/scripts/search_backend_jobspy.py
<pythonPath> skills/job-search-skill/scripts/normalize_jobs.py
<pythonPath> skills/job-search-skill/scripts/render_search_summary.py
```

### 4. Inspect outputs

Inspect the latest files under the configured `outputBase`, especially:

- `search-runs/`
- `raw/`
- `jobs/`

The run should produce:

- a run JSON file
- a run summary markdown file
- a raw backend JSON file
- a normalized jobs JSON file

## Operational guidance

- Treat this as a discovery-only skill
- Prefer collecting plausible results over aggressive filtering
- Preserve backend traceability in saved files
- If the live backend fails, surface the failure clearly
- Do not fabricate fallback data
- Present the run summary first when reporting to the user

## Success condition

A successful run produces live backend output, normalized saved job records, and a readable summary inside the project runtime-data area.

## References

- `references/run-notes.md`
- `references/backend-notes.md`
- `references/notes.md`
