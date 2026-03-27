# Step 1 Wrapper Contract

## Goal

Wrap `job-search-mcp-jobspy` as the primary discovery backend for the first version of the cron job searcher.

The wrapper owns:

- candidate brief intake
- search parameter preparation
- result normalization
- result persistence
- cron-friendly run behavior

The backend owns:

- multi-source job discovery
- source-level filtering
- raw listing retrieval

## Input Contract

A Step 1 search run should accept:

- `candidateProfile` — CV text, summary, or structured candidate profile
- `desiredRoles` — one or more role titles / target job types
- `seniority` — optional
- `targetCompanies` — optional list of companies to prioritize
- `locations` — optional list of preferred locations
- `workModes` — optional list such as remote, hybrid, onsite
- `salaryExpectation` — optional
- `freshnessWindow` — optional, such as past 24h / 7d / 30d
- `notes` — optional operator notes or constraints

## Output Contract

Each run should produce:

1. A human-readable run summary
2. A structured search-run record
3. Normalized job records

## Search Run Record

Suggested fields:

```json
{
  "runId": "2026-03-27-product-manager-paris",
  "createdAt": "2026-03-27T16:00:00+01:00",
  "backend": "job-search-mcp-jobspy",
  "desiredRoles": ["Product Manager", "AI Product Manager"],
  "targetCompanies": ["OpenAI", "Mistral AI"],
  "locations": ["Paris", "Remote"],
  "workModes": ["remote", "hybrid"],
  "resultCount": 0,
  "notes": "Step 1 discovery run"
}
```

## Normalized Job Record

Suggested fields:

```json
{
  "id": "<stable-local-id>",
  "title": "Senior Product Manager",
  "company": "Example Corp",
  "location": "Paris, France",
  "workMode": "hybrid",
  "source": "linkedin",
  "url": "https://example.com/job/123",
  "postedDate": null,
  "discoveredAt": "2026-03-27T16:00:00+01:00",
  "salary": null,
  "summary": "AI platform and marketplace role.",
  "fitNote": "Potential fit based on AI/product background.",
  "status": "new",
  "runId": "2026-03-27-product-manager-paris"
}
```

## Save Paths

- `data/search-runs/<run-id>.md`
- `data/search-runs/<run-id>.json`
- `data/jobs/<run-id>.json`

## Step 1 Scope Boundaries

This wrapper does not yet own:

- fit scoring beyond lightweight notes
- application generation
- application submission
- notification workflows
- interview preparation
- long-term tracking lifecycle

## Open Question

Next step: confirm the actual interface exposed by `job-search-mcp-jobspy` and map the wrapper inputs to its real parameters.
