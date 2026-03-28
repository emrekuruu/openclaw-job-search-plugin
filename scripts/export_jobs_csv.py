#!/usr/bin/env python3
import json
import os
from pathlib import Path
from openpyxl import Workbook


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


def load_export_source(output_base: Path):
    final_results_dir = output_base / 'final-results'
    if final_results_dir.exists():
        final_files = sorted(final_results_dir.glob('*.json'))
        if final_files:
            source_file = final_files[-1]
            payload = json.loads(source_file.read_text())
            final_listings = payload.get('finalListings')
            if isinstance(final_listings, list):
                return source_file, final_listings, 'final-results'

    jobs_dir = output_base / 'jobs'
    job_files = sorted(jobs_dir.glob('*.json'))
    if not job_files:
        raise SystemExit('No job files found to export.')
    source_file = job_files[-1]
    jobs = json.loads(source_file.read_text())
    if not isinstance(jobs, list):
        raise SystemExit(f'Export source must be a list of jobs: {source_file}')
    return source_file, jobs, 'jobs'


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    exports_dir = output_base / 'exports'
    exports_dir.mkdir(parents=True, exist_ok=True)

    source_file, jobs, source_kind = load_export_source(output_base)
    run_id = source_file.stem

    fields = ['title', 'company', 'location', 'workMode', 'source', 'postedDate', 'url', 'summary', 'score', 'decision', 'reasoning']
    xlsx_path = exports_dir / f'{run_id}.xlsx'
    latest_path = exports_dir / 'latest.xlsx'

    wb = Workbook()
    ws = wb.active
    ws.title = 'Jobs'
    ws.append(fields)

    for job in jobs:
        reasoning = job.get('reasoning')
        if isinstance(reasoning, list):
            reasoning = ' | '.join(str(item) for item in reasoning)
        ws.append([job.get(k) if k != 'reasoning' else reasoning for k in fields])

    for column_cells in ws.columns:
        max_len = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            value = '' if cell.value is None else str(cell.value)
            if len(value) > max_len:
                max_len = len(value)
        ws.column_dimensions[column_letter].width = min(max_len + 2, 60)

    wb.save(xlsx_path)
    wb.save(latest_path)
    print(f'{xlsx_path} ({source_kind})')


if __name__ == '__main__':
    main()
