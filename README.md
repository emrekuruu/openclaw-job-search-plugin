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
│   └── search-runs/
│       └── <runId>/
│           ├── search.json
│           ├── listings/
│           │   └── <listingId>.json
│           └── summary.md   # optional
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
- return concise reasoning

---

## Current limitations

- live source noise still exists
- cleanup remains intentionally lightweight
- summary generation is optional
- evaluation remains a separate post-retrieval step
- Excel export reads the latest `runtime-data/final-results/*.json` artifact and writes `runtime-data/exports/*.xlsx`
