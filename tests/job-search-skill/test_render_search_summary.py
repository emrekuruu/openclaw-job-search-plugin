from pathlib import Path
import importlib.util

SCRIPT = Path('/Users/emrekuru/Developer/job-search-bot/skills/job-search-skill/scripts/render_search_summary.py')
spec = importlib.util.spec_from_file_location('render_search_summary', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_module_paths_are_defined():
    assert mod.RUNS_DIR.name == 'search-runs'
    assert mod.JOBS_DIR.name == 'jobs'
