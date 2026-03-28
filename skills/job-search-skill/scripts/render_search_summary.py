#!/usr/bin/env python3
import json
import os
from pathlib import Path


def resolve_project_root() -> Path:
    env_root = os.environ.get('JOB_SEARCH_BOT_ROOT')
    if not env_root:
        raise SystemExit('JOB_SEARCH_BOT_ROOT is not set.')
    root = Path(env_root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f'Configured JOB_SEARCH_BOT_ROOT does not exist: {root}')
    return root


def runtime_config_path(project_root: Path) -> Path:
    return project_root / 'config/runtime.json'


def resolve_runtime_value(project_root: Path, value: str) -> Path:
    p = Path(value)
    if p.is_absolute():
        return p
    return (project_root / p).resolve()


def load_runtime_config(project_root: Path):
    config_path = runtime_config_path(project_root)
    if not config_path.exists():
        raise SystemExit(f'Runtime config not found: {config_path}')
    data = json.loads(config_path.read_text())
    data['outputBase'] = str(resolve_runtime_value(project_root, data['outputBase']))
    return data


def load_latest_search(output_base: Path):
    runs_dir = output_base / 'search-runs'
    run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir()) if runs_dir.exists() else []
    if not run_dirs:
        raise SystemExit('No search runs found.')
    latest = run_dirs[-1]
    search_path = latest / 'search.json'
    if not search_path.exists():
        raise SystemExit(f'Missing search.json in latest run: {latest}')
    return latest, search_path, json.loads(search_path.read_text())


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    run_dir, _, search = load_latest_search(output_base)

    lines = []
    lines.append(f"# Search Summary — {search.get('runId')}")
    lines.append('')
    lines.append('## Candidate Understanding')
    candidate_understanding = search.get('candidateUnderstanding') or {}
    if candidate_understanding:
        for key, value in candidate_understanding.items():
            lines.append(f'- {key}: {value}')
    else:
        lines.append('- Not yet filled by the agent.')
    lines.append('')
    lines.append('## Queries')
    for index, query in enumerate(search.get('queries') or [], start=1):
        lines.append(f"- {index}. {query.get('query', '')}")
        lines.append(f"  - reasoning: {query.get('reasoning', '')}")
        filters = query.get('filters') or {}
        if filters:
            lines.append('  - filters:')
            for key, value in filters.items():
                lines.append(f'    - {key}: {value}')
        filter_reasoning = query.get('filterReasoning') or {}
        if filter_reasoning:
            lines.append('  - filter reasoning:')
            for key, value in filter_reasoning.items():
                lines.append(f'    - {key}: {value}')
    lines.append('')
    lines.append(f"## Listings\n- count: {search.get('listingCount', 0)}")

    summary_path = run_dir / 'summary.md'
    summary_path.write_text('\n'.join(lines) + '\n')
    print(summary_path)


if __name__ == '__main__':
    main()
