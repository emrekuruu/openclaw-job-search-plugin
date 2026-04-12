---
name: resume-builder
description: Generate professional resumes that conform to the Reactive Resume schema. Use when the user wants to create, build, or generate a resume through conversational AI, or asks about resume structure, sections, or content. This skill guides the agent to ask clarifying questions, avoid hallucination, and produce valid JSON output for https://rxresu.me.
---

# Resume Builder for Reactive Resume

Build professional resumes through conversational AI for [Reactive Resume](https://rxresu.me), a free and open-source resume builder.

## Core Principles

1. **Never hallucinate** - Only include information explicitly provided by the user
2. **Ask questions** - When information is missing or unclear, ask before assuming
3. **Non-destructive tailoring** - Preserve the full CV structure; improve and reprioritize, but do not remove sections or drop content just because it is less relevant
4. **Be concise** - Use clear, direct language; avoid filler words inside bullets and summaries, not by deleting sections
5. **Validate output** - Ensure all generated JSON conforms to the schema or output contract in use

## Workflow

### Step 1: Gather Basic Information

Ask for essential details first, unless the user has already provided them:

- Full name
- Professional headline/title
- Email address
- Phone number
- Location (city, state/country)
- Website (optional)

### Step 2: Collect Section Content

For each section the user wants to include, gather specific details. Never invent dates, company names, achievements, technologies, scope, or metrics.

When tailoring an existing CV, operate in non-destructive mode by default:
- preserve all existing sections
- preserve lower-priority content such as projects, activities, volunteer work, and additional experience
- strengthen wording and keyword alignment without removing information
- reorder only when it improves relevance for the target role

**Experience**: company, position, location, period (e.g., "Jan 2020 - Present"), description of responsibilities/achievements

**Education**: school, degree, area of study, grade (optional), location, period

**Skills**: name, proficiency level (Beginner/Intermediate/Advanced/Expert), keywords

**Projects**: name, period, website (optional), description

**Other sections**: languages, certifications, awards, publications, volunteer work, interests, references

### Step 3: Configure Layout and Design

Ask about preferences:

- Template preference (13 available: azurill, bronzor, chikorita, ditto, ditgar, gengar, glalie, kakuna, lapras, leafish, onyx, pikachu, rhyhorn)
- Page format: A4 or Letter
- Which sections to include and their order

### Step 4: Generate Valid JSON

Output must conform to the Reactive Resume schema. See [references/schema.md](references/schema.md) for the complete schema structure.

Key requirements:
- All item `id` fields must be valid UUIDs
- Description fields accept HTML-formatted strings
- Website fields require both `url` and `label` properties
- Colors use `rgba(r, g, b, a)` format
- Fonts must be available on Google Fonts

## Local Skill Assets

Keep reusable CV tailoring inputs inside this skill:

- base profiles: `skills/resume-builder/assets/profiles/<candidate>/profile.md`
- role-specific contexts: `skills/resume-builder/assets/contexts/<candidate>/`
- saved job descriptions: `skills/resume-builder/assets/jobs/<candidate>/`
- generated outputs: `skills/resume-builder/assets/outputs/<candidate>/`

When working from repository files rather than direct user input, prefer these local skill paths over any repo-level runtime folder.

## Existing CV Preservation Mode

When the user provides an existing CV file and asks to keep the same style, layout, or schema:

- treat the existing CV as the layout source of truth
- preserve the section set and overall shape unless the user explicitly asks for restructuring
- keep stable sections such as volunteer work, activities, certifications, and similar personal-history sections unchanged by default
- prefer targeted edits over broad rewrites
- in project sections, replace only the least relevant projects when the user provides more relevant true projects for the target role
- in experience sections, paraphrase bullet wording to align with target-role keywords only when the underlying facts stay unchanged
- do not invent new employers, dates, shipped products, analytics ownership, ad-tech ownership, or production responsibilities
- if the source CV is a PDF, extract the current section order and bullet style first, then mirror that structure in the tailored output
- when asked for ATS-friendly output, keep the same section schema while normalizing wording, clarity, and keyword placement

For game-development tailoring specifically:

- preserve the existing CV schema from the source CV
- keep Volunteer Work and Activities fixed unless the user says otherwise
- keep Experience entries but allow keyword-aware paraphrasing for Unity, C#, gameplay systems, debugging, object-oriented programming, collaboration, and mobile games when those are truthfully supported
- prefer adding or swapping game-development projects in the Projects section over rewriting unrelated sections

## Resume Writing Tips

Share these tips when helping users craft their resume content:

### Content Guidelines

- **Lead with impact**: Start bullet points with clear action verbs such as Built, Implemented, Developed, Integrated, or Delivered
- **Use WHAT + HOW + WHY**: Each experience bullet should state what was built or changed, how it was done (technology / layer / method), and why it mattered (user, workflow, quality, product purpose, or system behavior)
- **Avoid generic phrasing**: Do not use weak phrases like "worked on" or "contributed to" when a more specific grounded verb is possible
- **Tailor to the role**: For backend/full-stack roles, emphasize backend layers, APIs, data access, system behavior, and the strongest matching technologies first
- **Preserve full structure**: Do not compress an existing CV into a shorter version unless the user explicitly asks
- **Keep it grounded**: Never invent metrics, scope, ownership, or tools that were not provided by the candidate
- **Keep it concise**: Prefer short, information-dense bullets over generic multi-clause descriptions while retaining the original section set

### Section Order Recommendations

For most professionals:
1. Summary (if experienced)
2. Experience
3. Education
4. Skills
5. Projects (if relevant)
6. Certifications/Awards

For students/recent graduates:
1. Education
2. Projects
3. Skills
4. Experience (if any)
5. Activities/Volunteer

### Common Mistakes to Avoid

- Including personal pronouns ("I", "my")
- Using passive voice
- Writing vague bullets that hide the technology, scope, or purpose
- Repeating generic phrases like "worked on" or "contributed to"
- Listing job duties without showing what was built and why it mattered
- Including irrelevant personal information
- Inconsistent date formatting

## Output Format

When generating the resume, output a complete JSON object that conforms to the Reactive Resume schema. The user can then import this JSON directly into Reactive Resume at https://rxresu.me.

Example minimal structure:

```json
{
  "picture": { "hidden": true, "url": "", "size": 80, "rotation": 0, "aspectRatio": 1, "borderRadius": 0, "borderColor": "rgba(0, 0, 0, 0.5)", "borderWidth": 0, "shadowColor": "rgba(0, 0, 0, 0.5)", "shadowWidth": 0 },
  "basics": { "name": "", "headline": "", "email": "", "phone": "", "location": "", "website": { "url": "", "label": "" }, "customFields": [] },
  "summary": { "title": "Summary", "columns": 1, "hidden": false, "content": "" },
  "sections": { ... },
  "customSections": [],
  "metadata": { "template": "onyx", "layout": { ... }, ... }
}
```

For the complete schema, see [references/schema.md](references/schema.md).

## Asking Good Questions

When information is missing, ask specific questions:

- "What was your job title at [Company]?"
- "What dates did you work there? (e.g., Jan 2020 - Dec 2022)"
- "What were your main responsibilities or achievements in this role?"
- "Do you have a specific target role or industry in mind?"

Avoid compound questions. Ask one thing at a time for clarity.
