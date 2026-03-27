# Search Plan Schema

## Purpose

The search plan is the bridge between:

- candidate interpretation by the skill
- deterministic backend execution by the scripts

It exists so the agent can think first, then execute a smaller number of higher-quality searches.

This is preferable to broad retrieval followed by heavy scoring.

## Design principle

The search plan should be:

- derived from the candidate profile
- explicit and inspectable
- focused on quality over volume
- suitable for deterministic execution by the backend layer

## Suggested structure

```json
{
  "runId": "2026-03-27-software-engineer",
  "profilePath": "/absolute/or/runtime/profile/path.md",
  "candidateModel": {
    "seniority": "junior",
    "roleFamily": ["software engineer", "backend engineer", "full stack developer"],
    "techFocus": ["java", "spring boot", "react", "python"],
    "domainFocus": ["banking technology", "fintech", "software"],
    "preferredCompanies": ["Yapı Kredi Teknoloji", "Akbank", "Garanti BBVA Teknoloji"],
    "locations": ["Istanbul"],
    "workModes": ["hybrid", "remote", "on premise"],
    "avoid": ["senior", "lead", "staff", "principal", "manager", "qa-only", "support-only"]
  },
  "queries": [
    {
      "kind": "role-core",
      "searchTerm": "Junior Software Engineer",
      "location": "Istanbul",
      "reason": "Junior candidate with general software engineering target"
    },
    {
      "kind": "role-tech",
      "searchTerm": "Java Spring Boot Developer",
      "location": "Istanbul",
      "reason": "Relevant backend stack from candidate experience"
    },
    {
      "kind": "company-targeted",
      "searchTerm": "Software Engineer Yapı Kredi Teknoloji",
      "location": "Istanbul",
      "reason": "Preferred company and directly relevant banking technology background"
    }
  ],
  "qualityRules": {
    "preferPrecisionOverRecall": true,
    "maxQueries": 8,
    "maxResultsPerQuery": 10,
    "dedupRequired": true
  }
}
```

## Query kinds

Recommended query kinds:

- `role-core` — core role searches such as junior software engineer
- `role-tech` — stack-specific role searches such as Java Spring Boot developer
- `domain-aware` — domain-specific searches such as fintech software engineer
- `company-targeted` — company-priority searches
- `fallback-broad` — optional last resort, used sparingly

## Recommended workflow

1. Skill reads profile
2. Skill infers candidate model
3. Skill creates a search plan
4. Execution layer runs the plan
5. Results are normalized, deduped, and summarized

## Important rule

The search plan should intentionally keep query count low.

High-quality focused searches are preferred over broad noisy retrieval.
