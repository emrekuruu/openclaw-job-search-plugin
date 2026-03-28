You are running the job-search retrieval flow for the `job-search-bot` project.

Project root:
`/Users/emrekuru/Developer/job-search-bot`

Environment:
- `JOB_SEARCH_BOT_ROOT=/Users/emrekuru/Developer/job-search-bot`

Your job is to run the minimal retrieval model.

Step 1 — Read the candidate profile
Read the candidate profile from the runtime-configured default profile unless the caller provides another profile path.

Use `config/runtime.json` to resolve:
- `defaultProfile`
- `pythonPath`

Fail clearly if the profile cannot be read.

Step 2 — Decide the search as the agent
The agent owns the retrieval reasoning.

From the profile, determine:
- candidate understanding
- target role family
- seniority
- employment intent
- sensible locations / work-mode assumptions
- a small, focused query set
- filters for each query
- reasoning for each query and filter

Rules:
- default to full-time unless the profile explicitly asks for internship, contract, or freelance work
- keep the plan minimal and inspectable
- do not invent extra pipeline stages
- do not push search reasoning into helper scripts

Step 3 — Write `search.json`
Create a new run directory under:
- `runtime-data/search-runs/<runId>/`

Write:
- `runtime-data/search-runs/<runId>/search.json`

The file must include:
- `runId`
- `profilePath`
- `candidateUnderstanding`
- `queries`

Each query entry must include:
- `query`
- `reasoning`
- `filters`
- `filterReasoning`

Step 4 — Run JobSpy directly
From the project root, use the runtime-configured Python interpreter and run:
- `skills/job-search-skill/scripts/run_jobspy_search.py`

That script is the retrieval backend.
It reads the latest `search.json`, runs JobSpy directly, writes one JSON file per listing into `listings/`, and updates `search.json` with execution details.

Fail clearly if the script fails.

Step 5 — Validate the retrieval artifacts
Use the active run folder and verify that retrieval produced:
- `search.json`
- `listings/`

Optional:
- `summary.md`

Fail clearly if:
- the run folder is missing
- `search.json` is missing
- the per-listing directory is missing
- no listing files are present

Step 6 — Return a concise retrieval summary
Report:
- `runId`
- `profilePath`
- number of queries executed
- number of listing files written
- artifact paths
- any obvious retrieval issues

Operational rules
- Keep orchestration thin.
- The agent controls the plan.
- The project script performs retrieval.
- Retrieval outputs are only `search.json` plus `listings/*.json`, with optional `summary.md`.
- Do not assume old pipeline files such as `plan.json`, `normalized-jobs.json`, `raw-results.json`, `rejected-jobs.json`, or Excel exports.
- Do not invent fallback data.
- Do not silently skip failed steps.

Success condition
A successful run should produce:
- `runtime-data/search-runs/<runId>/search.json`
- one or more `runtime-data/search-runs/<runId>/listings/<listingId>.json`
- optional `runtime-data/search-runs/<runId>/summary.md`

If any critical step fails, surface the failure clearly.
