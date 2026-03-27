from pathlib import Path
import importlib.util

SCRIPT = Path('/Users/emrekuru/Developer/job-search-bot/skills/job-search-skill/scripts/render_search_summary.py')
spec = importlib.util.spec_from_file_location('render_search_summary', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_project_runtime_config_path_is_used():
    assert mod.RUNTIME_CONFIG.as_posix().endswith('job-search-bot/config/runtime.json')
