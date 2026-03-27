from pathlib import Path
import importlib.util
import pytest

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/job-search-skill/scripts/search_backend_jobspy.py'
spec = importlib.util.spec_from_file_location('search_backend_jobspy', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_requests_creates_expected_shape():
    run = {
        'desiredRoles': ['Software Engineer', 'Backend Engineer'],
        'locations': ['Istanbul', 'Remote'],
        'workModes': ['remote', 'hybrid'],
        'targetCompanies': ['Akbank', 'Garanti BBVA Teknoloji', 'Yapı Kredi Teknoloji'],
    }
    config = {
        'siteNames': ['linkedin'],
        'resultsWanted': 12,
        'freshnessHours': 168,
        'easyApply': False,
        'linkedinFetchDescription': True,
        'defaultCountryIndeed': 'turkey',
        'verbose': 1,
    }
    requests = mod.build_requests(run, config)
    assert requests
    assert all('search_term' in r for r in requests)
    assert all('location' in r for r in requests)
    assert all(r['site_name'] == ['linkedin'] for r in requests)


def test_load_latest_run_requires_files(tmp_path):
    with pytest.raises(SystemExit):
        mod.load_latest_run(tmp_path)


def test_runtime_config_path_builder():
    root = Path('/tmp/project-root')
    assert mod.runtime_config_path(root).as_posix() == '/tmp/project-root/config/runtime.json'
