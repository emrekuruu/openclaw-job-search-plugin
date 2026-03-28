#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime
from pathlib import Path

TITLE_BLOCKLIST = ['senior', 'sr', 'lead', 'staff', 'principal', 'manager', 'head', 'director', 'architect']
ROLE_FAMILY_BLOCKLIST = {
    'qa engineer': [r'\bqa\b', r'quality assurance', r'test engineer', r'sdet'],
    'support': [r'support engineer', r'help desk', r'technical support'],
    'designer': [r'\bdesigner\b', r'ux\b', r'ui\b'],
    'product manager': [r'product manager', r'product owner'],
    'data scientist': [r'data scientist', r'data analyst', r'bi analyst'],
}


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


def load_latest_raw_payload(runs_dir: Path):
    run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir()) if runs_dir.exists() else []
    if run_dirs:
        latest = run_dirs[-1]
        raw_path = latest / 'raw-results.json'
        plan_path = latest / 'plan.json'
        if not raw_path.exists():
            raise SystemExit('No raw backend outputs found. Run search_backend_jobspy.py first.')
        payload = json.loads(raw_path.read_text())
        run = json.loads(plan_path.read_text()) if plan_path.exists() else {'runId': latest.name}
        return latest, run, payload

    raise SystemExit('No search runs found. Run prepare_search_run.py and search_backend_jobspy.py first.')


def normalize_record(raw, run_id, query=None):
    now = datetime.now().astimezone().isoformat()
    title = raw.get('title') or raw.get('job_title') or 'Unknown Title'
    company = raw.get('company') or raw.get('company_name') or 'Unknown Company'
    location = raw.get('location') or raw.get('job_location') or 'Unknown Location'
    url = raw.get('url') or raw.get('job_url') or raw.get('job_url_direct') or ''
    source = raw.get('source') or raw.get('site') or raw.get('site_name') or 'unknown'
    summary = raw.get('summary') or raw.get('description') or raw.get('job_summary') or ''
    return {
        'id': f"{run_id}-{company}-{title}".lower().replace(' ', '-').replace('/', '-'),
        'title': title,
        'company': company,
        'location': location,
        'workMode': raw.get('workMode') or ('remote' if raw.get('is_remote') else None),
        'source': source,
        'url': url,
        'postedDate': raw.get('postedDate') or raw.get('date_posted'),
        'discoveredAt': now,
        'salary': raw.get('salary') or raw.get('min_amount'),
        'summary': summary,
        'status': 'new',
        'runId': run_id,
        'discoveryContext': {
            'queryKind': (query or {}).get('kind'),
            'querySearchTerm': (query or {}).get('searchTerm'),
            'queryLocation': (query or {}).get('location'),
            'queryReason': (query or {}).get('reason'),
        },
    }


def exceeds_experience_limit(text: str, max_years: int | None):
    if max_years is None:
        return False
    matches = re.findall(r'(\d{1,2})\+?\s+years?', text, re.IGNORECASE)
    years = [int(value) for value in matches]
    return bool(years) and max(years) > max_years


def reject_reason(item, candidate_model):
    title = (item.get('title') or '').lower()
    summary = (item.get('summary') or '').lower()

    avoid_title_patterns = candidate_model.get('avoidTitlePatterns') or TITLE_BLOCKLIST
    if any(re.search(rf'\b{re.escape(pattern)}\b', title) for pattern in avoid_title_patterns):
        return 'seniority-mismatch'

    max_years = candidate_model.get('maxAcceptedExperienceYears')
    if exceeds_experience_limit(f'{title} {summary}', max_years):
        return 'experience-mismatch'

    for avoid_family in candidate_model.get('avoidRoleFamilies', []):
        for pattern in ROLE_FAMILY_BLOCKLIST.get(avoid_family, []):
            if re.search(pattern, title):
                return 'role-family-mismatch'

    return None


def update_run_plan(plan_path: Path, run: dict, normalized_count: int, rejected_count: int, listings_dir: Path, normalized_path: Path, rejected_path: Path):
    run['resultCount'] = normalized_count
    run['rejectedCount'] = rejected_count
    run.setdefault('artifacts', {})
    run['artifacts'].update({
        'normalizedJobsPath': str(normalized_path),
        'rejectedJobsPath': str(rejected_path),
        'listingsDir': str(listings_dir),
    })
    plan_path.write_text(json.dumps(run, indent=2) + '\n')


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    runs_dir = output_base / 'search-runs'

    run_dir, run, payload = load_latest_raw_payload(runs_dir)
    run_id = payload['runId']
    candidate_model = payload.get('candidateModel') or {}

    normalized = []
    rejected = []
    seen = set()
    for entry in payload.get('rawResults', []):
        query = entry.get('query') or {}
        for item in entry.get('results', []):
            normalized_item = normalize_record(item, run_id, query=query)
            key = (normalized_item['url'] or f"{normalized_item['company']}::{normalized_item['title']}").lower()
            if key in seen:
                continue
            seen.add(key)
            reason = reject_reason(normalized_item, candidate_model)
            if reason:
                rejected.append({
                    'reason': reason,
                    'title': normalized_item['title'],
                    'company': normalized_item['company'],
                    'url': normalized_item['url'],
                    'discoveryContext': normalized_item['discoveryContext'],
                })
                continue
            normalized.append(normalized_item)

    normalized_path = run_dir / 'normalized-jobs.json'
    rejected_path = run_dir / 'rejected-jobs.json'
    listings_dir = run_dir / 'listings'
    listings_dir.mkdir(parents=True, exist_ok=True)

    normalized_path.write_text(json.dumps(normalized, indent=2) + '\n')
    rejected_path.write_text(json.dumps(rejected, indent=2) + '\n')

    for item in normalized:
        listing_path = listings_dir / f"{item['id']}.json"
        listing_path.write_text(json.dumps(item, indent=2) + '\n')

    plan_path = run_dir / 'plan.json'
    if plan_path.exists():
        update_run_plan(plan_path, run, len(normalized), len(rejected), listings_dir, normalized_path, rejected_path)

    print(normalized_path)


if __name__ == '__main__':
    main()
