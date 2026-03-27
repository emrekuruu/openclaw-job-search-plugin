#!/usr/bin/env python3
import csv
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_CONFIG = PROJECT_ROOT / 'config/runtime.json'


def load_runtime_config():
    if not RUNTIME_CONFIG.exists():
        raise SystemExit(f'Runtime config not found: {RUNTIME_CONFIG}')
    return json.loads(RUNTIME_CONFIG.read_text())


def main():
    runtime = load_runtime_config()
    output_base = Path(runtime['outputBase'])
    jobs_dir = output_base / 'jobs'
    reviews_dir = output_base / 'reviews'
    exports_dir = output_base / 'exports'
    exports_dir.mkdir(parents=True, exist_ok=True)

    review_files = sorted(reviews_dir.glob('*.scored.json'))
    job_files = sorted(jobs_dir.glob('*.json'))

    source_file = review_files[-1] if review_files else (job_files[-1] if job_files else None)
    if source_file is None:
        raise SystemExit('No job or scored review files found to export.')

    jobs = json.loads(source_file.read_text())
    run_id = source_file.stem.replace('.scored', '')

    fields = ['title', 'company', 'location', 'workMode', 'source', 'postedDate', 'fitScore', 'preferredCompany', 'fitReasons', 'url', 'summary']
    csv_path = exports_dir / f'{run_id}.csv'
    latest_path = exports_dir / 'latest.csv'

    with csv_path.open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for job in jobs:
            row = {k: job.get(k) for k in fields}
            if isinstance(row.get('fitReasons'), list):
                row['fitReasons'] = ' | '.join(row['fitReasons'])
            writer.writerow(row)

    latest_path.write_text(csv_path.read_text())
    print(csv_path)


if __name__ == '__main__':
    main()
