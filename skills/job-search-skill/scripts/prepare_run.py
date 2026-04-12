#!/usr/bin/env python3
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-') or 'run'


def now_stamp() -> str:
    return datetime.now().strftime('%Y-%m-%d-%H%M%S')


def state_dir() -> Path:
    root = os.environ.get('OPENCLAW_STATE_DIR')
    if not root:
        raise SystemExit('OPENCLAW_STATE_DIR is not set')
    return Path(root).expanduser().resolve() / 'plugin-runtimes' / 'job-search'


def ensure(path: Path):
    path.mkdir(parents=True, exist_ok=True)


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: prepare_run.py <input-json>')

    payload = json.loads(Path(sys.argv[1]).read_text())
    profile_path = Path(payload['profilePath']).expanduser().resolve()
    if not profile_path.exists():
        raise SystemExit(f'Candidate profile does not exist: {profile_path}')

    run_id = payload.get('runId') or f"{now_stamp()}-{slugify(profile_path.stem)}"
    base = state_dir()
    run_dir = base / 'search-runs' / run_id
    listings_dir = run_dir / 'listings'
    resumes_dir = base / 'resumes' / run_id
    evaluations_dir = base / 'evaluations' / run_id
    exports_dir = base / 'exports'
    search_path = run_dir / 'search.json'

    ensure(listings_dir)
    ensure(resumes_dir)
    ensure(evaluations_dir)
    ensure(exports_dir)

    search = {
        'runId': run_id,
        'profilePath': str(profile_path),
        'candidateUnderstanding': payload.get('candidateUnderstanding', {}),
        'queries': payload.get('queries', []),
        'status': 'draft',
        'artifacts': {
            'stateDir': str(base),
            'runDir': str(run_dir),
            'searchPath': str(search_path),
            'listingsDir': str(listings_dir),
            'evaluationsDir': str(evaluations_dir),
            'resumesDir': str(resumes_dir),
            'exportsDir': str(exports_dir),
        },
    }
    search_path.write_text(json.dumps(search, indent=2) + '\n')
    print(json.dumps({
        'runId': run_id,
        'searchPath': str(search_path),
        'listingsDir': str(listings_dir),
        'resumesDir': str(resumes_dir),
        'evaluationsDir': str(evaluations_dir),
        'exportsDir': str(exports_dir),
    }, indent=2))


if __name__ == '__main__':
    main()
