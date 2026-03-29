# Job Search

Native OpenClaw plugin for state-backed job-search runs:

- prepares a run and artifact layout under the OpenClaw state dir
- executes JobSpy retrieval through a bundled Python worker
- lets OpenClaw orchestrate concurrent per-listing evaluation subagents
- exports evaluated results to Excel

This plugin owns the deterministic workflow pieces. Search reasoning and evaluator judgment stay in the bundled skills/prompts.

## What it does

The plugin registers four tools:

- `job_search_check_worker`
- `job_search_prepare_run`
- `job_search_run_retrieval`
- `job_search_export_run`

High-level flow:

1. verify worker readiness
2. read a candidate profile
3. prepare a run with normalized query inputs
4. run retrieval
5. evaluate listings in parallel with OpenClaw child sessions/subagents
6. export the scored results to `.xlsx`

## Artifact layout

Runtime artifacts are written under the OpenClaw state dir, not the repo checkout:

- `plugin-runtimes/job-search/search-runs/<runId>/search.json`
- `plugin-runtimes/job-search/search-runs/<runId>/listings/<listingId>.json`
- `plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`
- `plugin-runtimes/job-search/evaluations/<runId>/<listingId>.error.json`
- `plugin-runtimes/job-search/exports/<runId>.xlsx`
- `plugin-runtimes/job-search/exports/latest.xlsx`

## Install

Published package:

```bash
openclaw plugins install @emrekuruu/job-search
openclaw plugins enable job-search
```

Inspect after install:

```bash
openclaw plugins inspect job-search --json
openclaw plugins doctor
```

## Python worker setup

OpenClaw installs plugin JavaScript dependencies, but the JobSpy worker still needs a Python environment.

After plugin install, create the Python environment from the plugin directory:

```bash
uv sync
```

The worker interpreter selection is:

1. `JOB_SEARCH_PYTHON` if set
2. `.venv/bin/python3` if present
3. `python3`

The readiness check imports the required Python packages before retrieval:

- `python-jobspy`
- `pandas`
- `pydantic`
- `openpyxl`

Quick readiness probe:

```text
job_search_check_worker
```

If readiness fails, the plugin returns setup guidance instead of a vague runtime crash.

## Candidate profile input

Every real run must provide `profilePath` explicitly.

The sample profile in `assets/profiles/sample-software-engineer-profile.md` is example/demo content only.

## Query contract

`job_search_prepare_run` expects normalized query objects. Canonical shape:

```json
{
  "query": "Junior Backend Engineer",
  "reasoning": "Direct match for early-career backend roles in Istanbul.",
  "filters": {
    "location": "Istanbul, Turkey",
    "site_name": ["linkedin"],
    "results_wanted": 15,
    "hours_old": 720,
    "job_type": "fulltime",
    "is_remote": false,
    "easy_apply": false,
    "linkedin_fetch_description": true,
    "country_indeed": "turkey",
    "distance": 50
  },
  "filterReasoning": {
    "location": "Prefer Istanbul-based roles.",
    "job_type": "Default to full-time unless the profile explicitly requests otherwise.",
    "hours_old": "Prefer roles from the last 30 days.",
    "country_indeed": "Candidate is authorized in Turkey and targeting Turkey-based opportunities."
  }
}
```

Important normalization rules:

- `q` -> `query`
- `site` -> `filters.site_name` as an array
- `employmentType: "full-time"` -> `filters.job_type: "fulltime"`
- top-level `location` -> `filters.location`

Default search policy in this repo:

- default to `fulltime` unless internship/contract is explicitly requested
- broad retrieval is okay; evaluator agents do the real filtering

## Full workflow

The plugin does **not** own evaluator orchestration.

Recommended full workflow:

1. call `job_search_check_worker` if setup is uncertain
2. read the profile and bundled job-search skill guidance
3. call `job_search_prepare_run`
4. call `job_search_run_retrieval`
5. read `search.json` and listing JSON files from the run artifacts
6. spawn evaluator child sessions in parallel, one listing per child
7. ensure each evaluator writes exactly one JSON artifact
8. call `job_search_export_run`
9. return summary + export path

Reference orchestration prompt:

- `prompts/job-search-cron-orchestration-prompt.md`

## Evaluator artifact contract

Each evaluator must write exactly one JSON file to:

- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`

Optional failure artifact:

- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/evaluations/<runId>/<listingId>.error.json`

Canonical evaluation shape:

```json
{
  "listingId": "string",
  "decision": "keep|maybe|drop",
  "score": 78,
  "reasoning": "Concise explanation.",
  "dimensions": {
    "roleFit": 85,
    "seniorityFit": 90,
    "locationFit": 70,
    "domainFit": 80,
    "skillsFit": 65
  }
}
```

Rules:

- `dimensions` are required
- dimension scores must be normalized to `0-100`
- final `score` must be normalized to `0-100`
- `decision` must be exactly `keep`, `maybe`, or `drop`
- evaluators must not rely on stdout as the final artifact

## Tool details

### `job_search_prepare_run`

Creates a run and seeds `search.json`.

Inputs:

- `runId` (optional)
- `profilePath` (required)
- `candidateUnderstanding` (optional)
- `queries` (optional)

Returns:

- `runId`
- `searchPath`
- `listingsDir`

### `job_search_check_worker`

Verifies that the installed plugin copy can reach the Python worker and import the required packages.

### `job_search_run_retrieval`

Runs JobSpy retrieval for the specified run.

Inputs:

- `runId` (optional; falls back to latest prepared run)

Returns:

- `searchPath`
- `listingsDir`
- `listingCount`

### `job_search_export_run`

Builds an Excel workbook from the evaluation artifacts.

Inputs:

- `runId` (required)

Returns:

- `outputPath`

## Local development

Link the repo into OpenClaw for dev:

```bash
openclaw plugins install -l .
openclaw plugins inspect job-search --json
openclaw plugins doctor
```

If you already linked an older copy, remove or replace that install first.

Package sanity check:

```bash
npm pack --dry-run
```

## Publishing

Publish to npm from the plugin root:

```bash
npm publish --access public
```

Users can then install it with:

```bash
openclaw plugins install @emrekuruu/job-search
```

## Repo structure

- `index.ts` - plugin entry and tool registration
- `openclaw.plugin.json` - plugin manifest
- `skills/job-search-skill/` - retrieval guidance + JobSpy worker
- `skills/job-listing-evaluation-skill/` - evaluator guidance
- `prompts/` - orchestration prompts
- `config/search-defaults.json` - retrieval defaults
- `assets/profiles/` - example profile inputs

## Current sanity-check status

Checked locally:

- npm package tarball builds cleanly via `npm pack --dry-run`
- plugin manifest/tool discovery works via `openclaw plugins inspect job-search --json`
- `openclaw plugins doctor` reports no plugin issues

Not bundled into the repo/package:

- `node_modules/`
- `.venv/`

That is intentional. JavaScript dependencies come from npm, and the Python worker environment should be created locally with `uv sync`.
