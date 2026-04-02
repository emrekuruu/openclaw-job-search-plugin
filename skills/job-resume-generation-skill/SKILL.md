---
name: job-resume-generation-skill
description: Thin resume-generation skill for the job-search plugin workflow. Use when a listing has already been retrieved and evaluated as keep or maybe, and the agent should take the candidate profile plus the listing description and generate a moderately tailored JSON Resume, including ATS-aware but non-overfit rewrites of summaries and skills, ready for deterministic CLI rendering.
---

# Job Resume Generation Skill

This skill owns the resume-generation and PDF-render workflow for the later stage of the job-search pipeline.

## Workflow position

Use this after:
1. search
2. evaluate
3. select a `keep` or `maybe` listing
4. generate a tailored JSON Resume from the profile plus listing description
5. render the generated resume to PDF

This skill owns the judgment and writing guidance for converting a candidate profile plus one listing description into a truthful, moderately tailored JSON Resume, and then getting that resume rendered to PDF through the thin helper layer.

## Inputs

Canonical required inputs:
- `profilePath`: path to the candidate profile
- `listingDescription`: the job description text to tailor against

Optional inputs:
- `jobTitle`
- `company`
- `listingUrl`
- `decision`
- `score`
- `evaluationNotes`
- `listingId`
- `runId`

Do not require a retrieval artifact or listing JSON path unless some outer workflow happens to provide one. For resume generation, the profile and listing description are the real inputs that matter.

## Responsibilities

The agent using this skill should:
- read the candidate profile from the provided `profilePath`
- read the provided `listingDescription` carefully
- identify must-have and nice-to-have requirements
- identify exact keyword matches and adjacent transferable experience
- generate a moderately tailored JSON Resume that stays truthful to the profile
- strengthen summaries, bullet phrasing, and skill ordering for ATS and human readability without over-specializing the resume to one listing
- avoid fabricating experience, metrics, technologies, or seniority
- write JSON Resume output to the plugin runtime path when a runtime path is provided by the outer workflow

## Truthfulness rules

- Do not invent employers, dates, projects, metrics, certifications, degrees, or tools.
- Rephrase aggressively only within the factual boundaries of the profile.
- If the listing asks for unsupported experience, do not claim it.
- Prefer adjacent evidence and transferable outcomes over bluffing.

## Tailoring process

### 1. Build a fit map

Extract from the listing description:
- role title and scope
- core responsibilities
- required skills
- preferred skills
- domain and product signals
- seniority expectations
- location or work authorization constraints if relevant

Extract from the profile:
- strongest matching experiences
- technologies and domains
- achievements and measurable outcomes
- adjacent/transferable experience
- unsupported gaps
- contact details, links, education, certifications, projects, and languages when present

Then map:
- direct matches
- adjacent matches
- unsupported requirements

### 2. Decide emphasis

Choose the narrative based on fit, but avoid overfitting the entire document to one listing:
- **strong match**: reflect the listing language selectively where truthful, without copying its phrasing everywhere
- **stretch match**: emphasize transferability and overlap without overstating
- **specialist framing**: foreground the most relevant stack/domain thread only when the profile strongly supports it
- **generalist framing**: present breadth with a clear story tied to the target role; this is often the safer default

### 3. Produce JSON Resume content

Output a valid JSON Resume object instead of free-form CV text.

Target the standard top-level sections when supported by the profile:
- `$schema`
- `basics`
- `work`
- `volunteer`
- `education`
- `awards`
- `certificates`
- `publications`
- `skills`
- `languages`
- `interests`
- `references`
- `projects`

Use only sections supported by the candidate profile.

### 4. Tailor key sections

#### basics

Populate supported fields such as:
- `name`
- `label`
- `email`
- `phone`
- `url`
- `summary`
- `location`
- `profiles`

Use `basics.label` and `basics.summary` to align with the target role when truthful, but keep the language broad enough that the resume still reads as a strong general application document.

#### work

For each relevant role:
- set factual employer, role, dates, and links from the profile
- use `summary` for concise role scope when useful
- use `highlights` for tailored achievement bullets
- reorder or sharpen highlights for relevance to the listing
- prefer 3-6 strong highlights over noisy padding

Preferred highlight style:
- accomplished **what** by doing **how**, resulting in **impact**

If impact is not quantified in the profile, keep it qualitative.

#### skills

Build a focused JSON Resume `skills` array:
- keep only profile-supported skills
- group skills cleanly by theme or category
- place exact listing matches first
- avoid giant filler dumps

Use entries such as:
- `name`
- `level`
- `keywords`

#### projects, education, certificates, languages

Include these when they strengthen fit or legitimately address listing requirements.

## Runtime output contract

When the outer workflow provides a destination path, write one JSON file per selected listing under:

- `<OPENCLAW_STATE_DIR>/plugin-runtimes/job-search/resumes/<runId>/<listingId>.json`

If the outer workflow does not provide a path, still produce the JSON Resume object in the response so another layer can save it.

## Rendering contract

After writing the JSON Resume artifact, render it to PDF.

Preferred approach:
- use `scripts/render_resume.py` for deterministic PDF rendering
- treat PDF as the required deliverable
- do not prioritize HTML output unless some future workflow explicitly asks for it

## Quality checks

Before returning the result, verify:
- every claim is supported by the profile
- the target title and summary align with the listing without sounding copied from it
- the strongest relevant evidence appears early
- important listing language appears naturally where justified
- the resume remains broadly reusable and not excessively customized to one posting
- weak or irrelevant material is trimmed
- work highlights are specific and not generic filler
- the JSON structure is internally consistent and ready for validation
- the final output is ready to be rendered to PDF

## References

Read `skills/job-resume-generation-skill/references/json-resume-notes.md` when you need the JSON Resume section conventions, rendering assumptions, or field-mapping reminders.

## Script

Use:
- `scripts/render_resume.py`
