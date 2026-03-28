---
name: job-search-skill
description: Retrieval-only, candidate-aware job discovery for the job-search-bot project. Use when an agent must read a candidate profile, infer likely seniority and role family from that profile, build a focused search plan, execute live retrieval through the project runtime, and save normalized listings for later review. Reject obvious seniority, experience, and role-family mismatches during retrieval cleanup. Do not use for scoring, application help, resume tailoring, or interview preparation. Fail clearly if the profile, runtime, or live backend is unavailable; never use silent fallbacks.
---

# Job Search Skill

Run **discovery only**.

This skill owns:
- profile reading
- candidate seniority/role-family inference
- focused search planning
- live retrieval through the project runtime
- normalization plus obvious-mismatch rejection
- summary generation

This skill does **not** own:
- ranking beyond obvious retrieval cleanup
- application decisions
- resume or cover-letter work
- interview prep

## Enforce these rules

1. Resolve the project root from `JOB_SEARCH_BOT_ROOT`.
2. Read `<project-root>/config/runtime.json` and use its `pythonPath`.
3. Read the candidate profile before running anything.
4. Infer candidate seniority, role family, stack/domain signals, preferred companies, locations, and work mode from the profile itself.
5. Decide explicit retrieval filters from the profile, not just search text. Use structured filters such as site selection, remote/on-site intent, job type, distance, recency, and company targeting when the backend supports them.
6. Build a small, explicit search plan before retrieval.
7. Reject obvious mismatches during cleanup, especially:
   - `senior`, `sr`, `lead`, `staff`, `principal`, `manager`, `head`, `director`
   - experience requirements clearly above the candidate profile
   - role families outside the candidate target
8. Fail clearly when inference, runtime resolution, or the live backend is missing or broken.
9. Never fabricate fallback data.

## Use the workflow

```bash
<pythonPath> skills/job-search-skill/scripts/prepare_search_run.py
<pythonPath> skills/job-search-skill/scripts/search_backend_jobspy.py
<pythonPath> skills/job-search-skill/scripts/normalize_jobs.py
<pythonPath> skills/job-search-skill/scripts/render_search_summary.py
```

## Keep the search plan tight

- Prefer precision over recall.
- Use only a small number of high-signal queries.
- Search preferred companies directly when present.
- Include junior/entry variants only when the profile supports them.
- Do not widen into broad senior or adjacent-role searches just to increase count.

## Load references as needed

- Read `references/search-plan-schema.md` before changing planning behavior or inspecting plan structure.
- Read `references/retrieval-rules.md` when deciding what must be filtered or surfaced as a hard failure.
- Read `references/run-notes.md` for project-runtime expectations.
- Read `references/backend-notes.md` only if backend behavior matters.
