---
name: job-search-skill
description: Run candidate-aware job discovery for the job-search-bot project. Use when an agent needs to read a candidate profile, infer seniority and fit directly from that profile, build a focused search strategy, execute live job retrieval through the project runtime, and save cleaned results for later user presentation. Do not use for applications, resume tailoring, or interview preparation. Fail clearly if the project runtime or live backend is unavailable.
---

# Job Search Skill

Use this skill to run **Step 1: candidate-aware discovery and collection** for the `job-search-bot` project.

This skill is **project-centric** and **search-plan-first**.
It should not behave like a dumb script launcher. The scripts exist to execute the plan. The skill is responsible for reading the candidate profile, deciding what matters, forming a search strategy, and then reviewing results lightly for obvious mismatches.

## Core rule

Do not jump straight from profile file to raw search execution.

Before running the backend, the agent must:

1. read the candidate profile carefully
2. infer the candidate model from the profile itself
3. decide how search should be shaped
4. decide what should be avoided
5. build a focused search plan
6. then execute the project workflow

## Important design rule

Search/filter intelligence should come from the **profile**, not from app-level configuration.

The runtime config is only for application-level concerns such as:
- project root
- python path
- output path
- backend defaults
- source selection

The candidate profile is where the agent should infer:
- seniority
- role family
- domain relevance
- preferred companies
- location constraints
- work mode constraints
- what kinds of roles should be avoided

## What this skill does

This skill:

- reads the project runtime configuration from `config/runtime.json`
- reads the configured profile path
- interprets the candidate profile before searching
- derives search strategy from candidate seniority, background, and preferences
- runs a live JobSpy-backed backend search through the project runtime
- saves raw backend results
- normalizes and lightly cleans results into the project schema
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

Before searching, extract and reason about from the profile:

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

If the profile is for a recently graduated engineer with around 1 year of experience, the search strategy should favor:

- junior
- graduate
- entry-level
- early-career
- software engineer / backend / full stack roles

And should avoid or strongly suppress:

- senior
- staff
- lead
- principal
- manager-heavy roles

If the profile includes relevant domain history, such as banking or fintech-adjacent work, use that as a positive search signal.

If target companies are listed, treat them as genuine priority signals and search them explicitly.

## Search strategy formation (mandatory)

Do not just pass through raw profile text.

Build a concrete search plan from the interpreted profile.

The strategy should include:

- prioritized role-title queries
- junior/entry-level variants when relevant
- domain-aware variants when relevant
- company-targeted searches for preferred companies
- terms to avoid
- notes about what likely counts as weak fit

### Search strategy quality rules

- Prefer fewer better searches over broad noisy ones
- Low amount of high-quality results is better than many weak matches
- Respect candidate seniority explicitly
- Respect preferred companies explicitly
- Use prior domain background when it helps narrow the search
- Search target companies directly when they are listed
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

### 3. Build the search plan

Construct a focused plan such as:

- junior role queries
- company-targeted queries
- domain-aware queries
- location-aware variants

The plan should be based on profile reasoning, not on hardcoded filter rules in config.

### 4. Execute the project workflow

Use the configured Python interpreter to run these scripts from the project root:

```bash
<pythonPath> skills/job-search-skill/scripts/prepare_search_run.py
<pythonPath> skills/job-search-skill/scripts/search_backend_jobspy.py
<pythonPath> skills/job-search-skill/scripts/normalize_jobs.py
<pythonPath> skills/job-search-skill/scripts/render_search_summary.py
```

### 5. Review results lightly

After retrieval, do not blindly accept the results.

Do a light quality pass for:

- obvious seniority mismatch
- obvious role-family mismatch
- duplicate results
- whether preferred companies appeared
- whether the output reflects the candidate profile at all

This is not a numerical scoring stage. The goal is better search planning, not ranking theater.

## Operational guidance

- Treat this as a candidate-aware discovery skill, not a generic scraper
- Prefer fewer better searches over broad noisy recall
- Preserve backend traceability in saved files
- If the live backend fails, surface the failure clearly
- Do not fabricate fallback data
- When reporting to the user, separate:
  - retrieved jobs
  - likely relevant jobs
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
