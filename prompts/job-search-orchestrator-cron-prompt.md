You are running the job-search orchestration flow for the `job-search-bot` project.

Project root:
`/Users/emrekuru/Developer/job-search-bot`

Environment:
- `JOB_SEARCH_BOT_ROOT=/Users/emrekuru/Developer/job-search-bot`

Your job is to orchestrate the pipeline exactly in this order.

Step 1 — Run retrieval only
Use the repo-owned retrieval flow from `job-search-skill`.

From the project root, use the runtime-configured Python interpreter and run:
- `skills/job-search-skill/scripts/prepare_search_run.py`
- `skills/job-search-skill/scripts/search_backend_jobspy.py`
- `skills/job-search-skill/scripts/normalize_jobs.py`
- `skills/job-search-skill/scripts/render_search_summary.py`

Fail clearly if any script fails.

Step 2 — Resolve the current run
Read the latest run directory from:
- `runtime-data/search-runs/<runId>/`

Use the latest run folder as the active run and derive:
- `runId`
- `plan.json`
- `normalized-jobs.json`
- `listings/`

From `plan.json`, extract:
- `profilePath`
- `candidateModel`
- `artifacts.listingsDir` if present

If `artifacts.listingsDir` is not present, assume:
- `runtime-data/search-runs/<runId>/listings/`

Fail clearly if:
- the run folder is missing
- `plan.json` is missing
- `normalized-jobs.json` is missing
- `profilePath` is missing
- the per-listing directory is missing
- no listing files are present

Step 3 — Use one listing file per sub-agent
Each listing should already exist as its own JSON file under:
- `runtime-data/search-runs/<runId>/listings/<listingId>.json`

Spawn exactly one sub-agent per listing file.

Do not batch multiple listings into one sub-agent.

Each sub-agent should receive:
- `profilePath`
- `listingPath`
- `runId` (optional)

The sub-agent must evaluate exactly one listing using the `job-listing-evaluation-skill`.

Step 4 — Per-listing evaluator contract
Each listing-evaluation sub-agent must:
1. read the candidate profile from `profilePath`
2. read the listing JSON from `listingPath`
3. evaluate the listing against the profile using the `job-listing-evaluation-skill`
4. return JSON only

Minimum required JSON shape:
{
  "listingId": "string",
  "decision": "keep",
  "score": 84,
  "reasoning": "Strong junior backend fit with relevant Java/Spring experience; slight stretch on years requirement."
}

Optional fields:
- `dimensions` (0-100 only)
- `flags`

Rules:
- one listing only
- single 0-100 score system only
- no markdown
- no prose outside JSON
- concise, specific reasoning
- fail clearly if profile or listing cannot be read

Step 5 — Collect evaluation results
Wait for all listing-evaluation sub-agents to finish.

Write one evaluation artifact per successful listing under:
- `runtime-data/evaluations/<runId>/<listingId>.json`

If some sub-agents fail:
- preserve successful evaluations
- record failures explicitly
- do not fabricate missing evaluations

Step 6 — Build final aggregate
Create:
- `runtime-data/final-results/<runId>.json`

This aggregate must include:
- `runId`
- `retrievedCount`
- `evaluatedCount`
- `keptCount`
- `droppedCount`
- `failures`
- `finalListings`

Rules for `finalListings`:
- include only listings with `decision = keep`
- sort by highest `score` first
- merge evaluation fields onto the listing records where useful

If evaluation failures occurred, include them under `failures`.

Step 7 — Create the Excel export
Run the existing export step:
- `scripts/export_jobs_csv.py`

That script prefers:
- `runtime-data/final-results/<runId>.json`

and falls back to the latest per-run `normalized-jobs.json` if no final-results artifact exists.

So ensure the final-results file is written before export when evaluation succeeds.

Success means an Excel file is created under:
- `runtime-data/exports/`

Operational rules
- Do not invent fallback data.
- Do not silently skip failed steps.
- Keep orchestration thin.
- Use the repo’s existing scripts and artifact structure.
- One sub-agent per listing file.
- Prefer clear artifacts over prompt stuffing.

Suggested limits
- maximum listings to evaluate per run: 15
- concurrency cap for listing evaluators: 5

If more than the limit are retrieved:
- evaluate only the first 15 listing files
- be explicit about the cap in the final summary

Success condition
A successful run should produce:
- normalized retrieval output
- per-listing JSON artifacts
- one evaluation result per successfully evaluated listing
- `runtime-data/final-results/<runId>.json`
- Excel export in `runtime-data/exports/`

If any critical step fails, surface the failure clearly.
