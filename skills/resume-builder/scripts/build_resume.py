#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


SECTION_HEADERS = {
    "## Identity": "identity",
    "## Target Direction": "target_direction",
    "## Preferences": "preferences",
    "## Experience Summary": "experience_summary",
    "## Skills / Keywords": "skills",
    "## Education": "education",
    "## Target Companies": "target_companies",
    "## Constraints": "constraints",
    "## Notes": "notes",
}


def parse_candidate_profile(text: str):
    data = {
        "identity": {},
        "sections": {value: [] for value in SECTION_HEADERS.values()},
        "section_order": [],
    }
    section = None
    for raw in text.splitlines():
        stripped = raw.strip()
        if not stripped:
            continue
        if stripped in SECTION_HEADERS:
            section = SECTION_HEADERS[stripped]
            if section not in data["section_order"]:
                data["section_order"].append(section)
            continue
        if stripped.startswith("## "):
            section = None
            continue

        if section == "identity" and stripped.startswith("- "):
            body = stripped[2:]
            data["sections"][section].append(body)
            if ":" in body:
                key, value = body.split(":", 1)
                data["identity"][key.strip().lower()] = value.strip()
        elif section and stripped.startswith("- "):
            data["sections"][section].append(stripped[2:].strip())
    return data


def joined_profile_text(profile):
    all_lines = []
    for lines in profile["sections"].values():
        all_lines.extend(lines)
    return " | ".join(all_lines)


def extract_job_signals(job_text: str):
    lowered = job_text.lower()
    signals = {
        "role": "Software Engineer, Fullstack" if "fullstack" in lowered else "Software Engineer",
        "must_have": [],
        "nice_to_have": [],
        "priority_keywords": [
            "backend",
            "full stack",
            "java",
            "spring boot",
            "postgresql",
            "react",
            "javascript",
            "git",
            "api",
        ],
    }
    must_terms = [
        "NodeJS",
        "JavaScript",
        "HTML",
        "CSS",
        "Vue",
        "React",
        "RESTful APIs",
        "Git",
        "unit testing",
        "integration testing",
        "English",
    ]
    nice_terms = [
        "Google Cloud",
        "Pub/Sub",
        "Functions",
        "App Engine",
        "Vue3",
        "Firestore",
        "Redis",
        "Memcached",
    ]
    for term in must_terms:
        if term.lower() in lowered:
            signals["must_have"].append(term)
    for term in nice_terms:
        if term.lower() in lowered:
            signals["nice_to_have"].append(term)
    return signals


def strongest_techs(skills):
    ordered = ["Java", "Spring Boot", "PostgreSQL", "React", "JavaScript", "Python", "SQL", "Git"]
    skill_text = " | ".join(skills)
    return [tech for tech in ordered if tech.lower() in skill_text.lower()]


def build_summary(profile, job_signals):
    techs = strongest_techs(profile["sections"]["skills"])
    lead = ", ".join(techs[:4]) if techs else "Java, Spring Boot, PostgreSQL, React"
    return (
        f"Junior Backend / Full-Stack Software Engineer with hands-on experience in {lead}. "
        "Built backend and BFF functionality for an internal banking application, implemented React-based frontend flows, managed PostgreSQL-backed data access, and delivered API-integrated software across banking, mobile, and academic project environments. "
        "Best aligned with backend and full-stack roles that value strong engineering fundamentals, maintainable systems, and product-focused delivery."
    )


def pick_explicit_support(profile, term):
    haystack = joined_profile_text(profile)
    mappings = {
        "JavaScript": ["javascript"],
        "React": ["react"],
        "Git": ["git"],
        "English": ["english: advanced", "english"],
        "NodeJS": ["nodejs", "node.js"],
        "HTML": ["html"],
        "CSS": ["css"],
        "Vue": ["vue"],
        "Vue3": ["vue3"],
        "Google Cloud": ["google cloud"],
        "Pub/Sub": ["pub/sub"],
        "Functions": ["functions"],
        "App Engine": ["app engine"],
        "Firestore": ["firestore"],
        "Redis": ["redis"],
        "Memcached": ["memcached"],
        "unit testing": ["unit testing"],
        "integration testing": ["integration testing"],
    }
    for alias in mappings.get(term, [term]):
        if alias.lower() in haystack.lower():
            return True
    return False


