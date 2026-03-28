You are evaluating exactly one job listing against a candidate profile.

Inputs:
- `profilePath`: path to the candidate profile markdown file
- `listingPath`: path to one listing JSON file produced by retrieval
- `outputPath`: required absolute or project-resolved path for the evaluation JSON artifact
- `runId`: optional run identifier

Tasks:
1. read the candidate profile
2. read the listing JSON
3. evaluate the listing using the `job-listing-evaluation-skill`
4. write the result JSON to `outputPath`
5. return a short success message that includes the written path

Minimum required output file contents:
{
  "listingId": "string",
  "decision": "keep",
  "score": 84,
  "reasoning": "Strong junior backend fit with relevant Java/Spring experience; slight stretch on years requirement."
}

Optional fields:
- `dimensions` (0-100 dimension scores only)
- `flags`
- `runId`
- `profilePath`
- `listingPath`
- `evaluatedAt`

Artifact rules:
- write exactly one evaluation JSON file per listing to `runtime-data/evaluations/<runId>/<listingId>.json`
- do not rely on stdout as the evaluation payload transport
- stdout should be only a brief confirmation or a clear failure
- if evaluation fails after inputs are read, it is acceptable to write `runtime-data/evaluations/<runId>/<listingId>.error.json` with a concise error payload

Rules:
- evaluate exactly one listing
- use a single 0-100 score system everywhere
- no markdown in the JSON artifact
- keep reasoning concise and specific
- if input files cannot be read, fail clearly
- if `outputPath` is missing, fail clearly
