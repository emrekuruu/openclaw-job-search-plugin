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
4. Write exactly one JSON artifact per listing to the caller-provided output path.
5. Keep reasoning concise and specific.
6. Make hard mismatches explicit; do not hide them behind a middling score.

## Decision rules

- Use `keep` when the listing is plausibly worth human review.
- Use `drop` when the listing has a clear seniority, experience, location, work-mode, authorization, or role-family mismatch.
- A high score with a `drop` decision is not allowed.
- If critical evidence is missing, say so in the reasoning instead of inventing assumptions.

## Output contract

Use the schema in `references/evaluation-schema.md`.

Write one file per listing to:
- `runtime-data/evaluations/<runId>/<listingId>.json`

If the evaluator cannot complete after reading inputs, it may write:
- `runtime-data/evaluations/<runId>/<listingId>.error.json`

Do **not** rely on stdout to carry the evaluation payload. Stdout should only confirm success or report failure.

If the user wants an example payload or field meanings, read that reference before responding.
