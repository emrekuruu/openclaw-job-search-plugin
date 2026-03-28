# job-search-bot

Personal project for building an automated job search agent with OpenClaw.

This repo is the real runtime home of the project.
The installed skills are just agent-facing interfaces into this project.

---

## What this repo is

This project is for a candidate-aware workflow that can:

- read a candidate profile
- infer seniority, employment intent, role direction, and domain fit from that profile
- let the agent decide a focused search strategy
- run live retrieval directly through JobSpy
- save a small, inspectable retrieval artifact set
- evaluate listings later with a single 0-100 score system

Main principle:

> **the agent owns candidate understanding and search decisions**  
> **the project owns execution and saved artifacts**

---

## Environment variable: `JOB_SEARCH_BOT_ROOT`

The skills and scripts require an explicit project root.

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
├── prompts/
├── assets/
│   └── profiles/
│       └── sample-software-engineer-profile.md
├── runtime-data/
│   ├── search-runs/
│   │   └── <runId>/
│   │       ├── search.json
│   │       ├── listings/
│   │       │   └── <listingId>.json
│   │       └── summary.md   # optional
│   ├── evaluations/
│   │   └── <runId>/
│   │       ├── <listingId>.json
│   │       └── <listingId>.error.json   # optional
│   └── exports/
│       └── <runId>.xlsx
├── scripts/
│   └── export_jobs.py
├── skills/
│   ├── job-search-skill/
│   └── job-listing-evaluation-skill/
└── tests/
```

---

## Retrieval architecture

The retrieval flow should stay intentionally simple.

Each run folder under `runtime-data/search-runs/<runId>/` should contain:

- `search.json`
- `listings/*.json`
- optional `summary.md`

`search.json` is the main retrieval artifact.
It should make these decisions obvious:

- candidate understanding
- query list
- reason for each query
- filters per query
- reason for each filter

### Employment intent rule

The default profile path now lives in `assets/profiles/` so it is stable repo content rather than runtime output.

Default to **full-time** unless the profile explicitly signals:

- internship
- contract
- freelance

Internship experience in the background does **not** automatically mean the candidate wants internship roles.

### Scoring rule

The evaluation layer should use a **single 0-100 score system everywhere**.

---

## Evaluation architecture

Evaluation is intentionally file-based so every listing can be processed independently and safely in parallel.

For a given run:

- source listings live in `runtime-data/search-runs/<runId>/listings/`
- evaluator outputs live in `runtime-data/evaluations/<runId>/`
- each evaluator writes exactly one file: `runtime-data/evaluations/<runId>/<listingId>.json`
- optional failures can be written as `runtime-data/evaluations/<runId>/<listingId>.error.json`

The evaluator contract is:

1. the caller assigns one listing and one explicit `outputPath`
2. the evaluator reads the profile and listing
3. the evaluator writes the JSON artifact directly to `outputPath`
4. aggregation reads files from disk later

That means final aggregation does **not** depend on stdout capture or serialized in-memory collection.

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

Only default JobSpy request values, such as:

- source selection
- result count
- freshness window
- distance
- job type

It should **not** replace profile reasoning.
The agent still decides the search.

---

## Current retrieval workflow

From the project root:

```bash
export JOB_SEARCH_BOT_ROOT="$PWD"
.venv/bin/python skills/job-search-skill/scripts/run_jobspy_search.py
```

Expected flow:

1. the agent reads the stable repo-owned profile from `assets/profiles/` (or another explicit profile path)
2. the agent writes `runtime-data/search-runs/<runId>/search.json`
3. the script reads the latest `search.json`
4. the script runs JobSpy directly
5. the script writes one JSON file per listing into `listings/` using deterministic collision-safe IDs
6. the script updates `search.json` with execution details

---

## Evaluation + export workflow

Evaluators should be launched concurrently, one listing per evaluator.

Each evaluator should receive:

- `profilePath`
- `listingPath`
- `runId`
- `outputPath=runtime-data/evaluations/<runId>/<listingId>.json`

After evaluators finish, export the run to Excel with:

```bash
export JOB_SEARCH_BOT_ROOT="$PWD"
.venv/bin/python scripts/export_jobs.py --run-id <runId>
```

Behavior:

1. read all `runtime-data/evaluations/<runId>/*.json` files except `*.error.json`
2. enrich rows from `runtime-data/search-runs/<runId>/listings/*.json`
3. sort rows by score descending
4. write `runtime-data/exports/<runId>.xlsx`
5. also refresh `runtime-data/exports/latest.xlsx`

If `--run-id` is omitted, the exporter uses the latest run under `runtime-data/evaluations/`.

---

## Skills in this repo

### `job-search-skill`

Owns retrieval only:

- candidate inference
- profile-driven query planning
- writing `search.json`
- direct JobSpy retrieval
- one-file-per-listing outputs
- optional retrieval summary

### `job-listing-evaluation-skill`

Owns post-retrieval evaluation only:

- evaluate one collected listing against a candidate profile
- decide `keep` or `drop`
- assign a single 0-100 score
- write one JSON evaluation artifact per listing
- return concise reasoning

---

## Current limitations

- live source noise still exists
- cleanup remains intentionally lightweight
- summary generation is optional
- evaluation orchestration is external to this repo; this repo defines the file contract and export script
- `.error.json` files are intentionally excluded from the Excel export
