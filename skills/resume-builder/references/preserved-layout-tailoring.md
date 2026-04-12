# Preserved Layout Tailoring

Use this mode when the user already has a CV and wants the tailored version to keep the same overall structure.

## Goal

Preserve the source CV's visible schema while tailoring content for a target role.

## Default rules

1. Extract the current CV structure first, especially when the source is a PDF.
2. Keep the same section order unless the user explicitly asks for a restructure.
3. Keep stable sections such as Volunteer Work, Activities, Certifications, or similar background sections unchanged by default.
4. Keep Experience entries in place; only paraphrase wording for clarity and target-role keyword alignment.
5. Prefer changing the Projects section before changing other sections.
6. Replace only the least relevant projects with more relevant true projects supplied by the user.
7. Keep dates, employers, education facts, and personal-history items unchanged unless the user provides a correction.
8. Do not invent shipped games, analytics ownership, ads management ownership, or production responsibilities.

## Game-development tailoring rule set

For mobile game / Unity roles:

- emphasize Unity, C#, gameplay systems, debugging, object-oriented programming, grid mechanics, level systems, animation integration, and collaborative development when truthfully supported
- keep non-game sections intact unless keyword-aware paraphrasing improves alignment without changing facts
- if game-dev side projects exist, use them to replace the least relevant projects in the source CV
- preserve Volunteer Work and Activities as-is unless the user requests edits

## Output recommendation

Return both:

- a structured JSON artifact that records what was preserved and what was replaced
- an ATS-friendly CV text that mirrors the source CV's section schema
