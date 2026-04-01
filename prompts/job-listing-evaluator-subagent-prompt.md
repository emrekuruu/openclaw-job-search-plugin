You are evaluating exactly one job listing against a candidate profile.

Inputs:
- `profilePath`: path to the candidate profile markdown file
- `listingPath`: path to one listing JSON file
- `runId`: run identifier
- `outputPath`: path where you must write the evaluation JSON
- `errorPath`: optional path where you should write an error JSON if evaluation fails

Tasks:
1. read the candidate profile from `profilePath`
2. read the listing JSON from `listingPath`
3. evaluate the listing using the repo's job-listing-evaluation-skill contract
4. write exactly one JSON object to `outputPath`
5. if you cannot complete the evaluation, write a JSON error object to `errorPath`

Required output shape:
{
  "listingId": "string",
  "decision": "keep|maybe|drop",
  "score": 84,
  "reasoning": "Strong junior backend fit with relevant Java/Spring experience; slight stretch on years requirement.",
  "dimensions": {
    "roleFit": 90,
    "seniorityFit": 85,
    "locationFit": 70,
    "domainFit": 80,
    "skillsFit": 95
  }
}

Rules:
- evaluate exactly one listing
- do not rely on stdout for the result
- the result must be written to `outputPath`
- keep reasoning concise and specific
- do not assume any repo-local default profile; always use the provided `profilePath`
- `dimensions` are required, not optional
- every dimension score must be normalized to 0-100
- final `score` must be normalized to 0-100 and consistent with the dimension scores
- `decision` must be exactly one of `keep`, `maybe`, or `drop`
- if the listing is obviously outside the candidate's role, seniority, or location constraints, reflect that clearly in the dimension scores
