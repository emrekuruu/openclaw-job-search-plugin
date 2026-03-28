#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path

from openpyxl import Workbook


EXPORT_FIELDS = [
    'score',
    'decision',
    'title',
    'company',
    'location',
    'workMode',
    'source',
    'postedDate',
    'url',
    'reasoning',
    'summary',
    'listingId',
    'evaluationPath',
]


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


def load_runtime_config(project_root: Path) -> dict:
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


def load_json(path: Path):
    return json.loads(path.read_text())


def stringify(value) -> str:
    if value is None:
        return ''
    if isinstance(value, list):
        return ' | '.join(stringify(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def latest_run_dir(base_dir: Path) -> Path:
    run_dirs = sorted(path for path in base_dir.iterdir() if path.is_dir()) if base_dir.exists() else []
    if not run_dirs:
        raise SystemExit(f'No run folders found in {base_dir}')
    return run_dirs[-1]


def resolve_run_id(output_base: Path, run_id: str | None) -> str:
    if run_id:
        return run_id
    return latest_run_dir(output_base / 'evaluations').name


def load_listing_map(search_run_dir: Path) -> dict:
    listings_dir = search_run_dir / 'listings'
    if not listings_dir.exists():
        raise SystemExit(f'Listings directory not found: {listings_dir}')

    listing_map = {}
    for listing_path in sorted(listings_dir.glob('*.json')):
        listing = load_json(listing_path)
        listing_id = listing.get('id')
        if listing_id:
            listing_map[listing_id] = listing
    return listing_map


def list_evaluation_files(evaluations_dir: Path) -> list[Path]:
    files = []
    for path in sorted(evaluations_dir.glob('*.json')):
        if path.name.endswith('.error.json'):
            continue
        files.append(path)
    return files


def build_export_rows(evaluations_dir: Path, listing_map: dict) -> list[dict]:
    evaluation_files = list_evaluation_files(evaluations_dir)
    if not evaluation_files:
        raise SystemExit(f'No evaluation JSON files found in {evaluations_dir}')

    rows = []
    for evaluation_path in evaluation_files:
        evaluation = load_json(evaluation_path)
        listing_id = evaluation.get('listingId') or evaluation_path.stem
        listing = listing_map.get(listing_id, {})
        rows.append({
            'score': evaluation.get('score'),
            'decision': evaluation.get('decision'),
            'title': listing.get('title'),
            'company': listing.get('company'),
            'location': listing.get('location'),
            'workMode': listing.get('workMode'),
            'source': listing.get('source'),
            'postedDate': listing.get('postedDate'),
            'url': listing.get('url'),
            'reasoning': evaluation.get('reasoning'),
            'summary': listing.get('summary'),
            'listingId': listing_id,
            'evaluationPath': str(evaluation_path),
        })

    return sorted(rows, key=lambda row: row.get('score') if row.get('score') is not None else -1, reverse=True)


def write_xlsx(rows: list[dict], xlsx_path: Path, sheet_title: str) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_title
    ws.append(EXPORT_FIELDS)

    for row in rows:
        ws.append([stringify(row.get(field)) for field in EXPORT_FIELDS])

    for column_cells in ws.columns:
        max_len = 0
        column_letter = column_cells[0].column_letter
        for cell in column_cells:
            value = '' if cell.value is None else str(cell.value)
            max_len = max(max_len, len(value))
        ws.column_dimensions[column_letter].width = min(max_len + 2, 60)

    wb.save(xlsx_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Export one evaluation run to a single Excel workbook.')
    parser.add_argument('--run-id', help='Evaluation/search run ID. Defaults to the latest run under runtime-data/evaluations/.')
    return parser.parse_args()


def main():
    args = parse_args()
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    run_id = resolve_run_id(output_base, args.run_id)

    evaluations_dir = output_base / 'evaluations' / run_id
    if not evaluations_dir.exists():
        raise SystemExit(f'Evaluations directory not found: {evaluations_dir}')

    search_run_dir = output_base / 'search-runs' / run_id
    if not search_run_dir.exists():
        raise SystemExit(f'Search run directory not found: {search_run_dir}')

    exports_dir = output_base / 'exports'
    exports_dir.mkdir(parents=True, exist_ok=True)

    rows = build_export_rows(evaluations_dir, load_listing_map(search_run_dir))

    xlsx_path = exports_dir / f'{run_id}.xlsx'
    latest_path = exports_dir / 'latest.xlsx'
    write_xlsx(rows, xlsx_path, sheet_title='Evaluations')
    write_xlsx(rows, latest_path, sheet_title='Evaluations')
    print(xlsx_path)


if __name__ == '__main__':
    main()
