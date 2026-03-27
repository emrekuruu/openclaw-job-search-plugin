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


def test_skill_local_paths_are_used():
    assert mod.SKILL_ROOT.name == 'job-search-skill'
    assert mod.PROFILE.as_posix().endswith('skills/job-search-skill/data/profiles/sample-software-engineer-profile.md')
