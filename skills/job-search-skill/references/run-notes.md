# Run Notes

Keep retrieval simple.

## Required runtime files

- `config/runtime.json`
- `config/search-defaults.json`
- candidate profile file

## Required run artifacts

Each run should produce:

- `runtime-data/search-runs/<runId>/search.json`
- `runtime-data/search-runs/<runId>/listings/*.json`
- `runtime-data/search-runs/<runId>/summary.md`

That is enough for the retrieval stage.

## Design rule

The agent owns:
- profile understanding
- search queries
- filters
- reasoning

The scripts own:
- creating the run folder
- executing JobSpy
- writing listing files
- rendering summary

Do not push candidate reasoning into regex-heavy scripts.
