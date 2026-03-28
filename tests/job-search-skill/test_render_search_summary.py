from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/job-search-skill/scripts/render_search_summary.py'
spec = importlib.util.spec_from_file_location('render_search_summary', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_load_latest_run_dir_requires_directory(tmp_path):
    try:
        mod.load_latest_run_dir(tmp_path)
        assert False, 'expected SystemExit'
    except SystemExit:
        pass


def test_runtime_config_path_builder():
    root = Path('/tmp/project-root')
    assert mod.runtime_config_path(root).as_posix() == '/tmp/project-root/config/runtime.json'
