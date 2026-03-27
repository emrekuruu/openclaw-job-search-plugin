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

## Project runtime files

Expected project runtime files:

- `config/runtime.json`
- `config/search-defaults.json`
- `runtime-data/profiles/`
- `runtime-data/search-runs/`
- `runtime-data/raw/`
- `runtime-data/jobs/`

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

Use the Python interpreter defined in `config/runtime.json`.
Do not rely on whichever `python` happens to be on PATH.

## Current limitations

Known current limitations:

- source noise and regional failures may occur
- deduplication and cleanup are still lightweight
- profile-aware search planning still needs to become more explicit in execution, not just in the skill instructions
