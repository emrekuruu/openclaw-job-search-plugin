# Run Notes

## Current execution model

This skill now orchestrates the **project runtime** instead of trying to behave like a fully self-contained mini-application.

The project owns:

- Python runtime
- config
- output directories
- real runtime data

The skill owns:

- workflow guidance
- the invocation pattern
- the agent-facing instructions

## Project runtime files

Expected project runtime files:

- `config/runtime.json`
- `config/search-defaults.json`
- `runtime-data/profiles/`
- `runtime-data/search-runs/`
- `runtime-data/raw/`
- `runtime-data/jobs/`

## Script entrypoints

The skill uses these project scripts:

1. `skills/job-search-skill/scripts/prepare_search_run.py`
2. `skills/job-search-skill/scripts/search_backend_jobspy.py`
3. `skills/job-search-skill/scripts/normalize_jobs.py`
4. `skills/job-search-skill/scripts/render_search_summary.py`

## Runtime rule

Use the Python interpreter defined in `config/runtime.json`.
Do not rely on whichever `python` happens to be on PATH.

## Current limitations

Known current limitations:

- source noise and regional failures may occur
- ZipRecruiter may fail in EU contexts
- deduplication is not yet strong
- work mode normalization still needs improvement
