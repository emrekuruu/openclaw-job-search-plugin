# job-search-bot

This repo is now a native OpenClaw plugin for concurrent job-search runs.

## What the plugin owns

Deterministic workflow ownership lives in plugin code:
- run creation
- JobSpy retrieval execution
- listing artifact writing
- concurrent evaluator fanout
- Excel export from evaluation artifacts

## Runtime artifacts

The plugin writes runtime artifacts under `runtime-data/`:

- `search-runs/<runId>/search.json`
- `search-runs/<runId>/listings/<listingId>.json`
- `evaluations/<runId>/<listingId>.json`
- `evaluations/<runId>/<listingId>.error.json` (optional)
- `exports/<runId>.xlsx`
- `exports/latest.xlsx`

## Stable inputs

Tracked repo-owned inputs should live outside runtime-data.

Current example profile:
- `assets/profiles/sample-software-engineer-profile.md`

## Plugin surfaces

The plugin registers these tools:
- `job_search_prepare_run`
- `job_search_run_retrieval`
- `job_search_spawn_evaluators`
- `job_search_export_run`
- `job_search_full_run`

## Notes

- Retrieval uses JobSpy.
- Evaluator fanout is designed for concurrent subagent runs.
- Excel export is built from file-based evaluation artifacts, not stdout scraping.
