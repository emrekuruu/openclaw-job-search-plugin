#!/usr/bin/env python3
import json
import os
from pathlib import Path


def resolve_project_root() -> Path:
    env_root = os.environ.get('JOB_SEARCH_BOT_ROOT')
    if not env_root:
        raise SystemExit('JOB_SEARCH_BOT_ROOT is not set. This skill requires an explicit project root.')
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
    runs_dir = output_base / 'search-runs'
    jobs_dir = output_base / 'jobs'

    run_files = sorted(runs_dir.glob('*.json'))
    if not run_files:
        raise SystemExit('No search runs found.')
    latest = run_files[-1]
    run = json.loads(latest.read_text())
    run_id = run['runId']

    jobs_path = jobs_dir / f'{run_id}.json'
    jobs = json.loads(jobs_path.read_text()) if jobs_path.exists() else []

    lines = []
    lines.append(f'# Search Run Summary - {run_id}')
    lines.append('')
    lines.append('## Run Metadata')
    lines.append(f"- Run ID: `{run_id}`")
    lines.append(f"- Created at: `{run.get('createdAt')}`")
    lines.append(f"- Backend: `{run.get('backend')}`")
    lines.append(f"- Profile path: `{run.get('profilePath')}`")
    lines.append('')
    lines.append('## Search Brief')
    lines.append(f"- Desired roles: {', '.join(run.get('desiredRoles', []))}")
    lines.append(f"- Target companies: {', '.join(run.get('targetCompanies', []))}")
    lines.append(f"- Locations: {', '.join(run.get('locations', []))}")
    lines.append(f"- Work modes: {', '.join(run.get('workModes', []))}")
    lines.append(f"- Freshness window: {run.get('freshnessWindow')}")
    lines.append('')
    lines.append('## Results')
    lines.append(f"- Total normalized results: {len(jobs)}")
    for job in jobs[:10]:
        lines.append(f"- {job['title']} — {job['company']} — {job['location']} — {job['source']}")
    lines.append('')
    lines.append('## Notes')
    lines.append(f"- {run.get('notes', '')}")

    out = runs_dir / f'{run_id}.md'
    out.write_text('\n'.join(lines) + '\n')
    print(out)


if __name__ == '__main__':
    main()
