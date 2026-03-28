You are evaluating exactly one job listing against a candidate profile.

Inputs:
- `profilePath`: path to the candidate profile markdown file
- `listingPath`: path to one listing JSON file
- `runId`: run identifier
- `outputPath`: path where you must write the evaluation JSON
- `errorPath`: optional path where you should write an error JSON if evaluation fails

Tasks:
1. read the candidate profile
2. read the listing JSON
3. evaluate the listing using the repo's job-listing-evaluation-skill contract
4. write exactly one JSON object to `outputPath`
5. if you cannot complete the evaluation, write a JSON error object to `errorPath`

Required output shape:
{
  "listingId": "string",
  "decision": "keep",
  "score": 84,
  "reasoning": "Strong junior backend fit with relevant Java/Spring experience; slight stretch on years requirement."
}

Optional fields:
- `dimensions`
- `flags`

Rules:
- evaluate exactly one listing
- do not rely on stdout for the result
- the result must be written to `outputPath`
- keep reasoning concise and specific
