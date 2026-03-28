# job-search-bot

Personal project for building an **Automated Job Search Agent** with OpenClaw.

This repo is the real runtime home of the project.
The installed skill is an **agent-facing interface** into this project, not the runtime by itself.

---

## What this repo is

This project is for building a candidate-aware workflow that can:

- read a candidate profile
- infer seniority, employment intent, role direction, and domain fit from that profile
- build a focused search strategy
- run live job retrieval
- save the run in a way that is easy to inspect
- evaluate listings later with a single clear score system

Main principle:

> **profile interpretation and search reasoning belong to the skill**  
> **runtime execution and artifacts belong to the project**

---

## Environment variable: `JOB_SEARCH_BOT_ROOT`

The skill and scripts require an explicit project root.

```bash
export JOB_SEARCH_BOT_ROOT="$PWD"
```

---

## Python runtime

Use the project virtualenv:

```bash
uv sync
uv run pytest
```

---

## Repo structure

```text
job-search-bot/
├── config/
│   ├── runtime.json
│   └── search-defaults.json
├── runtime-data/
│   ├── profiles/
│   ├── search-runs/
│   │   └── <runId>/
│   │       ├── plan.json
│   │       ├── raw-results.json
│   │       ├── normalized-jobs.json
│   │       ├── rejected-jobs.json
│   │       ├── listings/
│   │       └── summary.md
│   ├── evaluations/
│   ├── final-results/
│   └── exports/
├── prompts/
├── scripts/
├── skills/
└── tests/
```

---

## Retrieval architecture

The retrieval flow should stay intentionally simple.

Each run folder under `runtime-data/search-runs/<runId>/` should contain:

- `search.json`
- `listings/*.json`
- `summary.md`

`search.json` is the important artifact.
It should make these decisions obvious:

- candidate understanding
- query list
- reason for each query
- filters per query
- reason for each filter

### Employment intent rule

Default to **full-time** unless the profile explicitly signals:

- internship
- contract / freelance

Internship experience in the background does **not** automatically mean the candidate wants internship roles.

### Scoring rule

The evaluation layer should use a **single 0-100 score system everywhere**.

---

## Config files

### `config/runtime.json`

Runtime/app-level paths only:

- `projectRoot`
- `pythonPath`
- `outputBase`
- `defaultProfile`
- `searchDefaultsPath`

### `config/search-defaults.json`

App/backend defaults only, such as:

- source selection
- result count
- freshness window
- backend toggles

It should **not** replace profile reasoning.

---

## Current retrieval workflow

From the project root:

```bash
export JOB_SEARCH_BOT_ROOT="$PWD"
.venv/bin/python skills/job-search-skill/scripts/prepare_search_run.py
.venv/bin/python skills/job-search-skill/scripts/search_backend_jobspy.py
.venv/bin/python skills/job-search-skill/scripts/normalize_jobs.py
.venv/bin/python skills/job-search-skill/scripts/render_search_summary.py
```

Optional export:

```bash
.venv/bin/python scripts/export_jobs_csv.py
```

---

## Skills in this repo

### `job-search-skill`

Owns retrieval only:

- candidate inference
- profile-driven query planning
- live retrieval
- normalization
- obvious mismatch rejection
- summary generation

### `job-listing-evaluation-skill`

Owns post-retrieval evaluation only:

- keep/drop decision
- single 0-100 score
- concise reasoning

---

## Current limitations

- live source noise still exists
- cleanup remains intentionally lightweight
- evaluation and final aggregation are still separate from retrieval artifacts
- export script name is legacy (`export_jobs_csv.py`) even though it writes Excel