def pick_adjacent_evidence(profile, term):
    haystack = joined_profile_text(profile)
    mappings = {
        "RESTful APIs": ["api", "open data apis"],
    }
    for alias in mappings.get(term, []):
        if alias.lower() in haystack.lower():
            return True
    return False


def infer_experience_entries(profile):
    items = []
    exp = profile["sections"]["experience_summary"]

    ykt = {"company": "Yapı Kredi Teknoloji", "title": "Software Engineering Intern", "bullets": []}
    if any("internal banking applications" in x.lower() for x in exp):
        ykt["bullets"].append("Built software for internal banking applications with a focus on efficient and secure workflows for internal users.")
    if any("react on the frontend" in x.lower() for x in exp) and any("java and spring boot" in x.lower() for x in exp):
        ykt["bullets"].append("Implemented React-based frontend flows and Java/Spring Boot backend and BFF functionality for full-stack delivery.")
    if any("postgresql" in x.lower() for x in exp):
        ykt["bullets"].append("Managed PostgreSQL data access to support core banking application behavior.")
    if ykt["bullets"]:
        items.append(ykt)

    asis = {"company": "Asis Elektronik ve Bilişim Sistemleri", "title": "Software Engineering / Mobile Development Intern", "bullets": []}
    if any("real-time bus tracking" in x.lower() for x in exp):
        asis["bullets"].append("Built mobile application features for real-time bus tracking and card balance inquiry.")
    if any("open data apis" in x.lower() for x in exp):
        asis["bullets"].append("Integrated open data APIs to support live transportation and balance-related functionality.")
    if any("mvvm architecture" in x.lower() for x in exp):
        asis["bullets"].append("Developed within an Android MVVM architecture to keep implementation structured and maintainable.")
    if asis["bullets"]:
        items.append(asis)

    academic = {"company": "Academic and Project Work", "title": "Software Projects", "bullets": []}
    if any("django" in x.lower() and "react" in x.lower() and "python" in x.lower() for x in exp):
        academic["bullets"].append("Built projects with Django, React, MySQL, and Python across web development and data-oriented problem spaces.")
    if any("machine learning" in x.lower() or "route optimization" in x.lower() for x in exp):
        academic["bullets"].append("Applied machine learning, data science, and route optimization work in academic projects.")
    if academic["bullets"]:
        items.append(academic)

    return items


def build_experience(profile, job_signals):
    items = infer_experience_entries(profile)
    for item in items:
        item["bullets"] = item["bullets"][:3]
    return items


def build_skills(profile, job_signals):
    all_skills = profile["sections"]["skills"]
    categories = {
        "Languages": ["Java", "Python", "JavaScript", "SQL", "C#", "C++"],
        "Frameworks & Platforms": ["Spring Boot", "React", "Django", "PostgreSQL", "MongoDB", "Android Studio"],
        "Engineering": ["backend", "full stack", "frontend", "unit testing", "Git"],
    }
    result = {}
    joined = " | ".join(all_skills)
    for key, values in categories.items():
        result[key] = [value for value in values if value.lower() in joined.lower()]
    return result


def tailor_section_lines(section_name, lines, job_signals):
    if section_name == "experience_summary":
        return [
            line.replace("Worked on a full-stack banking application", "Built software for a full-stack banking application")
                .replace("worked on backend and BFF layers", "implemented backend and BFF functionality")
                .replace("Built academic and project work in", "Built projects using")
            for line in lines
        ]
    if section_name == "skills":
        priority = job_signals["priority_keywords"]
        def sort_key(item):
            lowered = item.lower()
            for idx, kw in enumerate(priority):
                if kw in lowered:
                    return (0, idx, lowered)
            return (1, len(priority), lowered)
        return sorted(lines, key=sort_key)
    if section_name == "target_direction":
        priority = ["backend engineer", "full stack engineer", "software engineer", "junior software engineer", "full stack developer", "java developer", "python developer"]
        def sort_key(item):
            lowered = item.lower()
            for idx, kw in enumerate(priority):
                if kw in lowered:
                    return (0, idx, lowered)
            return (1, len(priority), lowered)
        return sorted(lines, key=sort_key)
    return list(lines)


