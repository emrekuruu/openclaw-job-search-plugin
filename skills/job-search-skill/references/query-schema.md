# Job Search Query Schema

Use this schema when preparing `candidateUnderstanding` and `queries` for `job_search_prepare_run`.

## Purpose

The retrieval worker expects normalized query objects.
Do not invent ad-hoc keys like `q` or `employmentType` unless they are mapped into this schema before writing `search.json`.

## Normalized query object

```json
{
  "query": "Junior Backend Engineer",
  "reasoning": "Direct match for early-career backend roles in Istanbul.",
  "filters": {
    "location": "Istanbul, Turkey",
    "site_name": ["linkedin"],
    "results_wanted": 15,
    "hours_old": 720,
    "job_type": "fulltime",
    "is_remote": false,
    "easy_apply": false,
    "linkedin_fetch_description": true,
    "country_indeed": "turkey",
    "distance": 50
  },
  "filterReasoning": {
    "location": "Prefer Istanbul-based roles.",
    "job_type": "Default to full-time unless the profile explicitly requests otherwise.",
    "hours_old": "Prefer roles from the last 30 days.",
    "country_indeed": "Candidate is authorized in Turkey and targeting Turkey-based opportunities."
  }
}
```

## Required fields

- `query` — non-empty search text
- `filters` — object, may be empty but should normally be populated deliberately

## Recommended fields

- `reasoning`
- `filterReasoning`

## Supported filter keys

Use these canonical keys inside `filters`:

- `location`
- `site_name` (array, e.g. `["linkedin"]`)
- `results_wanted`
- `hours_old`
- `job_type` (`fulltime`, `parttime`, etc.)
- `is_remote` (boolean)
- `easy_apply` (boolean)
- `linkedin_fetch_description` (boolean)
- `country_indeed`
- `distance`

## Invalid input examples

These shapes are invalid unless normalized before prepare-run:

```json
{ "q": "Junior Backend Engineer" }
```

```json
{ "employmentType": "full-time" }
```

```json
{ "site": "linkedin" }
```

## Required normalization

Normalize these common ad-hoc inputs before calling `job_search_prepare_run`:

- `q` -> `query`
- `site` -> `filters.site_name` as an array
- `employmentType: "full-time"` -> `filters.job_type: "fulltime"`
- top-level `location` -> `filters.location`

## Rule

If a query object is malformed, fix it before prepare-run.
Do not rely on the retrieval worker to guess intent from partial or ad-hoc fields.
