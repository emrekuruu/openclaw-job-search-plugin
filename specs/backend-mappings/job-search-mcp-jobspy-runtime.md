# job-search-mcp-jobspy Runtime Integration

## Summary

The inspected backend ecosystem suggests that `job-search-mcp-jobspy` is backed by a JobSpy MCP server and typically exposes a structured job-search tool interface.

Across the inspected references, the most concrete interface shape looks like:

- MCP server process running locally
- a search tool such as `search_jobs` or `scrape_jobs_tool`
- structured parameters for search terms, location, job boards, recency, remote filtering, and result count

## Practical runtime assumptions

Likely requirements:

- Python 3.10+
- JobSpy-compatible MCP server installed
- dependencies such as `mcp`, `python-jobspy` / `jobspy`, `pandas`, `pydantic`
- local MCP client/runtime that can call the server tool

## Concrete parameter model observed

Observed/likely parameters across implementations:

- `search_term` — primary job title / keywords
- `location` — search geography
- `site_name` or `site_names` — job boards to query
- `results_wanted` — result count
- `hours_old` — recency filter
- `job_type` — employment type
- `is_remote` — remote-only filter
- `distance` — radius
- `easy_apply` — Easy Apply filter
- `country_indeed` — Indeed/Glassdoor region
- `linkedin_fetch_description` — optional, slower
- `offset` — pagination
- `verbose` — diagnostics

## Implication for our wrapper

Our wrapper can now map local contract fields into likely backend fields:

- `desiredRoles[]` → one or more `search_term` values
- `locations[]` → `location`
- `workModes` including remote → `is_remote=true` when appropriate
- `freshnessWindow=30d` → convert to approximate `hours_old`
- preferred source selection → `site_name` / `site_names`
- recency and result count → backend controls

## Proposed first-pass invocation profile

For the first real run, keep it conservative:

- `search_term`: one role at a time
- `location`: one location at a time
- `site_names`: indeed, linkedin, zip_recruiter, google
- `results_wanted`: 10-20
- `hours_old`: 24 * 30
- `is_remote`: true only for remote-focused searches
- `linkedin_fetch_description`: false
- `easy_apply`: false initially
- `verbose`: low

## Why this matters

This confirms that our wrapper design is compatible with the backend family we selected.

The wrapper does not need the backend to understand the candidate profile directly. It only needs to translate project-owned search intent into concrete tool parameters.

## Current blocker

We still need one of the following to move into true execution:

1. a local running JobSpy MCP server we can call, or
2. a direct local implementation path using the JobSpy library without MCP as a temporary first-pass bridge

## Implementation recommendation

For a fast Step 1 first pass, the most practical path may be:

### Option A — ideal architecture
Run the MCP server and invoke its search tool.

### Option B — practical bridge
Implement a temporary local adapter script that calls JobSpy-compatible library/runtime directly, then normalize and save results using the same wrapper contract.

Option B preserves progress even if the MCP integration takes longer.
