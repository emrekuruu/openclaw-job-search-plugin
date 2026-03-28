# job-search-bot

Personal project for building an **Automated Job Search Agent** with OpenClaw.

This repo is the real runtime home of the project.
The ClawHub/OpenClaw skill is an **agent-facing interface** into this project, not the entire runtime by itself.

---

## What this repo is

This project is for building a candidate-aware job search workflow that can:

- read a candidate profile
- interpret the candidate's seniority, role direction, and domain fit
- build a focused search strategy
- run live job retrieval
- save and present discovered jobs cleanly

The main principle is:

> **profile interpretation and search reasoning belong to the skill**
> **runtime execution belongs to the project**

This means the repo owns:

- the Python runtime
- config
- runtime data directories and conventions
- scripts
- tests

Generated search outputs and exports live under `runtime-data/`, but they are runtime artifacts rather than source-of-truth files for git.

And the skill owns:

- how an agent should interpret the profile
- how an agent should shape the search
- how an agent should use this project

---

## Core architecture

### Project-centric runtime

This project uses a **project-centric** architecture.

That means the actual runtime is this repo, not the installed skill folder in the OpenClaw workspace.

The installed skill is meant to operate **against this repo**.

### Why

This project is more than a tiny standalone skill.
It is becoming a real multi-step application with:

- candidate profiles
- runtime data
- search history
- exports
- future additional skills

So the repo is the stable home.

---

## Environment variable: `JOB_SEARCH_BOT_ROOT`

The skill and scripts now require an explicit project root.

They resolve the project through:

- `JOB_SEARCH_BOT_ROOT`

### Easiest way when already inside the repo

```bash
export JOB_SEARCH_BOT_ROOT="$PWD"
```

### Verify it

```bash
echo $JOB_SEARCH_BOT_ROOT
```

### Why this exists

This avoids hardcoding machine-specific absolute paths and makes the skill work against the real project root explicitly.

---

## Python runtime

The intended runtime is the project `.venv`.

Current expected path:

- `.venv/bin/python`

### Install/sync dependencies

```bash
uv sync
```

### Run tests

```bash
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
│   ├── search-plans/
│   ├── search-runs/      # generated
│   ├── raw/              # generated
│   ├── jobs/             # generated
│   └── exports/          # generated
├── prompts/
├── skills/
│   ├── job-search-skill/
│   └── job-listing-evaluation-skill/
├── scripts/
│   └── export_jobs_csv.py
├── tests/
│   └── job-search-skill/
├── pyproject.toml
├── uv.lock
└── README.md
```

---

## Config files

### `config/runtime.json`

This is the main project runtime config.

It should stay focused on **runtime/app-level paths**, not candidate reasoning.

Current fields:

- `projectRoot`
- `pythonPath`
- `outputBase`
- `defaultProfile`
- `searchDefaultsPath`

These are resolved relative to `JOB_SEARCH_BOT_ROOT` when not absolute.

### `config/search-defaults.json`

This should only contain **app/backend defaults**, such as:

- source selection
- result count
- freshness window
- backend toggles

It should **not** contain intelligence knobs that try to replace profile reasoning.

Candidate-specific filtering and prioritization should come from:

- the candidate profile
- the skill's reasoning
- the search plan

---

## runtime-data/

This is where runtime inputs and generated artifacts are stored.

### Tracked inputs/docs

- `runtime-data/profiles/` — candidate profiles used for search
- `runtime-data/search-plans/README.md` — folder-level note for generated plans

### Generated artifacts

These are intentionally treated as runtime output, not long-lived source files:

- `runtime-data/search-plans/*.json` — generated search plans
- `runtime-data/search-runs/` — human-readable and structured run records
- `runtime-data/raw/` — raw backend output from live retrieval
- `runtime-data/jobs/` — normalized jobs after cleanup/dedup
- `runtime-data/job-listings/` — per-listing normalized JSON files
- `runtime-data/evaluations/` — listing evaluation outputs
- `runtime-data/final-results/` — final aggregated results
- `runtime-data/exports/` — user-facing Excel exports

---

## Skills

This repo can contain multiple skills over time.

Each skill lives under:

