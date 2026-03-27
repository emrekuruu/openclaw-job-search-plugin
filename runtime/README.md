# Runtime

This folder is reserved for runtime-facing artifacts used by the cron job search agent.

Potential future contents:

- pid/state files
- backend session metadata
- temporary request payloads
- adapter diagnostics

For now, the main runtime contract lives in:

- `config/search-defaults.json`
- `data/profiles/`
- `data/search-runs/`
- `data/raw/`
- `data/jobs/`
