#!/usr/bin/env python3
import json
import os
from datetime import datetime
from pathlib import Path


def resolve_project_root() -> Path:
    env_root = os.environ.get('JOB_SEARCH_BOT_ROOT')
    if not env_root:
        raise SystemExit('JOB_SEARCH_BOT_ROOT is not set.')
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
    return ''.join(ch.lower() if ch.isalnum() else '-' for ch in text).strip('-') or 'search'


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    profile_path = Path(runtime['defaultProfile'])
    if not profile_path.exists():
        raise SystemExit(f'Profile not found: {profile_path}')

    output_base = Path(runtime['outputBase'])
    runs_dir = output_base / 'search-runs'
    now = datetime.now().astimezone()
    run_id = f"{now.date().isoformat()}-{slugify(profile_path.stem)}"
    run_dir = runs_dir / run_id
    listings_dir = run_dir / 'listings'
    search_path = run_dir / 'search.json'

    run_dir.mkdir(parents=True, exist_ok=True)
    listings_dir.mkdir(parents=True, exist_ok=True)

    search = {
        'runId': run_id,
        'createdAt': now.isoformat(),
        'profilePath': str(profile_path),
        'status': 'draft',
        'instructions': {
            'agentOwnsDecisions': True,
            'noRegexExtraction': True,
            'defaultEmploymentIntent': 'full-time',
            'artifacts': {
                'searchPath': str(search_path),
                'listingsDir': str(listings_dir),
            },
        },
        'candidateUnderstanding': {},
        'queries': [],
        'notes': 'Agent-authored search plan. Fill candidateUnderstanding and queries before running JobSpy retrieval.',
    }

    search_path.write_text(json.dumps(search, indent=2) + '\n')
    print(search_path)


if __name__ == '__main__':
    main()
