#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path


def evaluations_dir(run_id: str) -> Path:
    root = os.environ.get('OPENCLAW_STATE_DIR')
    if not root:
        raise SystemExit('OPENCLAW_STATE_DIR is not set')
    path = Path(root).expanduser().resolve() / 'plugin-runtimes' / 'job-search' / 'evaluations' / run_id
    path.mkdir(parents=True, exist_ok=True)
    return path


def main():
    if len(sys.argv) != 2:
        raise SystemExit('Usage: write_evaluation.py <input-json>')
    payload = json.loads(Path(sys.argv[1]).read_text())
    run_id = payload['runId']
    listing_id = payload['listingId']
    out = evaluations_dir(run_id) / f'{listing_id}.json'
    out.write_text(json.dumps(payload, indent=2) + '\n')
    print(json.dumps({'outputPath': str(out)}, indent=2))


if __name__ == '__main__':
    main()
