#!/usr/bin/env python3
import json
import os
from pathlib import Path

from jobspy import scrape_jobs


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
    queries = run.get('queries') or []
    if not queries:
        raise SystemExit('Search run contains no explicit queries. Run prepare_search_run.py again after fixing profile inference.')

    work_modes = set(v.lower() for v in run.get('workModes', []))
    max_results = (run.get('qualityRules') or {}).get('maxResultsPerQuery') or config['resultsWanted']
    requests = []
    for query in queries[: (run.get('qualityRules') or {}).get('maxQueries', len(queries))]:
        requests.append({
            'search_term': query['searchTerm'],
            'location': query['location'],
            'site_name': config['siteNames'],
            'results_wanted': min(max_results, config['resultsWanted']),
            'hours_old': config['freshnessHours'],
            'is_remote': 'remote' in work_modes,
            'easy_apply': config['easyApply'],
            'linkedin_fetch_description': config['linkedinFetchDescription'],
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
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
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
        'candidateModel': run.get('candidateModel', {}),
        'queries': run.get('queries', []),
        'requests': requests,
        'rawResults': raw_results,
    }

    raw_dir.mkdir(parents=True, exist_ok=True)
    out = raw_dir / f'{run_id}.json'
    out.write_text(json.dumps(raw_payload, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
