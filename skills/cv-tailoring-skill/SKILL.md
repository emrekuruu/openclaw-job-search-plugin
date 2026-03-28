---
name: cv-tailoring-skill
description: Tailor a candidate CV to a target job description using only provided experience. Use when the user asks to tailor a resume/CV, improve ATS alignment, score match against a job post, reorder or rewrite bullets without inventing experience, or produce a structured gap analysis from candidate profile + job description.
---

# CV Tailoring Skill

## Purpose

Tailor an existing CV to a target role while preserving truthfulness. Rewrite and reorder only; never invent experience, metrics, employers, dates, tools, or responsibilities that the candidate did not provide.

## Inputs

Collect the minimum needed:
- candidate profile or current CV text
- target job description
- optional target title, region, or seniority

If the candidate profile is incomplete, ask for missing facts instead of guessing.

## Workflow

1. Extract required skills, tools, and responsibilities from the job description.
2. Identify explicit evidence already present in the candidate profile.
3. Compute a simple keyword-based match score.
4. Rewrite bullets to emphasize relevant evidence while keeping all claims grounded in the provided profile.
5. Reorder sections or bullets for relevance when helpful.
6. Produce structured output with:
   - tailored CV
   - match score
   - gap analysis

## Output rules

Always keep the response structured under these headings:
- Tailored CV
- Match Score
- Gap Analysis

Within the tailored CV:
- preserve the candidate's actual background
- prefer concise, achievement-oriented bullets
- do not add fake numbers or outcomes
- mark assumptions explicitly if any formatting choice is inferred

## Script usage

Use `scripts/tailor_cv.py` when you want a deterministic first pass from text files.

Example:

```bash
python3 skills/cv-tailoring-skill/scripts/tailor_cv.py candidate.txt job.txt --out cv_tailoring_output.json
```

The script returns a structured JSON payload with:
- `tailored_cv`
- `match_score`
- `gap_analysis`
- supporting keyword coverage fields

## References

Use these bundled references when helpful:
- `references/ats_keywords_template.csv` for ATS-oriented keyword buckets
- `references/output_schema.json` for the target output shape

## Boundaries

- Do not invent experience.
- Do not claim proficiency that is not supported by the input.
- Do not convert weak evidence into certainty.
- If the user asks for stronger claims than the profile supports, say so plainly and keep the draft honest.
