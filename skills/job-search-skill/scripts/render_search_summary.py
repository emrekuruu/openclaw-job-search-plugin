#!/usr/bin/env python3
import json
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[3]
RUNTIME_CONFIG = PROJECT_ROOT / 'config/runtime.json'


def load_runtime_config():
    if not RUNTIME_CONFIG.exists():
        raise SystemExit(f'Runtime config not found: {RUNTIME_CONFIG}')
    return json.loads(RUNTIME_CONFIG.read_text())


def main():
    runtime = load_runtime_config()
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
