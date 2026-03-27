---
name: job-search-skill
description: Run single-pass job discovery for the Automated Job Search project using a profile file, the skill-local JobSpy-backed search pipeline, and project-owned normalization/output files. Use when an agent needs to find and collect jobs from a candidate profile, desired roles, locations, and target companies, then save raw results, normalized job records, and a summary. Do not use for ranking, applications, resume tailoring, tracking, or interview preparation.
---

# Job Search Skill

Use this skill to run **Step 1: discovery and collection** inside the `job-search-bot` project.

This skill is agent-facing. It tells the agent how to perform one discovery pass using the skill-local pipeline, which currently uses a JobSpy-backed local adapter.

## What this skill does

This skill:

- reads a candidate profile from `data/profiles/`
- prepares a search run
- runs the local JobSpy-backed backend search
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

## Required project context

Run this skill from the project root.

Expected project structure:

- `pyproject.toml`
- `uv.lock`
- `.venv/`
- `config/search-defaults.json`
- `data/profiles/`
- `data/search-runs/`
- `data/raw/`
- `data/jobs/`
- `skills/job-search-skill/scripts/`

Default profile example:

- `data/profiles/sample-candidate-profile.md`

## Single-pass workflow

### 1. Confirm environment

From project root:

```bash
uv sync
source .venv/bin/activate
```

If the environment is already synced, activating `.venv` is enough.

### 2. Choose the profile file

Use a profile file under `data/profiles/`.

If the user does not specify a path, default to:

- `data/profiles/sample-candidate-profile.md`

### 3. Run the discovery pipeline

Run these scripts in order from the project root:

```bash
python skills/job-search-skill/scripts/prepare_search_run.py
python skills/job-search-skill/scripts/search_backend_jobspy.py
python skills/job-search-skill/scripts/normalize_jobs.py
python skills/job-search-skill/scripts/render_search_summary.py
```

### 4. Inspect outputs

After the run, inspect the latest files in:

- `data/search-runs/`
- `data/raw/`
- `data/jobs/`

The run should produce:

- a run JSON file
- a run summary markdown file
- a raw backend JSON file
- a normalized jobs JSON file

## Operational guidance

- Treat this as a discovery-only skill
- Prefer collecting plausible results over aggressive filtering
- Preserve backend traceability in saved files
- If some sources fail, keep successful results and note source-specific failures
- Use the project’s normalized schema rather than backend-native field names

## Backend note

The current implementation uses the skill-local script pipeline and a JobSpy-backed adapter in `skills/job-search-skill/scripts/search_backend_jobspy.py`.

Conceptually this corresponds to the `job-search-mcp-jobspy` discovery direction, but the current implementation is project-local and script-driven.

## Success condition

A successful run produces real or fallback backend output plus normalized saved job records and a readable summary in the project data directories.

## References

- `references/run-notes.md`
- `../../specs/step-1-wrapper-contract.md`
- `../../specs/backend-mappings/job-search-mcp-jobspy-runtime.md`
