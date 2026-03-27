from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[2] / 'scripts/export_jobs_csv.py'
spec = importlib.util.spec_from_file_location('export_jobs_csv', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_runtime_config_path_builder():
    root = Path('/tmp/project-root')
    assert mod.runtime_config_path(root).as_posix() == '/tmp/project-root/config/runtime.json'
