---
name: job-resume-generation-skill
description: Thin resume-generation skill for the job-search plugin workflow. Use when a listing has already been retrieved and evaluated as keep or maybe, and the agent should take the candidate profile plus the selected listing and generate a tailored CV/resume, including ATS-aware rewrites of summaries and skills, optionally shaped for Reactive Resume.
---

# Job Resume Generation Skill

This skill owns the content-generation guidance for the third step in the workflow.

## Workflow position

Use this after:
1. search
2. evaluate
3. select a `keep` or `maybe` listing
4. generate a tailored resume from the profile plus listing

The deterministic search/evaluation/export mechanics belong to the plugin. This skill owns the judgment and writing guidance for converting a candidate profile plus one selected listing into a tailored CV.

## Inputs

Expect:
- `profilePath`: path to the candidate profile
- selected listing content, or path to the selected listing JSON/artifact
- optional evaluation context such as:
  - `decision`
  - `score`
  - evaluator reasoning
  - target company/title

## Responsibilities

The agent using this skill should:
- read the candidate profile from the provided `profilePath`
- read the chosen listing carefully
- identify must-have and nice-to-have requirements
- identify exact keyword matches and adjacent transferable experience
- generate a tailored CV/resume that stays truthful to the profile
- strengthen summaries, bullet phrasing, and skill ordering for ATS and human readability
- avoid fabricating experience, metrics, technologies, or seniority
- produce output either as polished resume text or in a structure suitable for Reactive Resume

## Truthfulness rules

- Do not invent employers, dates, projects, metrics, certifications, degrees, or tools.
- Rephrase aggressively only within the factual boundaries of the profile.
- If the listing asks for unsupported experience, do not claim it.
- Prefer adjacent evidence and transferable outcomes over bluffing.

## Tailoring process

### 1. Build a fit map

Extract from the listing:
- role title and scope
- core responsibilities
- required skills
- preferred skills
- domain and product signals
- seniority expectations
- location or work authorization constraints if relevant

Extract from the profile:
- strongest matching experiences
- technologies and domains
- achievements and measurable outcomes
- adjacent/transferable experience
- unsupported gaps

Then map:
- direct matches
- adjacent matches
- unsupported requirements

### 2. Decide emphasis

Choose the narrative based on fit:
- **strong match**: mirror the listing language closely where truthful
- **stretch match**: emphasize transferability and overlap without overstating
- **specialist framing**: foreground the most relevant stack/domain thread
- **generalist framing**: present breadth with a clear story tied to the target role

### 3. Rewrite the CV

#### Summary

Write a concise summary that:
- aligns with the target role
- highlights the strongest supported domains/stacks
- mentions ownership, delivery, or impact where supported
- uses a few high-value listing keywords naturally

#### Experience

For relevant experiences:
- lead with action and impact
- include tools/stack where useful for ATS
- reorder bullets by relevance to the target role
- prefer 3-6 strong bullets over padding
- keep qualitative impact if the profile lacks hard metrics

Preferred bullet pattern:
- accomplished **what** by doing **how**, resulting in **impact**

#### Skills

Build a focused skills section:
- keep only profile-supported skills
- group skills clearly
- place exact listing matches first
- remove weak filler and duplicate variants

Possible groupings:
- Languages
- Frameworks
- Cloud/DevOps
- Data/AI
- Product/Leadership
- Tools

#### Other sections

Include projects, education, certifications, links, and languages only when they strengthen fit or close a legitimate gap.

## Output modes

Return one or more of these depending on the request:

### 1. Tailored resume draft
A polished human-readable CV/resume draft.

### 2. Structured Reactive Resume content
A sectioned payload suitable for entry into Reactive Resume.

### 3. Tailoring notes
A concise note covering:
- keywords targeted
- content emphasized
- content deprioritized
- unsupported requirements left unclaimed

## Reactive Resume

Use Reactive Resume as the target builder/editor when structured output is needed:
- https://github.com/amruthpillai/reactive-resume

Map content into these conceptual sections:
- basics
- headline or target title
- summary/objective
- work experience
- education
- skills
- projects
- certifications
- languages
- profiles/links

If exact schema or import formatting is required, inspect the current project/docs before producing automation-specific output.

## Quality checks

Before returning the result, verify:
- every claim is supported by the profile
- the title and summary align with the listing
- the most relevant evidence is near the top
- key listing language appears naturally where justified
- weak or irrelevant material is trimmed
- bullets are specific and not generic filler

## References

Read `skills/job-resume-generation-skill/references/reactive-resume-notes.md` when the user explicitly wants output tailored for Reactive Resume or asks for structured section output instead of plain CV text.
