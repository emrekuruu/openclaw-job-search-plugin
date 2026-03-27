from pathlib import Path
import importlib.util

SCRIPT = Path('/Users/emrekuru/Developer/job-search-bot/skills/job-search-skill/scripts/prepare_search_run.py')
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


def test_project_root_and_runtime_config_paths_are_used():
    assert mod.SKILL_ROOT.name == 'job-search-skill'
    assert mod.PROJECT_ROOT.name == 'job-search-bot'
    assert mod.RUNTIME_CONFIG.as_posix().endswith('job-search-bot/config/runtime.json')
