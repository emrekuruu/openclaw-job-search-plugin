# Retrieval Rules

Use this file when deciding whether a listing should survive retrieval cleanup.

## Hard requirements

- Surface missing runtime, profile, backend, or parser inputs as explicit failures.
- Never invent fallback jobs, fallback plans, or guessed profile values.
- Keep the retrieval layer conservative: better to return fewer listings than noisy mismatches.

## Candidate-aware rejection rules

Reject a listing during normalization when one of these is obvious from title or metadata:

1. **Seniority mismatch**
   - title contains `senior`, `sr`, `lead`, `staff`, `principal`, `manager`, `head`, `director`, or `architect`
   - title implies a level above the inferred candidate seniority

2. **Experience mismatch**
   - title/summary explicitly asks for experience well above the candidate profile
   - default threshold: reject when requirement is above `maxAcceptedExperienceYears`

3. **Role-family mismatch**
   - title belongs to a different family than the search plan
   - examples: QA-only, support-only, IT admin, product manager, designer, data scientist when the candidate targets software engineering

## What retrieval should still keep

Keep listings that are slightly noisy but plausibly in-family if they are not obviously disqualifying. The later evaluation skill can score them more carefully.

## Summary expectations

The summary should make it clear how many listings were:
- retrieved raw
- kept after normalization
- rejected for obvious mismatch
