#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]

SENIORITY_PATTERNS = {
    'junior': [r'\bjunior\b', r'\bentry[- ]level\b', r'\bnew grad\b', r'\bintern(ship)?\b'],
    'mid': [r'\bmid\b', r'\bmid[- ]level\b'],
    'senior': [r'\bsenior\b', r'\bsr\.?\b', r'\blead\b', r'\bstaff\b', r'\bprincipal\b', r'\bmanager\b'],
}
ROLE_KEYWORDS = {
    'software engineer': [r'software engineer', r'software developer', r'application developer'],
    'backend engineer': [r'backend engineer', r'backend developer', r'java developer', r'python developer'],
    'full stack engineer': [r'full stack', r'fullstack'],
    'frontend engineer': [r'frontend engineer', r'front[- ]end engineer', r'frontend developer', r'front[- ]end developer'],
    'mobile engineer': [r'android developer', r'ios developer', r'mobile developer', r'mobile engineer'],
    'data engineer': [r'data engineer'],
}
AVOID_ROLE_FAMILY_KEYWORDS = {
    'qa engineer': [r'\bqa\b', r'quality assurance', r'test engineer', r'sdet'],
    'support': [r'support engineer', r'help desk', r'customer support', r'technical support'],
    'designer': [r'\bdesigner\b', r'ux\b', r'ui\b', r'product design'],
    'product manager': [r'product manager', r'product owner'],
    'data scientist': [r'data scientist', r'data analyst', r'bi analyst'],
}
TITLE_AVOID_PATTERNS = ['senior', 'sr', 'lead', 'staff', 'principal', 'manager', 'head', 'director', 'architect']
TECH_TERMS = ['python', 'java', 'spring', 'spring boot', 'react', 'node', 'node.js', 'typescript', 'javascript', 'aws', 'sql', 'postgres', 'docker', 'kubernetes']
DOMAIN_TERMS = ['fintech', 'banking', 'payments', 'e-commerce', 'healthtech', 'saas', 'ai', 'machine learning']
WORK_MODE_TERMS = ['remote', 'hybrid', 'on-site', 'onsite', 'on premise']
EMPLOYMENT_INTENT_PATTERNS = {
    'internship': [r'\bintern(ship)?\b', r'\bplacement\b', r'\bco-?op\b', r'\bstudent\b'],
    'junior-fulltime': [r'\bjunior\b', r'\bentry[- ]level\b', r'\bgraduate role\b', r'\bnew grad\b'],
    'contract': [r'\bcontract\b', r'\bfreelance\b', r'\bconsult(ing|ant)?\b'],
}
EMPLOYMENT_INTENT_TO_JOB_TYPE = {
    'internship': 'internship',
    'junior-fulltime': 'fulltime',
    'fulltime': 'fulltime',
    'contract': 'contract',
}
SENIORITY_TO_MAX_DISTANCE = {
    'junior': 25,
    'mid': 40,
    'senior': 50,
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


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'search'


def extract_nested_list(lines: Iterable[str], section_heading: str, subsection_label: str):
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


def extract_section_bullets(lines: Iterable[str], section_heading: str):
    values = []
    in_section = False
    for line in lines:
        if line.startswith('## '):
            in_section = (line.strip() == section_heading)
            continue
        if in_section and line.strip().startswith('- '):
            values.append(line.strip()[2:].strip())
    return values


def unique_preserve(values):
    seen = set()
    ordered = []
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(normalized)
    return ordered


def first_years_of_experience(text: str):
    match = re.search(r'(\d{1,2})\+?\s+years?\s+of\s+experience', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    match = re.search(r'(\d{1,2})\+?\s+years?\b', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


def infer_seniority(text: str, experience_years: int | None):
    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in SENIORITY_PATTERNS['senior']):
        return 'senior', 'high'
    if any(re.search(pattern, lowered) for pattern in SENIORITY_PATTERNS['junior']):
        return 'junior', 'high'
    if experience_years is not None:
        if experience_years <= 2:
            return 'junior', 'medium'
        if experience_years <= 5:
            return 'mid', 'medium'
        return 'senior', 'medium'
    return None, 'low'


def infer_role_family(text: str, desired_roles):
    haystacks = desired_roles + [text]
    matches = []
    for role_family, patterns in ROLE_KEYWORDS.items():
        if any(re.search(pattern, haystack, re.IGNORECASE) for haystack in haystacks for pattern in patterns):
            matches.append(role_family)
    return unique_preserve(matches)


def infer_avoid_role_families(text: str, role_family):
    avoids = []
    for avoid_family, patterns in AVOID_ROLE_FAMILY_KEYWORDS.items():
        if role_family and avoid_family in role_family:
            continue
        if any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns):
            continue
        avoids.append(avoid_family)
    return unique_preserve(avoids)


def collect_terms(text: str, vocabulary):
    lowered = text.lower()
    found = [term for term in vocabulary if term in lowered]
    return unique_preserve(found)


def guess_locations(preferred_locations, text: str):
    if preferred_locations:
        return unique_preserve(preferred_locations)
    matches = re.findall(r'\b(?:in|at|location:?|based in)\s+([A-Z][A-Za-zİıŞşĞğÜüÖöÇç-]+(?:\s+[A-Z][A-Za-zİıŞşĞğÜüÖöÇç-]+)*)', text)
    return unique_preserve(matches)


def infer_employment_intent(text: str, seniority: str):
    lowered = text.lower()
    if any(re.search(pattern, lowered) for pattern in EMPLOYMENT_INTENT_PATTERNS['internship']):
        return 'internship'
    if any(re.search(pattern, lowered) for pattern in EMPLOYMENT_INTENT_PATTERNS['contract']):
        return 'contract'
    if seniority == 'junior':
        return 'junior-fulltime'
    return 'contract' if seniority == 'senior' and 'contract' in lowered else 'fulltime'


def derive_core_queries(role_families, tech_focus, preferred_companies, locations, seniority):
    if not role_families:
        raise SystemExit('Could not infer a target role family from the candidate profile. Refine the profile before retrieval.')

    primary_role = role_families[0]
    seniority_prefix = 'Junior ' if seniority == 'junior' else ''
    base_titles = [f'{seniority_prefix}{primary_role.title()}'.strip()]
    if primary_role == 'software engineer':
        base_titles.append(f'{seniority_prefix}Software Developer'.strip())
    if primary_role == 'backend engineer':
        base_titles.append(f'{seniority_prefix}Backend Developer'.strip())

    if tech_focus:
        preferred_stack = tech_focus[:2]
        base_titles.extend([f"{' '.join(term.title() for term in preferred_stack)} {primary_role.title()}".strip()])

    locations = locations[:2] or ['Remote']
    queries = []
    for title in unique_preserve(base_titles)[:3]:
        for location in locations:
            queries.append({
                'kind': 'role-core' if title == base_titles[0] else 'role-tech',
                'searchTerm': title,
                'location': location,
                'reason': f'Candidate target role: {primary_role}; inferred seniority: {seniority}',
            })

    for company in preferred_companies[:3]:
        queries.append({
            'kind': 'company-targeted',
            'searchTerm': f'{primary_role.title()} {company}',
            'location': locations[0],
            'reason': 'Preferred company from candidate profile',
        })

    return unique_preserve_dicts(queries)[:8]


def unique_preserve_dicts(items):
    seen = set()
    output = []
    for item in items:
        key = (item['kind'].lower(), item['searchTerm'].lower(), item['location'].lower())
        if key in seen:
            continue
        seen.add(key)
        output.append(item)
    return output


def build_candidate_model(profile_text: str, lines, desired_roles, target_companies, preferred_locations, work_modes):
    experience_years = first_years_of_experience(profile_text)
    seniority, confidence = infer_seniority(profile_text, experience_years)
    if not seniority:
        raise SystemExit('Could not infer candidate seniority from the profile. Add explicit experience or level signals before retrieval.')

    role_family = infer_role_family(profile_text, desired_roles)
    if not role_family:
        raise SystemExit('Could not infer the candidate role family from the profile. Add explicit desired roles before retrieval.')

    locations = guess_locations(preferred_locations, profile_text)
    work_modes = unique_preserve(work_modes or collect_terms(profile_text, WORK_MODE_TERMS))
    tech_focus = collect_terms(profile_text, TECH_TERMS)
    domain_focus = collect_terms(profile_text, DOMAIN_TERMS)
    preferred_companies = unique_preserve(target_companies)
    max_accepted_experience_years = 3 if seniority == 'junior' else 5 if seniority == 'mid' else 8
    employment_intent = infer_employment_intent(profile_text, seniority)
    retrieval_filters = {
        'siteNames': ['linkedin'],
        'isRemote': 'remote' in [mode.lower() for mode in work_modes],
        'jobType': EMPLOYMENT_INTENT_TO_JOB_TYPE.get(employment_intent, 'fulltime'),
        'employmentIntent': employment_intent,
        'distance': SENIORITY_TO_MAX_DISTANCE.get(seniority, 50),
        'easyApply': False,
        'hoursOld': 24 * 30,
        'linkedinFetchDescription': True,
    }

    return {
        'seniority': seniority,
        'confidence': confidence,
        'roleFamily': role_family,
        'experienceYears': experience_years,
        'techFocus': tech_focus,
        'domainFocus': domain_focus,
        'preferredCompanies': preferred_companies,
        'locations': locations,
        'workModes': work_modes,
        'avoidTitlePatterns': TITLE_AVOID_PATTERNS,
        'avoidRoleFamilies': infer_avoid_role_families(profile_text, role_family),
        'maxAcceptedExperienceYears': max_accepted_experience_years,
        'retrievalFilters': retrieval_filters,
    }


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    profile = Path(runtime['defaultProfile'])
    runs_dir = Path(runtime['outputBase']) / 'search-runs'

    if not profile.exists():
        raise SystemExit(f'Profile not found: {profile}')

    content = profile.read_text()
    lines = content.splitlines()

    desired_roles = extract_nested_list(lines, '## Target Direction', 'Desired roles')
    target_companies = extract_section_bullets(lines, '## Target Companies')
    preferred_locations = extract_nested_list(lines, '## Preferences', 'Preferred locations')
    work_modes = extract_nested_list(lines, '## Preferences', 'Work modes')

    candidate_model = build_candidate_model(content, lines, desired_roles, target_companies, preferred_locations, work_modes)
    queries = derive_core_queries(
        role_families=candidate_model['roleFamily'],
        tech_focus=candidate_model['techFocus'],
        preferred_companies=candidate_model['preferredCompanies'],
        locations=candidate_model['locations'],
        seniority=candidate_model['seniority'],
    )
    if not queries:
        raise SystemExit('Search plan generation produced no queries. Refine the profile before retrieval.')

    primary_role = candidate_model['roleFamily'][0]
    now = datetime.now().astimezone()
    run_id = f"{now.date().isoformat()}-{slugify(primary_role)}"

    run = {
        'runId': run_id,
        'createdAt': now.isoformat(),
        'backend': 'jobspy-project-adapter',
        'profilePath': str(profile),
        'desiredRoles': desired_roles,
        'targetCompanies': target_companies,
        'locations': candidate_model['locations'],
        'workModes': candidate_model['workModes'],
        'freshnessWindow': '30d',
        'resultCount': 0,
        'rejectedCount': 0,
        'candidateModel': candidate_model,
        'retrievalFilters': candidate_model['retrievalFilters'],
        'queries': queries,
        'qualityRules': {
            'preferPrecisionOverRecall': True,
            'maxQueries': 8,
            'maxResultsPerQuery': 12,
            'dedupRequired': True,
            'rejectObviousSeniorityMismatch': True,
            'rejectObviousRoleFamilyMismatch': True,
            'rejectExperienceMismatch': True,
        },
        'notes': 'Prepared from candidate-aware profile inference. Retrieval only; no evaluation fallback.',
    }

    runs_dir.mkdir(parents=True, exist_ok=True)
    out = runs_dir / f'{run_id}.json'
    out.write_text(json.dumps(run, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
