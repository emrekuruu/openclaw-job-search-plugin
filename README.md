# Job Search for OpenClaw

A structured OpenClaw job-search workflow built as a **thin native plugin plus repo-owned skills**.

## What this project is

This project is split into two layers:

- **Minimal plugin entrypoint**
  - intentionally introduces no workflow helpers
  - the package capabilities live under skills, scripts, and references
- **Skills**
  - own retrieval logic, environment checks, listing evaluation guidance, and resume-generation guidance

That split keeps the plugin small and install-friendly while letting the workflow still use Python and richer operational scripts through skills.

## What it helps with

- prepare organized job-search runs
- retrieve listings with JobSpy through skill scripts
- evaluate listings with OpenClaw agents
- generate tailored JSON Resume files
- render resumes to PDF
- export reviewed results to Excel

## Main skills

### `environment-check`
Use this first when setup or runtime readiness is unclear.

Checks:
- Python availability
- JobSpy dependencies
- Node dependencies
- Puppeteer availability
- resume theme resolution

### `job-search-skill`
Owns:
- candidate understanding
- query planning
- run preparation
- retrieval filters
- Python retrieval execution through skill scripts

### `job-listing-evaluation-skill`
Owns:
- one-listing evaluation logic
- keep / maybe / drop decisions
- normalized scoring output
- deterministic evaluation artifact writing

### `job-resume-generation-skill`
Owns:
- truthful moderate tailoring
- JSON Resume generation for selected listings
- PDF-render step for selected resumes

## Bundled skills own the capabilities

This package is now explicitly skills-first.

The plugin bundles its skills through `openclaw.plugin.json`, and OpenClaw should load them as bundled plugin skills when the plugin is enabled.

Deterministic operations live under each skill's `scripts/` folder rather than in the plugin entrypoint.

## Typical workflow

1. Run the environment check skill if setup is uncertain.
2. Use the job search skill to:
   - read the profile
   - prepare queries
   - prepare the run via the skill-owned script
   - execute retrieval via the Python script
3. Evaluate listings with the evaluation skill.
4. Generate tailored JSON Resume files with the resume-generation skill.
5. As part of that resume workflow, render selected resumes to PDF.
6. Write evaluation and export artifacts through the skill-owned scripts.

## Install

```bash
openclaw plugins install @emrekuruu/job-search
openclaw plugins enable job-search
```

Then inside the repo:

```bash
npm install
uv sync
```

## Why it is structured this way

The project intentionally moves operational logic into bundled skills and skill scripts/references, leaving the plugin index as thin as possible.

This gives you:
- a cleaner native plugin surface
- easier skill iteration
- Python retrieval without stuffing process-launch logic into the plugin layer
