#!/usr/bin/env python3
import json
from pathlib import Path

from jobspy import scrape_jobs

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / 'data/search-runs'
RAW_DIR = ROOT / 'data/raw'
CONFIG_PATH = ROOT / 'config/search-defaults.json'


def load_latest_run():
    run_files = sorted(RUNS_DIR.glob('*.json'))
    if not run_files:
        raise SystemExit('No search runs found. Run prepare_search_run.py first.')
    latest = run_files[-1]
    return json.loads(latest.read_text())


def load_config():
    if CONFIG_PATH.exists():
        return json.loads(CONFIG_PATH.read_text())
    return {
        'backend': 'jobspy-local-adapter',
        'siteNames': ['indeed', 'linkedin', 'zip_recruiter', 'google'],
        'resultsWanted': 15,
        'freshnessHours': 720,
        'linkedinFetchDescription': False,
        'easyApply': False,
        'defaultCountryIndeed': 'france',
        'verbose': 1,
    }


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
    records = json.loads(df.to_json(orient='records', date_format='iso'))
    return records


def stub_execute(requests):
    raw_results = []
    for idx, request in enumerate(requests, start=1):
        raw_results.append({
            'request': request,
            'mode': 'stub-fallback',
            'results': [
                {
                    'job_title': request['search_term'],
                    'company_name': 'Example Corp' if idx % 2 else 'Sample Labs',
                    'job_location': request['location'],
                    'site_name': request['site_name'][0] if isinstance(request['site_name'], list) else request['site_name'],
                    'job_url': f'https://example.com/jobs/{idx}',
                    'date_posted': None,
                    'is_remote': request['is_remote'],
                    'description': f"Synthetic fallback result for {request['search_term']} in {request['location']}."
                }
            ]
        })
    return raw_results


def live_execute(requests):
    payload = []
    for request in requests:
        try:
            df = scrape_jobs(**request)
            payload.append({
                'request': request,
                'mode': 'live',
                'results': dataframe_to_records(df),
            })
        except Exception as e:
            payload.append({
                'request': request,
                'mode': 'error',
                'error': repr(e),
                'results': [],
            })
    return payload


def main():
    run = load_latest_run()
    config = load_config()
    run_id = run['runId']
    requests = build_requests(run, config)
    raw_results = live_execute(requests)

    if not any(entry.get('mode') == 'live' and entry.get('results') for entry in raw_results):
        raw_results = stub_execute(requests)
        mode = 'stub-fallback'
    else:
        mode = 'live'

    raw_payload = {
        'runId': run_id,
        'backend': 'jobspy-local-adapter',
        'mode': mode,
        'requests': requests,
        'rawResults': raw_results,
    }

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = RAW_DIR / f'{run_id}.json'
    out.write_text(json.dumps(raw_payload, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
