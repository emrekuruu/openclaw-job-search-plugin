#!/usr/bin/env python3
import json
import subprocess
import sys
from pathlib import Path


def repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def main():
    if len(sys.argv) < 2:
        raise SystemExit('Usage: render_resume.py <resume-json-path> [theme]')

    resume_path = Path(sys.argv[1]).expanduser().resolve()
    if not resume_path.exists():
        raise SystemExit(f'Resume JSON does not exist: {resume_path}')

    theme = sys.argv[2] if len(sys.argv) > 2 else 'jsonresume-theme-even'
    repo = repo_root()
    resumed_bin = repo / 'node_modules' / '.bin' / ('resumed.cmd' if sys.platform == 'win32' else 'resumed')
    if not resumed_bin.exists():
        raise SystemExit(f'Resumed CLI not found: {resumed_bin}. Run npm install in the repo root.')

    pdf_path = resume_path.with_suffix('.pdf')
    cmd = [str(resumed_bin), 'export', str(resume_path), '--theme', theme, '--output', str(pdf_path)]
    proc = subprocess.run(cmd, cwd=repo, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit((proc.stderr or proc.stdout or '').strip())

    print(json.dumps({
        'resumePath': str(resume_path),
        'pdfPath': str(pdf_path),
        'theme': theme,
    }, indent=2))


if __name__ == '__main__':
    main()
