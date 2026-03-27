#!/usr/bin/env python3
import csv
import json
import os
from pathlib import Path


def resolve_project_root() -> Path:
    env_root = os.environ.get('JOB_SEARCH_BOT_ROOT')
    if not env_root:
        raise SystemExit('JOB_SEARCH_BOT_ROOT is not set. Export requires an explicit project root.')
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
    data['projectRoot'] = str(project_root)
    data['pythonPath'] = str(resolve_runtime_value(project_root, data['pythonPath']))
    data['outputBase'] = str(resolve_runtime_value(project_root, data['outputBase']))
    data['defaultProfile'] = str(resolve_runtime_value(project_root, data['defaultProfile']))
    data['searchDefaultsPath'] = str(resolve_runtime_value(project_root, data['searchDefaultsPath']))
    return data


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    jobs_dir = output_base / 'jobs'
    exports_dir = output_base / 'exports'
    exports_dir.mkdir(parents=True, exist_ok=True)

    job_files = sorted(jobs_dir.glob('*.json'))
    if not job_files:
        raise SystemExit('No job files found to export.')

    source_file = job_files[-1]
    jobs = json.loads(source_file.read_text())
    run_id = source_file.stem

    fields = ['title', 'company', 'location', 'workMode', 'source', 'postedDate', 'url', 'summary']
    csv_path = exports_dir / f'{run_id}.csv'
    latest_path = exports_dir / 'latest.csv'

    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            row = {k: job.get(k) for k in fields}
            writer.writerow(row)

    latest_path.write_text(csv_path.read_text())
    print(csv_path)


if __name__ == '__main__':
    main()
