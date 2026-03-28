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


def normalize_record(raw, run_id):
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


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    raw_dir = output_base / 'raw'
    jobs_dir = output_base / 'jobs'
    job_listings_dir = output_base / 'job-listings'
    runs_dir = output_base / 'search-runs'

    raw_files = sorted(raw_dir.glob('*.json'))
    if not raw_files:
        raise SystemExit('No raw backend outputs found. Run search_backend_jobspy.py first.')
    latest_raw = raw_files[-1]
    payload = json.loads(latest_raw.read_text())
    run_id = payload['runId']
    candidate_model = payload.get('candidateModel') or {}

    normalized = []
    rejected = []
    seen = set()
    for entry in payload.get('rawResults', []):
        for item in entry.get('results', []):
            normalized_item = normalize_record(item, run_id)
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
                })
                continue
            normalized.append(normalized_item)

    jobs_dir.mkdir(parents=True, exist_ok=True)
    out = jobs_dir / f'{run_id}.json'
    out.write_text(json.dumps(normalized, indent=2) + '\n')

    per_listing_dir = job_listings_dir / run_id
    per_listing_dir.mkdir(parents=True, exist_ok=True)
    for item in normalized:
        listing_path = per_listing_dir / f"{item['id']}.json"
        listing_path.write_text(json.dumps(item, indent=2) + '\n')

    rejected_out = jobs_dir / f'{run_id}.rejected.json'
    rejected_out.write_text(json.dumps(rejected, indent=2) + '\n')

    run_path = runs_dir / f'{run_id}.json'
    if run_path.exists():
        run = json.loads(run_path.read_text())
        run['resultCount'] = len(normalized)
        run['rejectedCount'] = len(rejected)
        run['jobListingsPath'] = str(per_listing_dir)
        run_path.write_text(json.dumps(run, indent=2) + '\n')

    print(out)


if __name__ == '__main__':
    main()
