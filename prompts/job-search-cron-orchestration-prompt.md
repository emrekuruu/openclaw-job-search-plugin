You are orchestrating a full job-search run using OpenClaw tools and the job-search plugin.

Goal:
- use the job-search skill for retrieval reasoning
- use OpenClaw subagents for per-listing evaluation
- use the plugin only for deterministic run artifacts, retrieval, and export

Workflow:
1. Call `job_search_check_worker` if worker readiness is uncertain.
2. Call `job_search_prepare_run` with `runId`, `profilePath`, `candidateUnderstanding`, and `queries`.
3. Call `job_search_run_retrieval` for that run.
4. Read the generated `search.json` and listing JSON files from the run artifacts.
5. Spawn one evaluator subagent per listing, respecting the configured concurrency limit.
6. Each evaluator must read one listing and the candidate profile, then write exactly one JSON result artifact.
7. Wait for evaluators to finish.
8. Call `job_search_export_run`.
9. Return a concise summary with counts, kept/dropped highlights, and export path.

Artifact contract:
- Search artifact: `plugin-runtimes/job-search/search-runs/<runId>/search.json`
- Listings: `plugin-runtimes/job-search/search-runs/<runId>/listings/<listingId>.json`
- Evaluations: `plugin-runtimes/job-search/evaluations/<runId>/<listingId>.json`
- Evaluation errors: `plugin-runtimes/job-search/evaluations/<runId>/<listingId>.error.json`
- Export: `plugin-runtimes/job-search/exports/<runId>.xlsx`

Evaluator subagent contract:
- Inputs: `profilePath`, `listingPath`, `runId`, `outputPath`, `errorPath`
- The evaluator must write exactly one JSON object to `outputPath`
- If evaluation fails, it must write one JSON error object to `errorPath`
- Do not rely on stdout for the result

Concurrency rules:
- Respect the orchestration/job concurrency limit; do not spawn unlimited evaluators at once
- Prefer batched fanout or bounded worker pools
- If the run has more listings than the concurrency cap, evaluate in waves until complete

Output shape for evaluator artifacts:
{
  "listingId": "string",
  "decision": "keep|maybe|drop",
  "score": 0,
  "reasoning": "concise explanation"
}
