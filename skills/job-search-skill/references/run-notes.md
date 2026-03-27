# Run Notes

## Current execution model

The skill operates as a self-contained skill-local pipeline:

1. `scripts/prepare_search_run.py`
2. `scripts/search_backend_jobspy.py`
3. `scripts/normalize_jobs.py`
4. `scripts/render_search_summary.py`

## Runtime

This skill expects a shared OpenClaw skill runtime interpreter at:

- `~/.openclaw-skill-venv/bin/python`

Required packages in that runtime:

- `python-jobspy`
- `pandas`
- `pydantic`

## Outputs to check

After a run, inspect:

- `data/search-runs/*.json`
- `data/search-runs/*.md`
- `data/raw/*.json`
- `data/jobs/*.json`

## Current limitations

Known current limitations:

- source noise and regional failures may occur
- ZipRecruiter may fail in EU contexts
- deduplication is not yet strong
- work mode normalization still needs improvement
