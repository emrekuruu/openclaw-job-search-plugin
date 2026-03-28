You are running the job-search retrieval flow for the `job-search-bot` plugin.

Project root:
`/Users/emrekuru/Developer/job-search-bot`

Your job is to keep orchestration thin and let the plugin own deterministic workflow mechanics.

Step 1 — Read the candidate profile
Use the caller-provided `profilePath`.

Do not assume a built-in default profile from the repo.
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

Step 3 — Create a state-backed run through the plugin
Call `job_search_prepare_run` with:
- `profilePath`
- `candidateUnderstanding`
- `queries`
- optional `runId`

This creates the canonical state-backed run and writes `search.json` under the plugin runtime state dir.

Step 4 — Run retrieval through the plugin
Call `job_search_run_retrieval` for the created run.

The plugin owns retrieval execution, listing writes, and `search.json` updates.
Fail clearly if retrieval fails.

Step 5 — Validate retrieval artifacts
Use the returned run information and verify that retrieval produced:
- `search.json`
- `listings/`

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
- The plugin performs retrieval and artifact writing.
- Retrieval outputs are only `search.json` plus `listings/*.json`, with optional future summary artifacts if the plugin adds them.
- Do not invent fallback data.
- Do not silently skip failed steps.
