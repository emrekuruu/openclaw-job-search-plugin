# Search Plan Schema

Use this file when editing or auditing the retrieval plan.

## Required shape

```json
{
  "runId": "2026-03-28-software-engineer",
  "profilePath": "/absolute/path/to/profile.md",
  "candidateModel": {
    "seniority": "junior",
    "confidence": "high",
    "roleFamily": ["software engineer", "backend engineer"],
    "experienceYears": 1,
    "employmentIntent": "full-time",
    "techFocus": ["java", "spring boot", "python"],
    "domainFocus": ["fintech", "banking"],
    "preferredCompanies": ["Example Bank Tech"],
    "locations": ["Istanbul", "Remote (Turkey)"],
    "workModes": ["hybrid", "remote", "on premise"],
    "avoidTitlePatterns": ["senior", "lead", "staff", "principal", "manager"],
    "avoidRoleFamilies": ["data scientist", "qa engineer", "designer"],
    "maxAcceptedExperienceYears": 3,
    "retrievalFilters": {
      "siteNames": ["linkedin"],
      "isRemote": true,
      "employmentIntent": "full-time",
      "jobType": "fulltime",
      "distance": 25,
      "easyApply": false,
      "hoursOld": 720,
      "linkedinFetchDescription": true
    },
    "inference": {
      "seniorityReason": "Explicit junior / early-career wording in the profile.",
      "employmentIntentReason": "Defaulted early-career candidate to full-time because internship was not explicitly requested.",
      "roleFamilyReason": "Role family inferred from desired roles and profile keywords: software engineer, backend engineer.",
      "locationsReason": "Locations came from explicit profile preferences.",
      "workModesReason": "Work modes came from explicit profile preferences."
    }
  },
  "retrievalFilters": {
    "siteNames": ["linkedin"],
    "isRemote": true,
    "employmentIntent": "full-time",
    "jobType": "fulltime",
    "distance": 25,
    "easyApply": false,
    "hoursOld": 720,
    "linkedinFetchDescription": true
  },
  "queries": [
    {
      "kind": "role-core",
      "searchTerm": "Junior Software Engineer",
      "location": "Istanbul",
      "reason": "Primary target role software engineer with junior seniority inferred from the profile."
    },
    {
      "kind": "role-tech",
      "searchTerm": "Java Spring Boot Software Engineer",
      "location": "Istanbul",
      "reason": "Stack-aware variant based on candidate technologies: java, spring boot."
    },
    {
      "kind": "company-targeted",
      "searchTerm": "Software Engineer Example Bank Tech",
      "location": "Istanbul",
      "reason": "Preferred company from the profile: Example Bank Tech."
    }
  ],
  "qualityRules": {
    "preferPrecisionOverRecall": true,
    "maxQueries": 8,
    "maxResultsPerQuery": 12,
    "dedupRequired": true,
    "rejectObviousSeniorityMismatch": true,
    "rejectObviousRoleFamilyMismatch": true,
    "rejectExperienceMismatch": true
  },
  "artifacts": {
    "runDir": "/absolute/path/to/runtime-data/search-runs/2026-03-28-software-engineer",
    "planPath": "/absolute/path/to/runtime-data/search-runs/2026-03-28-software-engineer/plan.json",
    "rawResultsPath": "/absolute/path/to/runtime-data/search-runs/2026-03-28-software-engineer/raw-results.json",
    "normalizedJobsPath": "/absolute/path/to/runtime-data/search-runs/2026-03-28-software-engineer/normalized-jobs.json",
    "rejectedJobsPath": "/absolute/path/to/runtime-data/search-runs/2026-03-28-software-engineer/rejected-jobs.json",
    "listingsDir": "/absolute/path/to/runtime-data/search-runs/2026-03-28-software-engineer/listings",
    "summaryPath": "/absolute/path/to/runtime-data/search-runs/2026-03-28-software-engineer/summary.md"
  }
}
```

## Planning rules

1. Infer from the profile; do not depend on static candidate filters in config.
2. Let the agent decide structured retrieval filters from the profile, not only search text.
3. Default to full-time unless the profile explicitly asks for internship or contract work.
4. Keep query count low.
5. Use company-targeted queries only for explicitly preferred companies.
6. Include adjacent role titles only if they are genuinely the same role family.
7. If role family or likely seniority cannot be inferred with enough confidence, fail clearly instead of guessing.
8. Record the inference reasons so a human can inspect why the run targeted those searches.

## Mandatory reject patterns

Always reject or exclude obvious title mismatches for junior and early-career profiles:
- senior
- sr
- lead
- staff
- principal
- manager
- head
- director
- architect

Also reject listings whose title clearly leaves the target family, for example:
- pure QA / test-only roles
- data scientist / analyst roles when the profile targets software engineering
- design/product roles when the profile targets engineering

## Retrieval vs evaluation

This plan only supports retrieval quality control.
Deep keep/drop judgment belongs in `job-listing-evaluation-skill`.
