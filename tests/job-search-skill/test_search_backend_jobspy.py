from pathlib import Path
import importlib.util
import pytest

SCRIPT = Path('/Users/emrekuru/Developer/job-search-bot/skills/job-search-skill/scripts/search_backend_jobspy.py')
spec = importlib.util.spec_from_file_location('search_backend_jobspy', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_requests_creates_expected_shape():
    run = {
        'desiredRoles': ['Software Engineer', 'Backend Engineer'],
        'locations': ['Paris, France', 'Remote'],
        'workModes': ['remote', 'hybrid'],
        'targetCompanies': ['Datadog', 'Doctolib', 'Stripe'],
    }
    config = {
        'siteNames': ['indeed', 'linkedin'],
        'resultsWanted': 12,
        'freshnessHours': 168,
        'easyApply': False,
        'linkedinFetchDescription': False,
        'defaultCountryIndeed': 'france',
        'verbose': 1,
    }
    requests = mod.build_requests(run, config)
    assert requests
    assert all('search_term' in r for r in requests)
    assert all('location' in r for r in requests)
    assert all(r['site_name'] == ['indeed', 'linkedin'] for r in requests)


def test_load_config_requires_real_file(monkeypatch):
    monkeypatch.setattr(mod, 'CONFIG_PATH', Path('/tmp/does-not-exist.json'))
    with pytest.raises(SystemExit):
        mod.load_config()
