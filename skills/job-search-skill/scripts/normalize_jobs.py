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
    run_dir, search_path, search = load_latest_search(output_base)
    listings_dir = run_dir / 'listings'
    if not listings_dir.exists():
        raise SystemExit(f'Listings directory not found: {listings_dir}')

    listing_files = sorted(listings_dir.glob('*.json'))
    search['listingCount'] = len(listing_files)
    search_path.write_text(json.dumps(search, indent=2) + '\n')
    print(search_path)


if __name__ == '__main__':
    main()
