from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/job-search-skill/scripts/prepare_search_run.py'
spec = importlib.util.spec_from_file_location('prepare_search_run', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_slugify_basic():
    assert mod.slugify('Senior Product Manager') == 'senior-product-manager'
    assert mod.slugify('  AI / Product  ') == 'ai-product'


def test_extract_nested_list_and_section_bullets():
    lines = [
        '## Target Direction',
        '- Desired roles:',
        '  - Product Manager',
        '  - AI Product Manager',
        '- Preferred industries:',
        '  - SaaS',
        '## Target Companies',
        '- OpenAI',
        '- Mistral AI',
    ]
    assert mod.extract_nested_list(lines, '## Target Direction', 'Desired roles') == ['Product Manager', 'AI Product Manager']
    assert mod.extract_section_bullets(lines, '## Target Companies') == ['OpenAI', 'Mistral AI']


def test_runtime_config_path_builder():
    root = Path('/tmp/project-root')
    assert mod.runtime_config_path(root).as_posix() == '/tmp/project-root/config/runtime.json'


def test_derive_core_queries_contains_company_targeted_entries():
    queries = mod.derive_core_queries(
        role_families=['software engineer', 'backend engineer'],
        tech_focus=['java', 'react'],
        preferred_companies=['Akbank', 'Insider'],
        locations=['Istanbul'],
        seniority='junior',
    )
    assert queries
    assert any(q['kind'] == 'company-targeted' for q in queries)