def build_full_cv(profile, job_signals, summary, experience_items):
    tailored_sections = []
    for section_name in profile["section_order"]:
        if section_name == "identity":
            identity_lines = list(profile["sections"][section_name])
            identity_lines.append(f"Tailored Headline: Junior Backend / Full-Stack Software Engineer")
            tailored_sections.append({"section": section_name, "items": identity_lines})
            continue
        if section_name == "experience_summary":
            lines = [f"Tailored Summary: {summary}"]
            for item in experience_items:
                lines.append(f"{item['company']} — {item['title']}")
                lines.extend(item["bullets"])
            original_tailored = tailor_section_lines(section_name, profile["sections"][section_name], job_signals)
            lines.extend(original_tailored)
            tailored_sections.append({"section": section_name, "items": lines})
            continue
        lines = tailor_section_lines(section_name, profile["sections"][section_name], job_signals)
        tailored_sections.append({"section": section_name, "items": lines})
    return tailored_sections


def build_gap_analysis(profile, job_signals):
    supported = []
    adjacent_evidence = []
    unsupported = []

    for term in job_signals["must_have"] + job_signals["nice_to_have"]:
        if pick_explicit_support(profile, term):
            supported.append(term)
        elif pick_adjacent_evidence(profile, term):
            adjacent_evidence.append(term)
        else:
            unsupported.append(term)

    notes = [
        "Keep backend/full-stack emphasis on Java, Spring Boot, PostgreSQL, React, JavaScript, Git, unit testing, and API integration where directly supported.",
        "Treat API integration as adjacent evidence for RESTful API work, not proof of API design ownership.",
        "Treat unit testing and integration testing separately; do not promote one into the other.",
        "Preserve lower-priority content such as projects, activities, volunteer work, and additional experience; deprioritize rather than remove.",
        "Do not claim NodeJS, Vue/Vue3, GCP, Firestore, Redis, Memcached, or integration testing unless the candidate confirms them.",
    ]

    return {
        "supported": supported,
        "adjacent_evidence": adjacent_evidence,
        "unsupported": unsupported,
        "notes": notes,
    }


def build_polished_text(profile, headline, summary, full_cv_sections):
    name = profile["identity"].get("name", "")
    lines = [name, headline, "", "SUMMARY", summary, ""]
    title_map = {
        "identity": "IDENTITY",
        "target_direction": "TARGET DIRECTION",
        "preferences": "PREFERENCES",
        "experience_summary": "EXPERIENCE",
        "skills": "SKILLS",
        "education": "EDUCATION",
        "target_companies": "TARGET COMPANIES",
        "constraints": "CONSTRAINTS",
        "notes": "NOTES",
    }
    for section in full_cv_sections:
        if section["section"] == "identity":
            continue
        lines.append(title_map.get(section["section"], section["section"].upper()))
        for item in section["items"]:
            lines.append(f"- {item}")
        lines.append("")
    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate_profile")
    parser.add_argument("job_description")
    parser.add_argument("--out", default="resume_builder_output.json")
    args = parser.parse_args()

    profile_text = Path(args.candidate_profile).read_text(encoding="utf-8")
    job_text = Path(args.job_description).read_text(encoding="utf-8")
    profile = parse_candidate_profile(profile_text)
    job_signals = extract_job_signals(job_text)

    headline = "Junior Backend / Full-Stack Software Engineer"
    summary = build_summary(profile, job_signals)
    experience = build_experience(profile, job_signals)
    skills = build_skills(profile, job_signals)
    gaps = build_gap_analysis(profile, job_signals)
    full_cv = build_full_cv(profile, job_signals, summary, experience)

    result = {
        "structured_resume": {
            "target_role": job_signals["role"],
            "headline": headline,
            "summary": summary,
            "experience": experience,
            "education": profile["sections"]["education"],
            "skills": skills,
            "full_cv": full_cv,
            "gap_analysis": gaps,
        },
        "polished_resume": build_polished_text(profile, headline, summary, full_cv),
    }

    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
