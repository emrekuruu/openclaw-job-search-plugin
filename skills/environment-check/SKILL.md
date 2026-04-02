---
name: environment-check
description: Check whether the local environment is ready for the job-search workflow. Use when preparing or debugging the job-search stack, especially to verify Python, uv/.venv, JobSpy dependencies, Node dependencies, Puppeteer availability, and resume theme availability before retrieval or rendering.
---

# Environment Check Skill

Use this skill to verify that the repo and runtime are ready before running job-search retrieval or resume rendering workflows.

## Responsibilities

- verify Python availability
- verify the retrieval script exists
- verify JobSpy-related imports work in the intended interpreter
- verify Node dependencies are installed
- verify Puppeteer is available for PDF generation
- verify the default or requested JSON Resume theme can be resolved
- return actionable setup guidance instead of vague failures

## Script

Run:

- `scripts/check_job_search_environment.py`

The script prints a JSON report with:
- `ok`
- `python`
- `node`
- `retrieval`
- `rendering`
- `issues`
- `suggestedFixes`

## Expected usage

Use this before:
- first-time setup
- debugging retrieval failures
- debugging resume rendering failures
- validating the repo after dependency changes

## Notes

- prefer repo-local `.venv/bin/python3` when present
- otherwise fall back to `JOB_SEARCH_PYTHON`, then `python3`
- if the report is not `ok`, summarize the issues clearly and suggest the exact next setup step
