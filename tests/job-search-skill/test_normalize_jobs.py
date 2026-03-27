from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/job-search-skill/scripts/normalize_jobs.py'
spec = importlib.util.spec_from_file_location('normalize_jobs', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_normalize_record_maps_backend_fields():
    raw = {
        'job_title': 'Senior Product Manager',
        'company_name': 'Example Corp',
        'job_location': 'Paris, France',
        'site_name': 'indeed',
        'job_url': 'https://example.com/job/1',
        'date_posted': '2026-03-27T00:00:00.000',
        'is_remote': True,
        'description': 'Role summary',
    }
    result = mod.normalize_record(raw, 'run-123')
    assert result['title'] == 'Senior Product Manager'
    assert result['company'] == 'Example Corp'
    assert result['location'] == 'Paris, France'
    assert result['source'] == 'indeed'
    assert result['url'] == 'https://example.com/job/1'
    assert result['workMode'] == 'remote'
    assert result['runId'] == 'run-123'


def test_runtime_config_path_builder():
    root = Path('/tmp/project-root')
    assert mod.runtime_config_path(root).as_posix() == '/tmp/project-root/config/runtime.json'
