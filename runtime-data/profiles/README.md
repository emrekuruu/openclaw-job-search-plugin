# Profiles

This directory stores reusable candidate profile data for resume/CV tailoring.

## Structure

Each candidate should live in its own folder, for example:

- `sample-software-engineer/`
- `sample-data-analyst/`
- `sample-game-developer/`

Each profile folder should use the same structure:

- `profile.md` — the stable, ground-truth candidate profile. This is the primary source of truth and should contain the candidate's durable, factual background in the existing profile schema/format.
- `contexts/` — role-specific augmentation files. These do **not** replace `profile.md`; they only add emphasis, missing-but-true details, relevant technologies, projects, and keywords for a target role.
- `jobs/` — optional storage for job descriptions, one file per target role/company if you want to keep source job posts alongside the profile.
- `outputs/` — optional storage for generated tailored resumes, analysis files, match reports, or draft outputs.

## How to use this with resume-builder

When generating a tailored resume, combine:

1. the candidate's `profile.md` as the base truth source
2. one selected file from `contexts/` for the target role
3. the target job description from `jobs/` or from user input

Recommended rule:

- `profile.md` provides the factual base
- the selected context file provides role-specific emphasis and augmentation
- the target job provides demand-side requirements and keywords

Important:

- do not merge role-specific context back into `profile.md`
- do not treat `contexts/` as a replacement for the base profile
- keep generated outputs in `outputs/`, not inside the base profile or context files
