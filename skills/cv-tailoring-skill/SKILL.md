---
name: cv-tailoring-skill
description: Tailor an existing CV or candidate profile to a target job description for the job-search-bot project. Use when an agent already has candidate information plus a job description and must produce a truthful tailored CV draft, a match score, and a concise gap analysis. This skill is for CV tailoring only, not live job retrieval, listing evaluation, application submission, or interview preparation.
---

# CV Tailoring Skill

Tailor the CV **after** the target role is known.

This skill owns:
- reading the candidate profile or existing CV
- reading the target job description
- extracting role-relevant keywords and requirements
- rewriting and reordering existing content only
- producing a structured tailored draft
- producing a match score and gap analysis

This skill does **not** own:
- live job retrieval
- listing ranking or keep/drop decisions
- submitting applications
- fabricating stronger claims than the source profile supports

## Follow this workflow

1. Read the candidate profile or current CV first.
2. Read the target job description.
3. Extract must-have and high-signal keywords from the job description.
4. Map those requirements to evidence that is explicitly present in the candidate material.
5. Rewrite and reorder only the supported content.
6. Produce output with:
   - `tailored_cv`
   - `match_score`
   - `gap_analysis`
7. Make unsupported requirements explicit in the gap analysis instead of silently smoothing them over.

## Enforce these rules

1. Never invent experience, tools, dates, employers, scope, certifications, or metrics.
2. Only rewrite, reorder, compress, or clarify claims already supported by the input.
3. If the source material is too weak or incomplete, say so clearly.
4. Keep the output structured and easy to parse.
5. Prefer concise, achievement-oriented bullets, but do not exaggerate.
6. If a keyword appears in the job description without clear candidate evidence, treat it as a gap.

## Use the workflow script

```bash
python3 skills/cv-tailoring-skill/scripts/tailor_cv.py <candidate_profile.txt> <job_description.txt> --out <output.json>
```

The script produces a deterministic first pass containing:
- `tailored_cv`
- `match_score`
- `gap_analysis`
- keyword coverage details

## Load references as needed

- Read `references/ats_keywords_template.csv` when reviewing ATS-oriented keyword buckets.
- Read `references/output-schema.md` before changing the output structure or validating the response shape.
- Read `references/resume-builder-notes.md` only if you want guidance inspired by the external `resume-builder` skill without changing this skill's narrower scope.
