# job-search-bot

This repo is now a native OpenClaw plugin for concurrent job-search runs.

## Architecture

### Plugin owns
- run creation
- state-dir artifact layout
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
- `job_search_check_worker`
- `job_search_prepare_run`
- `job_search_run_retrieval`
- `job_search_export_run`

`job_search_run_retrieval` can target a specific prepared `runId`; if omitted, it falls back to the latest prepared run.

Evaluator orchestration is intentionally not owned by the plugin anymore.
OpenClaw agents/subagents should read the prepared artifacts, write evaluation JSON files into `plugin-runtimes/job-search/evaluations/<runId>/`, and then call `job_search_export_run`.

## Python worker setup

OpenClaw installs plugin JS dependencies with `npm install --ignore-scripts`; there is no plugin-era Python dependency provisioning hook here. So the Python worker setup has to be explicit.

Recommended setup from the plugin repo or installed plugin directory:

```bash
uv sync
```

That creates/updates `.venv` from `pyproject.toml`. The plugin now prefers this interpreter automatically:

- uses `JOB_SEARCH_PYTHON` if you set it
- otherwise uses `.venv/bin/python3` when present
- otherwise falls back to `python3`

## Runtime readiness behavior

Before retrieval runs, the plugin now verifies that:
- the JobSpy worker script exists in the installed plugin copy
- the selected Python interpreter is callable
- `python-jobspy`, `pandas`, `pydantic`, and `openpyxl` import successfully

If readiness fails, the tool returns an actionable error telling you to run:

```bash
cd /path/to/job-search-plugin
uv sync
```

You can also probe readiness directly with `job_search_check_worker` before starting a run.
