# Profiles

This directory stores reusable candidate base profiles for resume/CV tailoring inside the `resume-builder` skill.

## Layout

The local asset layout is split by concern:

- `skills/resume-builder/assets/profiles/<candidate>/profile.md` — stable ground-truth candidate profile
- `skills/resume-builder/assets/contexts/<candidate>/` — role-specific augmentation files
- `skills/resume-builder/assets/jobs/<candidate>/` — saved target job descriptions
- `skills/resume-builder/assets/outputs/<candidate>/` — generated tailored resumes, analysis files, and drafts

## How to use this with resume-builder

When generating a tailored resume, combine:

1. the candidate's `profile.md` as the base truth source
2. one selected file from the matching `contexts/<candidate>/` directory
3. the target job description from `jobs/<candidate>/` or from user input

Recommended rule:

- `profile.md` provides the factual base
- the selected context file provides role-specific emphasis and augmentation
- the target job provides demand-side requirements and keywords

Important:

- do not merge role-specific context back into `profile.md`
- do not treat `contexts/` as a replacement for the base profile
- keep generated outputs in `outputs/`, not inside the base profile or context files
