# Search Plan Schema

Use this file when editing or auditing the retrieval plan.

## Required shape

```json
{
  "runId": "2026-03-28-junior-software-engineer",
  "profilePath": "/absolute/path/to/profile.md",
  "candidateModel": {
    "seniority": "junior",
    "confidence": "high",
    "roleFamily": ["software engineer", "backend engineer"],
    "experienceYears": 2,
    "techFocus": ["java", "spring boot", "python"],
    "domainFocus": ["fintech", "banking technology"],
    "preferredCompanies": ["Example Bank Tech"],
    "locations": ["Istanbul"],
    "workModes": ["hybrid", "remote"],
    "avoidTitlePatterns": ["senior", "lead", "staff", "principal", "manager"],
    "avoidRoleFamilies": ["data scientist", "qa engineer", "designer"],
    "maxAcceptedExperienceYears": 3
  },
  "queries": [
    {
      "kind": "role-core",
      "searchTerm": "Junior Software Engineer",
      "location": "Istanbul",
      "reason": "Primary target role aligned with inferred junior profile"
    },
    {
      "kind": "role-tech",
      "searchTerm": "Java Backend Developer",
      "location": "Istanbul",
      "reason": "Relevant stack from the candidate profile"
    },
    {
      "kind": "company-targeted",
      "searchTerm": "Software Engineer Example Bank Tech",
      "location": "Istanbul",
      "reason": "Preferred company plus relevant domain"
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
  }
}
```

## Planning rules

1. Infer from the profile; do not depend on static candidate filters in config.
2. Keep query count low.
3. Use company-targeted queries only for explicitly preferred companies.
4. Include adjacent role titles only if they are genuinely the same role family.
5. If role family or likely seniority cannot be inferred with enough confidence, fail clearly instead of guessing.

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
