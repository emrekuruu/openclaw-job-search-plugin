# JSON Resume Notes

Use this reference when generating resume output for the plugin runtime.

Standard:
- https://jsonresume.org/

Preferred visual reference and theme direction:
- https://registry.jsonresume.org/thomasdavis?theme=executive-slate

Recommended CLI renderer:
- `resumed`

Recommended default theme choice for this workflow:
- `jsonresume-theme-executive-slate` when available in the renderer environment

## Goal

Generate truthful, moderately tailored JSON Resume documents that the plugin can validate and render deterministically.

The goal is not to overfit every resume to a single listing. Tailor enough to:
- surface the strongest matches
- improve ATS relevance
- make the fit obvious to a recruiter

But keep the resume broad and reusable.

## Recommended top-level sections

Use only the sections supported by the profile:
- `$schema`
- `basics`
- `work`
- `volunteer`
- `education`
- `awards`
- `certificates`
- `publications`
- `skills`
- `languages`
- `interests`
- `references`
- `projects`

## High-value tailoring zones

Prioritize listing alignment in:
- `basics.label`
- `basics.summary`
- `work[].summary`
- `work[].highlights`
- `skills[]`
- `projects[]`

Use selective alignment, not blanket rewriting.

## Anti-overfitting rules

- Do not mirror the listing line-by-line
- Do not repeat listing keywords unnaturally across many sections
- Do not reshape the whole profile around one posting if the candidate is better presented more generally
- Prefer durable role labels like `Backend Engineer`, `Software Engineer`, or `Full-Stack Engineer` over overly narrow titles unless the profile strongly supports them
- Keep the summary broadly reusable while still reflecting the target direction

## Safe optimization rules

- Rephrase strongly; do not fabricate facts
- Add metrics only when present in the source profile
- If the candidate lacks a required tool, emphasize adjacent tools and transferable outcomes
- If the listing is broad, keep the resume coherent instead of chasing every keyword

## Rendering assumptions

The plugin can render JSON Resume files after they are written to runtime storage.

Expected source location pattern:
- `plugin-runtimes/job-search/resumes/<runId>/<listingId>.json`

Expected rendered outputs may include:
- `plugin-runtimes/job-search/resumes/<runId>/<listingId>.html`
- `plugin-runtimes/job-search/resumes/<runId>/<listingId>.pdf`

## Suggested delivery extras

Optionally provide a short note with:
- keywords lightly targeted
- content emphasized
- content omitted or deprioritized
- unsupported requirements left unclaimed
