#!/usr/bin/env python3
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def resolve_python(repo: Path) -> str:
    env_python = os.environ.get("JOB_SEARCH_PYTHON")
    venv_python = repo / ".venv" / "bin" / "python3"
    if env_python:
        return env_python
    if venv_python.exists():
        return str(venv_python)
    return shutil.which("python3") or "python3"


def run(cmd, cwd=None):
    try:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "").strip(),
            "stderr": (proc.stderr or "").strip(),
        }
    except Exception as e:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(e)}


def main():
    repo = repo_root()
    python = resolve_python(repo)
    retrieval_script = repo / "skills" / "job-search-skill" / "scripts" / "run_jobspy_search.py"
    package_json = repo / "package.json"

    report = {
        "ok": True,
        "python": {"binary": python},
        "node": {},
        "retrieval": {"script": str(retrieval_script)},
        "rendering": {},
        "issues": [],
        "suggestedFixes": [],
    }

    py_version = run([python, "--version"])
    report["python"]["versionCheck"] = py_version
    if not py_version["ok"]:
        report["ok"] = False
        report["issues"].append("Python is not available.")
        report["suggestedFixes"].append("Install Python 3 or set JOB_SEARCH_PYTHON to a working interpreter.")

    if not retrieval_script.exists():
        report["ok"] = False
        report["issues"].append("Retrieval script is missing.")
        report["suggestedFixes"].append("Restore skills/job-search-skill/scripts/run_jobspy_search.py.")

    imports = run([python, "-c", "from jobspy import scrape_jobs; import pandas, pydantic, openpyxl; print('jobspy-ready')"], cwd=repo)
    report["retrieval"]["importsCheck"] = imports
    if not imports["ok"]:
        report["ok"] = False
        report["issues"].append("Python retrieval dependencies are not ready.")
        report["suggestedFixes"].append("Run `uv sync` in the repo root (or install jobspy, pandas, pydantic, openpyxl into the selected interpreter).")

    node_check = run(["node", "--version"])
    report["node"]["versionCheck"] = node_check
    if not node_check["ok"]:
        report["ok"] = False
        report["issues"].append("Node.js is not available.")
        report["suggestedFixes"].append("Install Node.js 20+.")

    report["node"]["packageJsonExists"] = package_json.exists()
    if not package_json.exists():
        report["ok"] = False
        report["issues"].append("package.json is missing.")

    for pkg, key in [("puppeteer", "puppeteer"), ("jsonresume-theme-even", "defaultTheme")]:
        spec = run(["node", "-e", f"console.log(require.resolve('{pkg}'))"], cwd=repo)
        report["rendering"][key] = spec
        if not spec["ok"]:
            report["ok"] = False
            report["issues"].append(f"Node dependency not resolvable: {pkg}.")
            report["suggestedFixes"].append("Run `npm install` in the repo root.")

    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
