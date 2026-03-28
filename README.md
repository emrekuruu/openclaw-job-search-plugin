# job-search-bot

This repo is now a native OpenClaw plugin for concurrent job-search runs.

## Architecture

### Plugin owns
- run creation
- state-dir artifact layout
- evaluator fanout
- export / aggregation

### Job-search skill owns
- JobSpy retrieval execution via a Python worker script
- retrieval-specific guidance for the agent

This split keeps the plugin as the deterministic engine while leaving the Python-native JobSpy integration in the skill where it fits naturally.

## Runtime artifacts

The plugin writes runtime artifacts under the OpenClaw state dir:

- `plugin-runtimes/job-search/search-runs/<runId>/search.json`
- `plugin-runtimes/job-search/search-runs/<runId>/listings/<listingId>.json`
- `plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`
- `plugin-runtimes/job-search/evaluations/<runId>/<listingId>.error.json`
- `plugin-runtimes/job-search/exports/<runId>.xlsx`
- `plugin-runtimes/job-search/exports/latest.xlsx`

## Profile input

The candidate profile is a run input.

Real runs must provide `profilePath` explicitly.
The sample profile under `assets/profiles/` is example/demo content only.

## Plugin surfaces

The plugin registers these tools:
- `job_search_prepare_run`
- `job_search_run_retrieval`
- `job_search_spawn_evaluators`
- `job_search_export_run`
- `job_search_full_run`
