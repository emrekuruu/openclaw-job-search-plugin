#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime
from pathlib import Path


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


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'search'


def extract_nested_list(lines, section_heading, subsection_label):
    values = []
    in_section = False
    in_subsection = False
    for line in lines:
        if line.startswith('## '):
            in_section = (line.strip() == section_heading)
            in_subsection = False
            continue
        if not in_section:
            continue
        stripped = line.rstrip()
        if stripped.strip().startswith(f'- {subsection_label}:'):
            in_subsection = True
            continue
        if in_subsection:
            if stripped.strip().startswith('- ') and not stripped.startswith('  - '):
                break
            if stripped.startswith('  - '):
                values.append(stripped.strip()[2:].strip())
    return values


def extract_section_bullets(lines, section_heading):
    values = []
    in_section = False
    for line in lines:
        if line.startswith('## '):
            in_section = (line.strip() == section_heading)
            continue
        if in_section and line.strip().startswith('- '):
            values.append(line.strip()[2:].strip())
    return values


def infer_candidate_model(profile_path: Path):
    content = profile_path.read_text()
    lines = content.splitlines()
    desired_roles = extract_nested_list(lines, '## Target Direction', 'Desired roles')
    target_companies = extract_section_bullets(lines, '## Target Companies')
    preferred_locations = extract_nested_list(lines, '## Preferences', 'Preferred locations')
    work_modes = extract_nested_list(lines, '## Preferences', 'Work modes')
    experience = extract_section_bullets(lines, '## Experience Summary')
    notes = '\n'.join(lines).lower()

    seniority = 'junior'
    if 'recently graduated' in notes or 'early-career' in notes or 'intern' in notes:
        seniority = 'junior'

    domain_focus = []
    for term in ['banking technology', 'fintech', 'software', 'mobility technology', 'saas']:
        if term in notes:
            domain_focus.append(term)

    tech_focus = []
    for term in ['java', 'spring boot', 'react', 'python', 'postgresql', 'django']:
        if term in notes:
            tech_focus.append(term)

    avoid = ['senior', 'staff', 'lead', 'principal', 'manager', 'qa-only', 'support-only']

    return {
        'desiredRoles': desired_roles,
        'targetCompanies': target_companies,
        'locations': preferred_locations,
        'workModes': work_modes,
        'experienceSummary': experience,
        'seniority': seniority,
        'domainFocus': domain_focus,
        'techFocus': tech_focus,
        'avoid': avoid,
    }


def build_search_plan(run_id: str, profile_path: Path, model: dict):
    location = model['locations'][0] if model['locations'] else 'Istanbul'
    queries = []

    core_roles = []
    for role in model['desiredRoles']:
        role_lower = role.lower()
        if 'junior' in role_lower:
            core_roles.append(role)
        elif any(x in role_lower for x in ['software engineer', 'backend engineer', 'full stack', 'java developer', 'python developer']):
            core_roles.append(role)

    seen = set()
    def add_query(kind, search_term, reason):
        key = (kind, search_term.lower(), location.lower())
        if key in seen:
            return
        seen.add(key)
        queries.append({
            'kind': kind,
            'searchTerm': search_term,
            'location': location,
            'reason': reason,
        })

    for role in core_roles[:4]:
        if model['seniority'] == 'junior' and 'junior' not in role.lower() and 'graduate' not in role.lower():
            add_query('role-core', f'Junior {role}', 'Junior-focused variant based on candidate seniority')
        add_query('role-core', role, 'Core role directly aligned with desired role family')

    if 'java' in model['techFocus']:
        add_query('role-tech', 'Java Spring Boot Developer', 'Strong match to backend banking-tech experience')
    if 'python' in model['techFocus']:
        add_query('role-tech', 'Python Software Engineer', 'Relevant technical direction from profile')
    if 'react' in model['techFocus']:
        add_query('role-tech', 'React Full Stack Developer', 'Relevant full-stack/frontend signal from profile')

    for domain in model['domainFocus'][:2]:
        if domain == 'banking technology':
            add_query('domain-aware', 'banking technology software engineer', 'Banking technology background should shape search')
        elif domain == 'fintech':
            add_query('domain-aware', 'fintech software engineer', 'Fintech relevance from profile')

    for company in model['targetCompanies'][:6]:
        add_query('company-targeted', f'Software Engineer {company}', 'Preferred company should be searched directly')

    return {
        'runId': run_id,
        'profilePath': str(profile_path),
        'candidateModel': {
            'seniority': model['seniority'],
            'roleFamily': model['desiredRoles'],
            'techFocus': model['techFocus'],
            'domainFocus': model['domainFocus'],
            'preferredCompanies': model['targetCompanies'],
            'locations': model['locations'],
            'workModes': model['workModes'],
            'avoid': model['avoid'],
        },
        'queries': queries,
        'qualityRules': {
            'preferPrecisionOverRecall': True,
            'maxQueries': 12,
            'maxResultsPerQuery': 8,
            'dedupRequired': True,
        }
    }


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    profile = Path(runtime['defaultProfile'])
    output_base = Path(runtime['outputBase'])
    runs_dir = output_base / 'search-runs'
    plans_dir = output_base / 'search-plans'

    if not profile.exists():
        raise SystemExit(f'Profile not found: {profile}')

    model = infer_candidate_model(profile)
    primary_role = model['desiredRoles'][0] if model['desiredRoles'] else 'job-search'
    now = datetime.now().astimezone()
    run_id = f"{now.date().isoformat()}-{slugify(primary_role)}"

    run = {
        'runId': run_id,
        'createdAt': now.isoformat(),
        'backend': 'jobspy-project-adapter',
        'profilePath': str(profile),
        'desiredRoles': model['desiredRoles'],
        'targetCompanies': model['targetCompanies'],
        'locations': model['locations'],
        'workModes': model['workModes'],
        'freshnessWindow': '30d',
        'resultCount': 0,
        'notes': 'Prepared from project-centric runtime profile.',
        'searchPlanPath': str(plans_dir / f'{run_id}.json')
    }

    plan = build_search_plan(run_id, profile, model)

    runs_dir.mkdir(parents=True, exist_ok=True)
    plans_dir.mkdir(parents=True, exist_ok=True)
    run_out = runs_dir / f'{run_id}.json'
    plan_out = plans_dir / f'{run_id}.json'
    run_out.write_text(json.dumps(run, indent=2) + '\n')
    plan_out.write_text(json.dumps(plan, indent=2) + '\n')
    print(run_out)
    print(plan_out)


if __name__ == '__main__':
    main()
