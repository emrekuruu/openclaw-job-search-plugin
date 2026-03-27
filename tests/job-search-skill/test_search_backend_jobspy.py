from pathlib import Path
import importlib.util

SCRIPT = Path('/Users/emrekuru/Developer/job-search-bot/skills/job-search-skill/scripts/search_backend_jobspy.py')
spec = importlib.util.spec_from_file_location('search_backend_jobspy', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_build_requests_creates_expected_shape():
    run = {
        'desiredRoles': ['Product Manager', 'AI Product Manager'],
        'locations': ['Paris', 'Remote (Europe)'],
        'workModes': ['remote', 'hybrid'],
        'targetCompanies': ['OpenAI', 'Mistral AI', 'Datadog'],
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


def test_stub_execute_returns_results():
    requests = [{
        'search_term': 'Product Manager',
        'location': 'Paris',
        'site_name': ['indeed'],
        'is_remote': False,
    }]
    payload = mod.stub_execute(requests)
    assert len(payload) == 1
    assert payload[0]['mode'] == 'stub-fallback'
    assert payload[0]['results'][0]['job_title'] == 'Product Manager'
