#!/usr/bin/env python3
import json
import os
import re
from datetime import datetime
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
SKILL_ROOT = SCRIPT_PATH.parents[1]


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
    primary_role = desired_roles[0] if desired_roles else 'job-search'
    now = datetime.now().astimezone()
    run_id = f"{now.date().isoformat()}-{slugify(primary_role)}"

    run = {
        'runId': run_id,
        'createdAt': now.isoformat(),
        'backend': 'jobspy-project-adapter',
        'profilePath': str(profile),
        'desiredRoles': desired_roles,
        'targetCompanies': target_companies,
        'locations': preferred_locations,
        'workModes': work_modes,
        'freshnessWindow': '30d',
        'resultCount': 0,
        'notes': 'Prepared from project-centric runtime profile.'
    }

    runs_dir.mkdir(parents=True, exist_ok=True)
    out = runs_dir / f'{run_id}.json'
    out.write_text(json.dumps(run, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
