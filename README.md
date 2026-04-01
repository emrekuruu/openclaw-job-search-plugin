# Job Search for OpenClaw

An OpenClaw plugin for running a structured AI-assisted job search workflow.

It helps you:
- search for jobs with JobSpy
- evaluate listings with OpenClaw agents
- generate tailored resumes per listing
- render resumes PDF

This plugin is for people who want an autonomous job-search pipeline inside OpenClaw instead of a messy mix of notes, links, and one-off prompts.

## What it does

The plugin provides tools for the key workflow steps:
- prepare a search run
- check that the Python search worker is ready
- run job retrieval
- prepare canonical resume output paths
- import generated JSON Resume files
- render resumes to HTML/PDF
- export results to Excel

In practice, the workflow looks like this:
1. prepare a run for a profile
2. retrieve listings
3. review or evaluate the results with OpenClaw
4. generate tailored resumes for strong matches
5. render resumes to shareable files
6. export the scored run to `.xlsx`



## Install

Install the plugin in OpenClaw:

```bash
openclaw plugins install @emrekuruu/job-search
openclaw plugins enable job-search
```

Then verify the install:

```bash
openclaw plugins inspect job-search --json
openclaw plugins doctor
```

## Required setup

This plugin depends on both Node.js packages and a Python environment.

### 1) JavaScript dependencies

From the plugin directory, install Node dependencies:

```bash
npm install
```

These are used for:
- Excel export
- JSON Resume rendering
- PDF generation

### 2) Python worker setup

Job retrieval uses a Python worker.

Recommended setup:

```bash
uv sync
```

If you prefer, you can also point the plugin at a custom Python interpreter with:

```bash
export JOB_SEARCH_PYTHON=/path/to/python3
```

The worker checks for the required packages before running retrieval.

### 3) Readiness check

Before your first real run, verify the worker:

```text
job_search_check_worker
```

If resume rendering matters for your workflow, also verify the renderer:

```text
job_search_check_resume_renderer
```

## Basic workflow

A typical user flow is:

### Step 1: Prepare a run

Create a run using your profile file:

```text
job_search_prepare_run
```

You will provide a `profilePath`, and optionally a custom `runId`, candidate understanding, or search queries.

### Step 2: Retrieve listings

Run search retrieval:

```text
job_search_run_retrieval
```

This collects job listings and stores them under the run's artifact directory.

### Step 3: Review and evaluate

Use OpenClaw to evaluate which jobs are worth pursuing.

Common pattern:
- drop weak matches
- keep strong matches
- mark uncertain ones as maybe

### Step 4: Generate tailored resumes

For good matches, create one JSON Resume per listing.

You can ask the plugin for the canonical output location first:

```text
job_search_prepare_resume_path
```

If your resume JSON was generated elsewhere, import it:

```text
job_search_import_resume_json
```

### Step 5: Render resumes

Render the JSON Resume files into HTML, PDF, or both:

```text
job_search_render_resumes
```

### Step 6: Export results

Export the run to Excel:

```text
job_search_export_run
```

## Output files

The plugin stores artifacts in OpenClaw's state directory so your runs stay organized.

Typical outputs include:
- search metadata for the run
- individual listing JSON files
- evaluation results
- generated resume JSON files
- rendered HTML resumes
- rendered PDF resumes
- Excel exports

This makes it easier to:
- revisit a previous run
- compare shortlisted roles
- keep tailored resumes tied to specific listings

## Configuration

The plugin supports a small number of user-facing config options:

- `evaluationConcurrency` — maximum number of evaluation subagents to run in parallel
- `evaluationModel` — optional model override for evaluator agents
- `defaultResumeTheme` — default JSON Resume theme used during rendering

If you use resume rendering regularly, setting a preferred `defaultResumeTheme` is worth it.

## What makes a good result with this plugin

You will get the best results if you:
- provide a solid profile/resume input
- use clear search queries
- let OpenClaw evaluate fit instead of overfiltering too early
- generate tailored resumes only for the strongest listings
- export and review results after each run

In other words: broad retrieval first, smart filtering second.

