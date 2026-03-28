# job-search-bot

This repo is a native OpenClaw plugin. The repo now holds only plugin code, static assets, prompts, and skills.

## Final plugin structure

- `index.ts` — native plugin entry and deterministic workflow engine
- `openclaw.plugin.json` — plugin manifest and config schema
- `config/search-defaults.json` — repo-owned static retrieval defaults
- `config/runtime.json` — non-operational reference notes only
- `prompts/` — evaluator/orchestrator prompt templates
- `skills/` — thin agent-facing skills
- `assets/profiles/sample-software-engineer-profile.md` — optional example profile only

## Runtime artifact layout

Operational artifacts are written under the OpenClaw state dir, inside a plugin-owned folder:

- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/search-runs/<runId>/search.json`
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/search-runs/<runId>/listings/<listingId>.json`
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.error.json`
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/exports/<runId>.xlsx`
- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/exports/latest.xlsx`

The repo checkout is not used as writable runtime storage.

## Profile input model

`profilePath` is an explicit runtime input:

- required for `job_search_prepare_run`
- required for `job_search_spawn_evaluators`
- required for `job_search_full_run`
- persisted into each run's `search.json`
- validated before preparation/evaluation starts

The sample profile in `assets/profiles/` is just demo content. It is not an operational default.

## Plugin tools

- `job_search_prepare_run`
- `job_search_run_retrieval`
- `job_search_spawn_evaluators`
- `job_search_export_run`
- `job_search_full_run`

## Notes

- Retrieval uses JobSpy.
- Evaluator fanout uses concurrent subagent runs.
- Excel export is built from file-based evaluation artifacts, not stdout scraping.
- `job_search_run_retrieval` and `job_search_export_run` work from the state-backed run artifacts created earlier in the flow.
