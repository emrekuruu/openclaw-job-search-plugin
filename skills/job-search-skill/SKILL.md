---
name: job-search-skill
description: Run single-pass job discovery as a fully self-contained skill using a bundled profile, bundled config, and a JobSpy-backed local search pipeline. Use when an agent needs to find and collect jobs from the skill’s own profile/config context, save raw live results, normalize job records, and render a summary. Do not use for ranking, applications, resume tailoring, tracking, or interview preparation. Fail clearly if the environment or live backend is unavailable.
---

# Job Search Skill

Use this skill to run **Step 1: discovery and collection** as a self-contained installed skill.

This skill is agent-facing and self-contained. It ships with its own scripts, config, and sample profile data. It should be able to run from its installed location without relying on an external project repo.

## What this skill does

This skill:

- reads a candidate profile from `data/profiles/`
- prepares a search run
- runs a live JobSpy-backed backend search
- saves raw backend results
- normalizes results into the skill’s local schema
- renders a human-readable run summary

This skill does **not** yet do:

- ranking/scoring
- resume tailoring
- cover letters
- applications
- lifecycle tracking
- interview preparation

## Runtime requirement

This skill expects a dedicated shared Python runtime for OpenClaw skills at:

- `~/.openclaw-skill-venv/bin/python`

That runtime should have at least:

- `python-jobspy`
- `pandas`
- `pydantic`

If that interpreter does not exist or `jobspy` is not importable there, the skill should fail clearly.
Do not silently produce fallback results.

## Bundled skill structure

Expected local structure inside the installed skill:

- `config/search-defaults.json`
- `data/profiles/`
- `data/search-runs/`
- `data/raw/`
- `data/jobs/`
- `scripts/`

Default bundled profile:

- `data/profiles/sample-software-engineer-profile.md`

## Single-pass workflow

### 1. Confirm runtime

Check that this interpreter exists and works:

```bash
~/.openclaw-skill-venv/bin/python -c "import jobspy; print(jobspy.__file__)"
```

If this fails, stop and report the runtime issue clearly.

### 2. Choose the profile file

Use a profile file under `data/profiles/`.

If the user does not specify a path, default to:

- `data/profiles/sample-software-engineer-profile.md`

### 3. Run the discovery pipeline

Run these scripts in order from the skill root using the dedicated runtime:

```bash
~/.openclaw-skill-venv/bin/python scripts/prepare_search_run.py
~/.openclaw-skill-venv/bin/python scripts/search_backend_jobspy.py
~/.openclaw-skill-venv/bin/python scripts/normalize_jobs.py
~/.openclaw-skill-venv/bin/python scripts/render_search_summary.py
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
- If the live backend fails, surface the failure clearly
- Do not fabricate fallback data
- Use the skill’s normalized schema rather than backend-native field names

## Success condition

A successful run produces live backend output, normalized saved job records, and a readable summary inside the skill-local data directories.

## References

- `references/run-notes.md`
- `references/backend-notes.md`
- `references/notes.md`
