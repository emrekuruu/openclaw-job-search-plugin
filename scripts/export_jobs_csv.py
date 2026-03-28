#!/usr/bin/env python3
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


def latest_final_results_path(output_base: Path) -> Path:
    final_results_dir = output_base / 'final-results'
    final_files = sorted(final_results_dir.glob('*.json')) if final_results_dir.exists() else []
    if not final_files:
        raise SystemExit(f'No final-results JSON files found in {final_results_dir}')
    return final_files[-1]


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


def load_listing_map(payload: dict) -> dict:
    listing_map = {}

    for item in payload.get('finalListings') or []:
        listing_id = item.get('listingId') or item.get('id')
        if listing_id:
            listing_map[listing_id] = item

    for file_path in payload.get('evaluatedListingFiles') or []:
        path = Path(file_path)
        if not path.exists():
            continue
        listing = load_json(path)
        listing_id = listing.get('id')
        if listing_id:
            listing_map[listing_id] = listing

    listings_dir = payload.get('listingsDir')
    if listings_dir:
        path = Path(listings_dir)
        if path.exists():
            for listing_path in sorted(path.glob('*.json')):
                listing = load_json(listing_path)
                listing_id = listing.get('id')
                if listing_id and listing_id not in listing_map:
                    listing_map[listing_id] = listing

    return listing_map


def build_export_rows(payload: dict) -> list[dict]:
    listing_map = load_listing_map(payload)

    if payload.get('evaluations'):
        rows = []
        for evaluation in payload['evaluations']:
            listing_id = evaluation.get('listingId')
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
            })
        return sorted(rows, key=lambda row: row.get('score') if row.get('score') is not None else -1, reverse=True)

    final_listings = payload.get('finalListings') or []
    if not isinstance(final_listings, list) or not final_listings:
        raise SystemExit('Final-results JSON must contain either evaluations or finalListings.')

    rows = []
    for listing in final_listings:
        rows.append({
            'score': listing.get('score'),
            'decision': listing.get('decision'),
            'title': listing.get('title'),
            'company': listing.get('company'),
            'location': listing.get('location'),
            'workMode': listing.get('workMode'),
            'source': listing.get('source'),
            'postedDate': listing.get('postedDate'),
            'url': listing.get('url'),
            'reasoning': listing.get('reasoning'),
            'summary': listing.get('summary'),
            'listingId': listing.get('listingId') or listing.get('id'),
        })

    return sorted(rows, key=lambda row: row.get('score') if row.get('score') is not None else -1, reverse=True)


def write_xlsx(rows: list[dict], xlsx_path: Path) -> None:
    wb = Workbook()
    ws = wb.active
    ws.title = 'Final Results'
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


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    exports_dir = output_base / 'exports'
    exports_dir.mkdir(parents=True, exist_ok=True)

    source_file = latest_final_results_path(output_base)
    payload = load_json(source_file)
    rows = build_export_rows(payload)

    run_id = payload.get('runId') or source_file.stem
    xlsx_path = exports_dir / f'{run_id}.xlsx'
    latest_path = exports_dir / 'latest.xlsx'

    write_xlsx(rows, xlsx_path)
    write_xlsx(rows, latest_path)
    print(xlsx_path)


if __name__ == '__main__':
    main()
