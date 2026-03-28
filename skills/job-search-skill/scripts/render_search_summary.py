#!/usr/bin/env python3
import json
import os
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


def load_latest_run_dir(runs_dir: Path) -> Path:
    run_dirs = sorted(path for path in runs_dir.iterdir() if path.is_dir()) if runs_dir.exists() else []
    if not run_dirs:
        raise SystemExit('No search runs found.')
    return run_dirs[-1]


def main():
    project_root = resolve_project_root()
    runtime = load_runtime_config(project_root)
    output_base = Path(runtime['outputBase'])
    runs_dir = output_base / 'search-runs'

    run_dir = load_latest_run_dir(runs_dir)
    plan_path = run_dir / 'plan.json'
    normalized_path = run_dir / 'normalized-jobs.json'
    rejected_path = run_dir / 'rejected-jobs.json'
    raw_path = run_dir / 'raw-results.json'

    if not plan_path.exists():
        raise SystemExit(f'Run plan not found: {plan_path}')

    run = json.loads(plan_path.read_text())
    run_id = run['runId']
    jobs = json.loads(normalized_path.read_text()) if normalized_path.exists() else []
    rejected = json.loads(rejected_path.read_text()) if rejected_path.exists() else []
    raw_payload = json.loads(raw_path.read_text()) if raw_path.exists() else {}
    candidate_model = run.get('candidateModel') or {}
    filters = run.get('retrievalFilters') or {}
    inference = candidate_model.get('inference') or {}

    lines = []
    lines.append(f'# Search Run Summary - {run_id}')
    lines.append('')
    lines.append('## Run Metadata')
    lines.append(f"- Run ID: `{run_id}`")
    lines.append(f"- Created at: `{run.get('createdAt')}`")
    lines.append(f"- Backend: `{run.get('backend')}`")
    lines.append(f"- Profile path: `{run.get('profilePath')}`")
    lines.append('')
    lines.append('## Candidate Inference')
    lines.append(f"- Seniority: {candidate_model.get('seniority', 'unknown')} ({candidate_model.get('confidence', 'unknown')} confidence)")
    lines.append(f"- Employment intent: {candidate_model.get('employmentIntent', 'unknown')}")
    lines.append(f"- Role family: {', '.join(candidate_model.get('roleFamily', []))}")
    lines.append(f"- Experience years: {candidate_model.get('experienceYears')}")
    lines.append(f"- Tech focus: {', '.join(candidate_model.get('techFocus', []))}")
    lines.append(f"- Domain focus: {', '.join(candidate_model.get('domainFocus', []))}")
    lines.append(f"- Inference notes: {inference.get('seniorityReason', 'n/a')} | {inference.get('employmentIntentReason', 'n/a')}")
    lines.append('')
    lines.append('## Retrieval Filters')
    for key, value in filters.items():
        lines.append(f'- {key}: {value}')
    lines.append('')
    lines.append('## Query Plan')
    lines.append(f"- Query count: {len(run.get('queries', []))}")
    for query in run.get('queries', [])[:8]:
        lines.append(f"- [{query['kind']}] {query['searchTerm']} @ {query['location']} — {query['reason']}")
    lines.append('')
    lines.append('## Retrieval Execution')
    lines.append(f"- Requests executed: {len(raw_payload.get('requests', []))}")
    lines.append(f"- Query payloads recorded in: `{raw_path}`")
    lines.append('')
    lines.append('## Results')
    lines.append(f'- Kept after normalization: {len(jobs)}')
    lines.append(f'- Rejected as obvious mismatch: {len(rejected)}')
    for job in jobs[:10]:
        context = job.get('discoveryContext') or {}
        lines.append(
            f"- KEEP: {job['title']} — {job['company']} — {job['location']} — {job['source']} "
            f"(via {context.get('querySearchTerm', 'unknown query')})"
        )
    if rejected:
        lines.append('')
        lines.append('## Rejected examples')
        for item in rejected[:10]:
            context = item.get('discoveryContext') or {}
            lines.append(
                f"- DROP: {item['title']} — {item['company']} — {item['reason']} "
                f"(via {context.get('querySearchTerm', 'unknown query')})"
            )
    lines.append('')
    lines.append('## Artifacts')
    for key, value in (run.get('artifacts') or {}).items():
        lines.append(f'- {key}: `{value}`')
    lines.append('')
    lines.append('## Notes')
    lines.append(f"- {run.get('notes', '')}")

    out = run_dir / 'summary.md'
    out.write_text('\n'.join(lines) + '\n')
    print(out)


if __name__ == '__main__':
    main()
