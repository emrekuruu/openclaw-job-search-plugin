#!/usr/bin/env python3
import json
from pathlib import Path

from jobspy import scrape_jobs

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[3]
RUNTIME_CONFIG = PROJECT_ROOT / 'config/runtime.json'


def load_runtime_config():
    if not RUNTIME_CONFIG.exists():
        raise SystemExit(f'Runtime config not found: {RUNTIME_CONFIG}')
    return json.loads(RUNTIME_CONFIG.read_text())


def load_latest_run(runs_dir: Path):
    run_files = sorted(runs_dir.glob('*.json'))
    if not run_files:
        raise SystemExit('No search runs found. Run prepare_search_run.py first.')
    latest = run_files[-1]
    return json.loads(latest.read_text())


def load_search_config(runtime):
    config_path = Path(runtime['searchDefaultsPath'])
    if not config_path.exists():
        raise SystemExit(f'Search defaults config not found: {config_path}')
    return json.loads(config_path.read_text())


def build_requests(run, config):
    requests = []
    roles = run.get('desiredRoles', [])[:2]
    locations = run.get('locations', [])[:2] or ['Remote']
    work_modes = set(v.lower() for v in run.get('workModes', []))
    target_companies = run.get('targetCompanies', [])[:3]

    for role in roles:
        for location in locations:
            requests.append({
                'search_term': role,
                'location': location,
                'site_name': config['siteNames'],
                'results_wanted': config['resultsWanted'],
                'hours_old': config['freshnessHours'],
                'is_remote': 'remote' in work_modes,
                'easy_apply': config['easyApply'],
                'linkedin_fetch_description': config['linkedinFetchDescription'],
                'country_indeed': config['defaultCountryIndeed'],
                'verbose': config['verbose'],
            })
        for company in target_companies:
            requests.append({
                'search_term': f'{role} {company}',
                'location': locations[0],
                'site_name': config['siteNames'],
                'results_wanted': 8,
                'hours_old': config['freshnessHours'],
                'is_remote': 'remote' in work_modes,
                'easy_apply': config['easyApply'],
                'linkedin_fetch_description': False,
                'country_indeed': config['defaultCountryIndeed'],
                'verbose': config['verbose'],
            })
    return requests


def dataframe_to_records(df):
    if df is None:
        return []
    return json.loads(df.to_json(orient='records', date_format='iso'))


def live_execute(requests):
    payload = []
    failures = []
    for request in requests:
        try:
            df = scrape_jobs(**request)
            payload.append({
                'request': request,
                'mode': 'live',
                'results': dataframe_to_records(df),
            })
        except Exception as e:
            failures.append({'request': request, 'error': repr(e)})
            payload.append({
                'request': request,
                'mode': 'error',
                'error': repr(e),
                'results': [],
            })

    if not any(entry.get('mode') == 'live' and entry.get('results') for entry in payload):
        raise SystemExit(f'Live job search failed or returned no results for all requests: {failures}')

    return payload


def main():
    runtime = load_runtime_config()
    output_base = Path(runtime['outputBase'])
    runs_dir = output_base / 'search-runs'
    raw_dir = output_base / 'raw'

    run = load_latest_run(runs_dir)
    config = load_search_config(runtime)
    run_id = run['runId']
    requests = build_requests(run, config)
    raw_results = live_execute(requests)

    raw_payload = {
        'runId': run_id,
        'backend': 'jobspy-project-adapter',
        'mode': 'live',
        'requests': requests,
        'rawResults': raw_results,
    }

    raw_dir.mkdir(parents=True, exist_ok=True)
    out = raw_dir / f'{run_id}.json'
    out.write_text(json.dumps(raw_payload, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