- `skills/<skill-name>/`

The repo is the product.
Each skill is an agent-facing capability module.

### Installing / downloading skills

If a skill has been published to ClawHub, install it with OpenClaw:

```bash
openclaw skills install <skill-slug>
```

Example:

```bash
openclaw skills install job-search-skill
```

To inspect installed skills:

```bash
openclaw skills list
```

To view a skill:

```bash
openclaw skills info <skill-slug>
```

Example:

```bash
openclaw skills info job-search-skill
```

### Publishing a skill

Publishing uses the `clawhub` CLI, not `openclaw`.

Example:

```bash
clawhub publish **skill** --slug **skill** --name "Name of Skill" --version 0.1.0 --tags latest
```

---

## Current skill: `job-search-skill`

### What it is

`job-search-skill` is the first skill in this repo.

It is responsible for:

- interpreting a candidate profile
- inferring seniority and role direction
- understanding domain relevance and preferred companies
- building a focused search strategy
- executing live retrieval through the project runtime
- saving outputs in the project runtime-data folders

### What it is **not**

It is not:

- a standalone mini app
- the runtime itself
- a resume tailoring skill
- an application automation skill
- an interview prep skill

### Design philosophy

This skill is:

- **candidate-aware**
- **search-plan-first**
- **precision-oriented**
- **project-centric**

It should prefer:

- fewer better queries
- fewer better matches
- target-company searches when appropriate
- junior-aware search behavior when the profile calls for it

It should avoid:

- broad noisy retrieval
- fake fallback paths
- overreliance on post-search scoring
- making the user configure advanced search logic manually

### Execution chain

The intended chain is:

1. read candidate profile
2. infer candidate model
3. build search plan
4. execute plan through backend
5. normalize results
6. render summary
7. optionally export for review

### Scripts used by the skill

The skill currently uses these scripts:

- `skills/job-search-skill/scripts/prepare_search_run.py`
- `skills/job-search-skill/scripts/search_backend_jobspy.py`
- `skills/job-search-skill/scripts/normalize_jobs.py`
- `skills/job-search-skill/scripts/render_search_summary.py`

### References used by the skill

- `skills/job-search-skill/references/run-notes.md`
- `skills/job-search-skill/references/backend-notes.md`
- `skills/job-search-skill/references/retrieval-rules.md`
- `skills/job-search-skill/references/search-plan-schema.md`

---

## Search plan model

A major design decision in this project is that:

> the system should not rely on broad retrieval + scoring hacks

Instead, the preferred workflow is:

- profile interpretation
- reasoning
- search plan generation
- exact query execution

The search-plan schema now lives under:

- `skills/job-search-skill/references/search-plan-schema.md`

And runtime search plans are saved under:

- `runtime-data/search-plans/`

---

## How to run the current workflow manually

From the project root:

```bash
export JOB_SEARCH_BOT_ROOT="$PWD"
```

Then run:

```bash
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

## Current retrieval behavior

Current backend setup is intentionally simple:

- live retrieval
- no fake fallback
- LinkedIn-only (current preferred source)
- project `.venv` runtime

If the runtime or dependency setup is broken, the system should fail clearly.

---

## Current known limitations

This project is improving, but not finished.

Current limitations include:

- search-plan execution is still early and can be tightened further
- some senior/noisy roles still leak through
- company-targeted search still needs refinement
- post-search cleanup is intentionally light
- dedup exists but can be improved
- export script is still named `export_jobs_csv.py` even though it now writes Excel output

---

## Personal usage notes

This repo is being optimized first for **personal use and iteration**, not for pretending to be a polished universal skill platform.

That means:

- project runtime matters more than skill self-containment
- profile-driven search quality matters more than flashy dashboards
- fewer better matches are preferred over lots of mediocre results
- no fallback behavior

---

## Working rule of thumb

### Config should answer:
- where is the project?
- where is the runtime?
- where do outputs go?
- what backend defaults are used?

### The profile + skill should answer:
- what kind of candidate is this?
- what kind of roles should be searched?
- what should be prioritized?
- what should be avoided?
- what exact searches should be run?

That split is the core design of this repo.
