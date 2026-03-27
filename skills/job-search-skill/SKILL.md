---
name: job-search-skill
description: Run candidate-aware job discovery for the job-search-bot project. Use when an agent needs to read a candidate profile, interpret seniority and fit, build a targeted search strategy, execute live job retrieval through the project runtime, and save reviewed results for later user presentation. Do not use for applications, resume tailoring, or interview preparation. Fail clearly if the project runtime or live backend is unavailable.
---

# Job Search Skill

Use this skill to run **Step 1: candidate-aware discovery and collection** for the `job-search-bot` project.

This skill is **project-centric** and **reasoning-first**.
It should not behave like a dumb script launcher. The scripts exist to execute the plan. The skill is responsible for reading the candidate profile, deciding what matters, forming a search strategy, and then reviewing results against that strategy.

## Core rule

Do not jump straight from profile file to raw search execution.

Before running the backend, the agent must:

1. read the candidate profile carefully
2. infer the candidate model
3. decide how search should be shaped
4. decide what should be avoided
5. then execute the project workflow

## What this skill does

This skill:

- reads the project runtime configuration from `config/runtime.json`
- reads the configured profile path
- interprets the candidate profile before searching
- derives search strategy from candidate seniority, background, and preferences
- runs a live JobSpy-backed backend search through the project runtime
- saves raw backend results
- normalizes results into the project schema
- renders a human-readable run summary

This skill does **not** yet do:

- applications
- resume tailoring
- cover letters
- interview preparation

## Project runtime requirements

The project runtime configuration should exist at:

- `config/runtime.json`

That config should define at least:

- `projectRoot`
- `pythonPath`
- `outputBase`
- `defaultProfile`
- `searchDefaultsPath`

The Python runtime defined by `pythonPath` must have the required packages installed, including:

- `python-jobspy`
- `pandas`
- `pydantic`

If the runtime config, Python path, or live backend is unavailable, fail clearly.
Do not silently produce fallback data.

## Candidate interpretation (mandatory)

Before searching, extract and reason about:

- likely seniority
- target role family
- current experience level
- prior domain background
- industries or domains to favor
- preferred companies
- location constraints
- work mode constraints
- roles or seniority levels to avoid

### Example reasoning expectations

If the profile is for a recently graduated engineer with 1 year of experience, the search strategy should favor:

- junior
- graduate
- entry-level
- early-career
- software engineer / backend / full stack roles

And should avoid or strongly down-rank:

- senior
- staff
- lead
- principal
- manager-heavy roles

If the profile includes relevant domain history, such as banking or fintech-adjacent work, use that as a positive search and ranking signal where appropriate.

If target companies are listed, treat them as genuine priority signals, not decorative metadata.

## Search strategy formation (mandatory)

Do not just pass through raw profile text.

Build a search strategy from the interpreted profile.

The strategy should include:

- prioritized role titles
- junior/entry-level variants when relevant
- domain-aware variants when relevant
- company-seeded searches for preferred companies
- exclusions or down-ranking rules
- notes about what likely counts as weak fit

### Search strategy quality rules

- Prefer targeted searches over noisy broad ones
- Respect candidate seniority explicitly
- Respect preferred companies explicitly
- Use prior domain background when it helps narrow the search
- Avoid broad search plans that flood the pipeline with obviously mismatched senior roles

## Execution workflow

### 1. Confirm project runtime

Read `config/runtime.json`.

Check that the configured Python interpreter exists and can import `jobspy`.

### 2. Read and interpret the profile

Use `defaultProfile` unless another profile path is explicitly provided.

Before executing any scripts, produce a brief internal interpretation of:

- seniority
- target role family
- industries/domains to favor
- preferred companies
- avoid/down-rank patterns

### 3. Execute the project workflow

Use the configured Python interpreter to run these scripts from the project root:

```bash
<pythonPath> skills/job-search-skill/scripts/prepare_search_run.py
<pythonPath> skills/job-search-skill/scripts/search_backend_jobspy.py
<pythonPath> skills/job-search-skill/scripts/normalize_jobs.py
<pythonPath> skills/job-search-skill/scripts/render_search_summary.py
```

### 4. Review results against the interpreted profile

After retrieval, do not blindly accept the results.

Review them for:

- seniority mismatch
- role-family mismatch
- domain mismatch
- preferred-company presence or absence
- likely strong-fit roles
- likely weak-fit roles

Call out obvious failures in retrieval quality if the results do not align with the candidate profile.

## Operational guidance

- Treat this as a candidate-aware discovery skill, not a generic scraper
- Prefer fewer better searches over broad noisy recall
- Preserve backend traceability in saved files
- If the live backend fails, surface the failure clearly
- Do not fabricate fallback data
- When reporting to the user, separate:
  - retrieved jobs
  - likely good-fit jobs
  - obvious mismatches

## Success condition

A successful run should do more than fetch jobs.

It should:

- use the project runtime correctly
- perform live retrieval
- respect the candidate profile in search strategy
- reduce obvious seniority/domain mismatches
- save outputs to the project runtime-data area
- produce a user-facing summary that reflects actual fit, not just raw retrieval

## References

- `references/run-notes.md`
- `references/backend-notes.md`
- `references/notes.md`
