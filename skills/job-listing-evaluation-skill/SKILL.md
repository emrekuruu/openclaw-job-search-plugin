---
name: job-listing-evaluation-skill
description: Evaluate collected job listings against a candidate profile after retrieval is complete. Use when an agent already has a candidate profile plus one or more job listings and must decide keep/drop, assign a single consistent 0-100 score, and explain the judgment concisely and consistently. This skill is for fit evaluation, not live retrieval, applications, resume tailoring, or interview prep.
---

# Job Listing Evaluation Skill

Evaluate listings **after** retrieval.

## Follow this workflow

1. Read the candidate profile first.
2. Read the collected listing.
3. Score the listing on a **single 0-100 scale**.
4. Output one record per listing with:
   - `decision`
   - `score` (0-100)
   - `reasoning`
   - optional dimension breakdowns that also use 0-100 values
5. Keep reasoning concise and specific.
6. Make hard mismatches explicit; do not hide them behind a middling score.

## Decision rules

- Use `keep` when the listing is plausibly worth human review.
- Use `drop` when the listing has a clear seniority, experience, location, work-mode, authorization, or role-family mismatch.
- A high score with a `drop` decision is not allowed.
- If critical evidence is missing, say so in the reasoning instead of inventing assumptions.

## Output contract

Use the schema in `references/evaluation-schema.md`.

If the user wants an example payload or field meanings, read that reference before responding.
