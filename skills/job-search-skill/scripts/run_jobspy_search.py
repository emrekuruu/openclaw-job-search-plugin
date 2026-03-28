#!/usr/bin/env python3
import hashlib
import json
import os
from pathlib import Path

from jobspy import scrape_jobs


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def state_dir() -> Path:
    env_root = os.environ.get('OPENCLAW_STATE_DIR')
    if not env_root:
        raise SystemExit('OPENCLAW_STATE_DIR is not set.')
    return Path(env_root).expanduser().resolve() / 'plugin-runtimes' / 'job-search'


def load_search_defaults() -> dict:
    path = repo_root() / 'config' / 'search-defaults.json'
    if not path.exists():
        raise SystemExit(f'Search defaults missing: {path}')
    return json.loads(path.read_text())


def latest_run_dir(base: Path) -> Path:
    runs_dir = base / 'search-runs'
    runs_dir.mkdir(parents=True, exist_ok=True)
    run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir())
    if not run_dirs:
        raise SystemExit('No search runs found.')
    return run_dirs[-1]


def load_search(run_dir: Path):
    search_path = run_dir / 'search.json'
    if not search_path.exists():
        raise SystemExit(f'Missing search.json: {search_path}')
    payload = json.loads(search_path.read_text())
    profile_path = Path(payload.get('profilePath', ''))
    if not profile_path.exists():
        raise SystemExit(f'Candidate profile does not exist: {profile_path}')
    return search_path, payload


def slugify(text: str) -> str:
    return ''.join(ch.lower() if ch.isalnum() else '-' for ch in text).strip('-') or 'listing'


def listing_identity(listing: dict) -> str:
    return str(listing.get('url') or f"{listing.get('company','unknown-company')}::{listing.get('title','unknown-title')}::{listing.get('location','unknown-location')}::{listing.get('query','unknown-query')}")


def listing_id(run_id: str, listing: dict) -> str:
    base = slugify(f"{run_id}-{listing.get('company','unknown-company')}-{listing.get('title','unknown-title')}")
    suffix = hashlib.sha1(listing_identity(listing).encode('utf-8')).hexdigest()[:10]
    return f"{base}-{suffix}"


def normalize_listing(run_id: str, raw: dict, query_entry: dict) -> dict:
    listing = {
        'title': raw.get('title') or raw.get('job_title') or 'Unknown Title',
        'company': raw.get('company') or raw.get('company_name') or 'Unknown Company',
        'location': raw.get('location') or raw.get('job_location') or 'Unknown Location',
        'workMode': raw.get('workMode') or ('remote' if raw.get('is_remote') else None),
        'source': raw.get('source') or raw.get('site') or raw.get('site_name') or 'unknown',
        'url': raw.get('url') or raw.get('job_url') or raw.get('job_url_direct') or '',
        'postedDate': raw.get('postedDate') or raw.get('date_posted'),
        'salary': raw.get('salary') or raw.get('min_amount'),
        'summary': raw.get('summary') or raw.get('description') or raw.get('job_summary') or '',
        'query': query_entry.get('query'),
        'reasoning': query_entry.get('reasoning'),
        'filters': query_entry.get('filters', {}),
        'filterReasoning': query_entry.get('filterReasoning', {}),
        'runId': run_id,
    }
    listing['id'] = listing_id(run_id, listing)
    return listing


def main():
    base = state_dir()
    defaults = load_search_defaults()
    run_dir = latest_run_dir(base)
    search_path, search = load_search(run_dir)
    queries = search.get('queries') or []
    if not queries:
        raise SystemExit('search.json has no queries.')

    listings_dir = run_dir / 'listings'
    if listings_dir.exists():
        for file in listings_dir.glob('*.json'):
            file.unlink()
    listings_dir.mkdir(parents=True, exist_ok=True)

    seen = set()
    executed_queries = []
    listing_count = 0

    for query_entry in queries:
        filters = query_entry.get('filters') or {}
        request = {
            'site_name': filters.get('site_name', defaults.get('siteNames')),
            'search_term': query_entry.get('query'),
            'location': filters.get('location'),
            'results_wanted': filters.get('results_wanted', defaults.get('resultsWanted', 10)),
            'hours_old': filters.get('hours_old', defaults.get('hoursOld', defaults.get('freshnessHours', 720))),
            'is_remote': filters.get('is_remote', False),
            'easy_apply': filters.get('easy_apply', defaults.get('easyApply', False)),
            'linkedin_fetch_description': filters.get('linkedin_fetch_description', defaults.get('linkedinFetchDescription', True)),
            'country_indeed': filters.get('country_indeed', defaults.get('defaultCountryIndeed', 'turkey')),
            'verbose': filters.get('verbose', defaults.get('verbose', 1)),
            'job_type': filters.get('job_type', defaults.get('jobType', 'fulltime')),
            'distance': filters.get('distance', defaults.get('distance')),
        }
        request = {k: v for k, v in request.items() if v is not None}
        df = scrape_jobs(**request)
        results = json.loads(df.to_json(orient='records', date_format='iso'))
        executed_queries.append({
            'query': query_entry.get('query'),
            'reasoning': query_entry.get('reasoning'),
            'filters': filters,
            'filterReasoning': query_entry.get('filterReasoning', {}),
            'request': request,
            'resultCount': len(results),
        })
        for raw in results:
            listing = normalize_listing(search['runId'], raw, query_entry)
            identity = listing_identity(listing).lower()
            if identity in seen:
                continue
            seen.add(identity)
            (listings_dir / f"{listing['id']}.json").write_text(json.dumps(listing, indent=2) + '\n')
            listing_count += 1

    search['status'] = 'completed'
    search['listingCount'] = listing_count
    search['executedQueries'] = executed_queries
    artifacts = search.get('artifacts') or {}
    artifacts['searchPath'] = str(search_path)
    artifacts['listingsDir'] = str(listings_dir)
    search['artifacts'] = artifacts
    search_path.write_text(json.dumps(search, indent=2) + '\n')
    print(search_path)


if __name__ == '__main__':
    main()
