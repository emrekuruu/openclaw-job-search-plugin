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
    run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir()) if runs_dir.exists() else []
    if run_dirs:
        latest = run_dirs[-1]
        plan_path = latest / 'plan.json'
        if not plan_path.exists():
            raise SystemExit(f'Latest run directory is missing plan.json: {latest}')
        return json.loads(plan_path.read_text())

    legacy_run_files = sorted(runs_dir.glob('*.json')) if runs_dir.exists() else []
    if legacy_run_files:
        return json.loads(legacy_run_files[-1].read_text())

    raise SystemExit('No search runs found. Run prepare_search_run.py first.')


def load_search_config(runtime):
    config_path = Path(runtime['searchDefaultsPath'])
    if not config_path.exists():
        raise SystemExit(f'Search defaults config not found: {config_path}')
    return json.loads(config_path.read_text())


def merge_retrieval_filters(run, config):
    filters = {}
    filters.update(config or {})
    filters.update(run.get('retrievalFilters') or {})
    return filters


def build_requests(run, config):
    queries = run.get('queries') or []
    if not queries:
        raise SystemExit('Search run contains no explicit queries. Run prepare_search_run.py again after fixing profile inference.')

    filters = merge_retrieval_filters(run, config)
    work_modes = set(v.lower() for v in run.get('workModes', []))
    max_results = (run.get('qualityRules') or {}).get('maxResultsPerQuery') or filters['resultsWanted']
    requests = []
    for query in queries[: (run.get('qualityRules') or {}).get('maxQueries', len(queries))]:
        request = {
            'search_term': query['searchTerm'],
            'location': query['location'],
            'site_name': filters['siteNames'],
            'results_wanted': min(max_results, filters['resultsWanted']),
            'hours_old': filters.get('hoursOld', filters.get('freshnessHours')),
            'is_remote': filters.get('isRemote', 'remote' in work_modes),
            'easy_apply': filters['easyApply'],
            'linkedin_fetch_description': filters['linkedinFetchDescription'],
            'country_indeed': filters['defaultCountryIndeed'],
            'verbose': filters['verbose'],
        }
        if filters.get('jobType'):
            request['job_type'] = filters['jobType']
        if filters.get('distance') is not None:
            request['distance'] = filters['distance']
        if filters.get('linkedinCompanyIds'):
            request['linkedin_company_ids'] = filters['linkedinCompanyIds']
        if filters.get('offset'):
            request['offset'] = filters['offset']
        if filters.get('userAgent'):
            request['user_agent'] = filters['userAgent']
        requests.append(request)
    return requests


def dataframe_to_records(df):
    if df is None:
        return []
    return json.loads(df.to_json(orient='records', date_format='iso'))


def live_execute(run, requests):
    payload = []
    failures = []
    queries = run.get('queries') or []
    for index, request in enumerate(requests):
        query = queries[index] if index < len(queries) else {}
        try:
            df = scrape_jobs(**request)
            payload.append({
                'query': query,
                'request': request,
                'mode': 'live',
                'results': dataframe_to_records(df),
            })
        except Exception as e:
            failures.append({'request': request, 'error': repr(e)})
            payload.append({
                'query': query,
                'request': request,
                'mode': 'error',
                'error': repr(e),
                'results': [],
            })

    if not any(entry.get('mode') == 'live' and entry.get('results') for entry in payload):
        raise SystemExit(f'Live job search failed or returned no results for all requests: {failures}')

    return payload, failures


def resolve_artifact_paths(run, output_base: Path):
    artifacts = run.get('artifacts') or {}
    run_id = run['runId']
    run_dir = Path(artifacts.get('runDir') or (output_base / 'search-runs' / run_id))
    return {
        'runDir': run_dir,
        'planPath': Path(artifacts.get('planPath') or (run_dir / 'plan.json')),
        'rawResultsPath': Path(artifacts.get('rawResultsPath') or (run_dir / 'raw-results.json')),
    }


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    runs_dir = output_base / 'search-runs'

    run = load_latest_run(runs_dir)
    config = load_search_config(runtime)
    requests = build_requests(run, config)
    raw_results, failures = live_execute(run, requests)
    artifact_paths = resolve_artifact_paths(run, output_base)

    raw_payload = {
        'runId': run['runId'],
        'backend': 'jobspy-project-adapter',
        'mode': 'live',
        'candidateModel': run.get('candidateModel', {}),
        'retrievalFilters': run.get('retrievalFilters', {}),
        'queries': run.get('queries', []),
        'requests': requests,
        'rawResults': raw_results,
        'failures': failures,
    }

    artifact_paths['runDir'].mkdir(parents=True, exist_ok=True)
    artifact_paths['rawResultsPath'].write_text(json.dumps(raw_payload, indent=2) + '\n')
    print(artifact_paths['rawResultsPath'])


if __name__ == '__main__':
    main()
