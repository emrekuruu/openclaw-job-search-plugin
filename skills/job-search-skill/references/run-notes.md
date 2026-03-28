# Run Notes

## Current execution model

This skill orchestrates the **project runtime** instead of trying to behave like a fully self-contained mini-application.

The project owns:

- Python runtime
- config
- output directories
- real runtime data
- optional export utilities

The skill owns:

- workflow guidance
- the invocation pattern
- the agent-facing instructions
- candidate interpretation and search planning

## Project root rule

The skill must resolve the project through:

- `JOB_SEARCH_BOT_ROOT`

If that environment variable is missing or invalid, the skill should fail clearly.

## Project runtime files

Expected project runtime files under the resolved project root:

- `config/runtime.json`
- `config/search-defaults.json`
- `runtime-data/profiles/`
- `runtime-data/search-runs/`
- `runtime-data/final-results/`
- `runtime-data/exports/`

## Per-run artifact layout

Each retrieval run should now live under:

- `runtime-data/search-runs/<runId>/`

Expected artifacts inside that folder:

- `plan.json` — candidate inference, retrieval filters, query plan, artifact paths
- `raw-results.json` — backend requests and raw results grouped by query
- `normalized-jobs.json` — deduplicated kept listings
- `rejected-jobs.json` — obvious mismatches rejected during retrieval cleanup
- `listings/` — one normalized JSON file per kept listing
- `summary.md` — human-readable run summary

This structure is meant to make it obvious why the run searched what it searched and what happened to each result.

## Runtime config rule

`config/search-defaults.json` should only hold app-level/backend defaults.
It should not become a substitute for candidate reasoning.

Candidate-specific filtering and prioritization should come from the profile and from the skill’s reasoning, not from static filter knobs in config.

## Script entrypoints

The skill uses these project scripts:

1. `skills/job-search-skill/scripts/prepare_search_run.py`
2. `skills/job-search-skill/scripts/search_backend_jobspy.py`
3. `skills/job-search-skill/scripts/normalize_jobs.py`
4. `skills/job-search-skill/scripts/render_search_summary.py`

## Runtime rule

Use the Python interpreter defined in `<JOB_SEARCH_BOT_ROOT>/config/runtime.json`.
Do not rely on whichever `python` happens to be on PATH.

## Current limitations

Known current limitations:

- source noise and regional failures may occur
- deduplication and cleanup are still lightweight
- evaluation/final-results remain separate from retrieval runs for now
