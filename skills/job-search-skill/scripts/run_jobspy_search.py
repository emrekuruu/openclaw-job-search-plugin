#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path

from jobspy import scrape_jobs

ALLOWED_REQUEST_FIELDS = {
    'site_name',
    'search_term',
    'location',
    'results_wanted',
    'hours_old',
    'is_remote',
    'easy_apply',
    'linkedin_fetch_description',
    'country_indeed',
    'verbose',
    'job_type',
    'distance',
    'linkedin_company_ids',
    'offset',
    'user_agent',
}


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
    data['defaultProfile'] = str(resolve_runtime_value(project_root, data['defaultProfile']))
    data['searchDefaultsPath'] = str(resolve_runtime_value(project_root, data['searchDefaultsPath']))
    return data


def load_search_defaults(project_root: Path, runtime: dict):
    config_path = Path(runtime['searchDefaultsPath'])
    if not config_path.exists():
        raise SystemExit(f'Search defaults config not found: {config_path}')
    return json.loads(config_path.read_text())


def latest_run_dir(output_base: Path) -> Path:
    runs_dir = output_base / 'search-runs'
    run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir()) if runs_dir.exists() else []
    if not run_dirs:
        raise SystemExit('No search run folders found. Create a run folder with search.json first.')
    return run_dirs[-1]


def load_search_json(run_dir: Path) -> tuple[Path, dict]:
    search_path = run_dir / 'search.json'
    if not search_path.exists():
        raise SystemExit(f'Missing search.json: {search_path}')
    payload = json.loads(search_path.read_text())
    return search_path, payload


def build_request(query_entry: dict, defaults: dict) -> dict:
    filters = query_entry.get('filters') or {}
    request = {
        'site_name': filters.get('site_name') or defaults.get('siteNames'),
        'search_term': query_entry.get('query'),
        'location': filters.get('location'),
        'results_wanted': filters.get('results_wanted', defaults.get('resultsWanted', 10)),
        'hours_old': filters.get('hours_old', defaults.get('hoursOld', defaults.get('freshnessHours', 24 * 30))),
        'is_remote': filters.get('is_remote', False),
        'easy_apply': filters.get('easy_apply', defaults.get('easyApply', False)),
        'linkedin_fetch_description': filters.get('linkedin_fetch_description', defaults.get('linkedinFetchDescription', True)),
        'country_indeed': filters.get('country_indeed', defaults.get('defaultCountryIndeed', 'turkey')),
        'verbose': filters.get('verbose', defaults.get('verbose', 1)),
        'job_type': filters.get('job_type', defaults.get('jobType', 'fulltime')),
        'distance': filters.get('distance', defaults.get('distance')),
    }
    request = {key: value for key, value in request.items() if value is not None}
    unknown = sorted(set(request) - ALLOWED_REQUEST_FIELDS)
    if unknown:
        raise SystemExit(f'Unsupported JobSpy request fields: {unknown}')
    if not request.get('search_term'):
        raise SystemExit('Each search.json query entry must include a non-empty query.')
    return request


def dataframe_to_records(df):
    if df is None:
        return []
    return json.loads(df.to_json(orient='records', date_format='iso'))


def slugify(text: str) -> str:
    text = text.lower().replace('/', '-')
    return ''.join(ch if ch.isalnum() or ch == '-' else '-' for ch in text).strip('-')


def normalize_listing(raw: dict, run_id: str, query_entry: dict) -> dict:
    title = raw.get('title') or raw.get('job_title') or 'Unknown Title'
    company = raw.get('company') or raw.get('company_name') or 'Unknown Company'
    location = raw.get('location') or raw.get('job_location') or 'Unknown Location'
    url = raw.get('url') or raw.get('job_url') or raw.get('job_url_direct') or ''
    source = raw.get('source') or raw.get('site') or raw.get('site_name') or 'unknown'
    summary = raw.get('summary') or raw.get('description') or raw.get('job_summary') or ''
    listing_id = slugify(f'{run_id}-{company}-{title}')
    return {
        'id': listing_id,
        'runId': run_id,
        'title': title,
        'company': company,
        'location': location,
        'workMode': raw.get('workMode') or ('remote' if raw.get('is_remote') else None),
        'source': source,
        'url': url,
        'postedDate': raw.get('postedDate') or raw.get('date_posted'),
        'salary': raw.get('salary') or raw.get('min_amount'),
        'summary': summary,
        'query': query_entry.get('query'),
        'reasoning': query_entry.get('reasoning'),
        'filters': query_entry.get('filters', {}),
        'filterReasoning': query_entry.get('filterReasoning', {}),
        'retrievedAt': datetime.now().astimezone().isoformat(),
    }


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    defaults = load_search_defaults(project_root, runtime)
    output_base = Path(runtime['outputBase'])
    run_dir = latest_run_dir(output_base)
    listings_dir = run_dir / 'listings'
    listings_dir.mkdir(parents=True, exist_ok=True)

    search_path, search = load_search_json(run_dir)
    queries = search.get('queries') or []
    if not queries:
        raise SystemExit('search.json has no queries. The agent must write the search plan first.')

    run_id = search.get('runId') or run_dir.name
    executed_queries = []
    seen = set()
    listing_count = 0

    for query_entry in queries:
        request = build_request(query_entry, defaults)
        df = scrape_jobs(**request)
        results = dataframe_to_records(df)
        executed_queries.append({
            'query': query_entry.get('query'),
            'reasoning': query_entry.get('reasoning'),
            'filters': query_entry.get('filters', {}),
            'filterReasoning': query_entry.get('filterReasoning', {}),
            'request': request,
            'resultCount': len(results),
        })
        for raw in results:
            listing = normalize_listing(raw, run_id, query_entry)
            dedup_key = (listing.get('url') or f"{listing['company']}::{listing['title']}").lower()
            if dedup_key in seen:
                continue
            seen.add(dedup_key)
            listing_path = listings_dir / f"{listing['id']}.json"
            listing_path.write_text(json.dumps(listing, indent=2) + '\n')
            listing_count += 1

    search['status'] = 'completed'
    search['listingCount'] = listing_count
    search['executedQueries'] = executed_queries
    search['artifacts'] = {
        'searchPath': str(search_path),
        'listingsDir': str(listings_dir),
    }
    search_path.write_text(json.dumps(search, indent=2) + '\n')
    print(search_path)


if __name__ == '__main__':
    main()
