#!/usr/bin/env python3
import argparse
import json
import re
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

GROUP_LABELS = {
    "identity": {"Contact"},
    "target_direction": {"Desired roles", "Preferred industries", "Preferred company types"},
    "preferences": {"Preferred locations", "Work modes", "Salary expectation", "Freshness preference"},
}


def slug_title(name: str) -> str:
    return name.replace("_", " ").title()


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


def contains_term(text: str, term: str) -> bool:
    pattern = r"(?<![A-Za-z0-9])" + re.escape(term) + r"(?![A-Za-z0-9])"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def parse_candidate_profile(text: str):
    data = {
        "identity": {},
        "section_order": [],
        "sections": {},
    }
    current_section = None
    current_group = None

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if stripped in SECTION_HEADERS:
            current_section = SECTION_HEADERS[stripped]
            current_group = None
            if current_section not in data["section_order"]:
                data["section_order"].append(current_section)
                data["sections"][current_section] = []
            continue

        if stripped.startswith("## "):
            current_section = None
            current_group = None
            continue

        if not current_section or not stripped.startswith("-"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        body = stripped[1:].strip()
        is_label = body.endswith(":")
        label_name = body[:-1] if is_label else None

        if current_section == "identity":
            if is_label and label_name in GROUP_LABELS.get("identity", set()):
                current_group = {"label": label_name, "items": []}
                data["sections"][current_section].append(current_group)
                continue
            if current_group is not None and indent >= 2:
                current_group["items"].append(body)
                continue
            if ":" in body:
                key, value = body.split(":", 1)
                key = key.strip()
                value = value.strip()
                data["identity"][key.lower()] = value
                data["sections"][current_section].append({"type": "field", "label": key, "value": value})
                current_group = None
            else:
                data["sections"][current_section].append({"type": "item", "text": body})
            continue

        if is_label and label_name in GROUP_LABELS.get(current_section, set()):
            current_group = {"label": label_name, "items": []}
            data["sections"][current_section].append(current_group)
            continue

        if current_group is not None and indent >= 2:
            current_group["items"].append(body)
        else:
            current_group = None
            data["sections"][current_section].append({"type": "item", "text": body})

    return data


def joined_profile_text(profile):
    chunks = []
    for section_name in profile["section_order"]:
        for entry in profile["sections"].get(section_name, []):
            if isinstance(entry, dict) and "items" in entry:
                chunks.append(entry["label"])
                chunks.extend(entry["items"])
            elif entry.get("type") == "field":
                chunks.append(entry["label"])
                chunks.append(entry["value"])
            elif entry.get("type") == "item":
                chunks.append(entry["text"])
    return " | ".join(chunks)


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


def strongest_techs(skill_entries):
    ordered = ["Java", "Spring Boot", "PostgreSQL", "React", "JavaScript", "Python", "SQL", "Git"]
    skill_text = " | ".join(skill_entries)
    return [tech for tech in ordered if contains_term(skill_text, tech)]


def collect_skill_entries(profile):
    results = []
    for entry in profile["sections"].get("skills", []):
        if entry.get("type") == "item":
            results.append(entry["text"])
    return results


def collect_section_items(profile, section_name):
    items = []
    for entry in profile["sections"].get(section_name, []):
        if isinstance(entry, dict) and "items" in entry:
            items.extend(entry["items"])
        elif entry.get("type") == "field":
            items.append(f"{entry['label']}: {entry['value']}")
        elif entry.get("type") == "item":
            items.append(entry["text"])
    return items


def build_summary(profile, job_signals):
    skills = collect_skill_entries(profile)
    techs = strongest_techs(skills)
    lead = ", ".join(techs[:4]) if techs else "Java, Spring Boot, PostgreSQL, React"
    return (
        f"Junior Backend / Full-Stack Software Engineer with hands-on experience in {lead}. "
        "Built backend and BFF functionality for an internal banking application, implemented React-based frontend flows, managed PostgreSQL-backed data access, and delivered API-integrated software across banking, mobile, and academic project environments. "
        "Best aligned with backend and full-stack roles that value strong engineering fundamentals, maintainable systems, and product-focused delivery."
    )


def pick_explicit_support(profile, term):
    haystack = joined_profile_text(profile)
    mappings = {
        "JavaScript": ["JavaScript"],
        "React": ["React"],
        "Git": ["Git"],
        "English": ["English"],
        "NodeJS": ["NodeJS", "Node.js"],
        "HTML": ["HTML"],
        "CSS": ["CSS"],
        "Vue": ["Vue"],
        "Vue3": ["Vue3"],
        "Google Cloud": ["Google Cloud"],
        "Pub/Sub": ["Pub/Sub"],
        "Functions": ["Functions"],
        "App Engine": ["App Engine"],
        "Firestore": ["Firestore"],
        "Redis": ["Redis"],
        "Memcached": ["Memcached"],
        "unit testing": ["unit testing"],
        "integration testing": ["integration testing"],
    }
    for alias in mappings.get(term, [term]):
        if contains_term(haystack, alias):
            return True
    return False


def pick_adjacent_evidence(profile, term):
    haystack = joined_profile_text(profile)
    mappings = {
        "RESTful APIs": ["API", "APIs", "open data APIs"],
    }
    for alias in mappings.get(term, []):
        if contains_term(haystack, alias):
            return True
    return False


def infer_experience_entries(profile):
    exp = collect_section_items(profile, "experience_summary")
    entries = []

    ykt = {"company": "Yapı Kredi Teknoloji", "title": "Software Engineering Intern", "bullets": []}
    if any("internal banking applications" in x.lower() for x in exp):
        ykt["bullets"].append("Built software for internal banking applications with a focus on efficient and secure workflows for internal users.")
    if any("react on the frontend" in x.lower() for x in exp) and any("java and spring boot" in x.lower() for x in exp):
        ykt["bullets"].append("Implemented React-based frontend flows and Java/Spring Boot backend and BFF functionality for full-stack delivery.")
    if any("postgresql" in x.lower() for x in exp):
        ykt["bullets"].append("Managed PostgreSQL data access to support core banking application behavior.")
    if ykt["bullets"]:
        entries.append(ykt)

    asis = {"company": "Asis Elektronik ve Bilişim Sistemleri", "title": "Software Engineering / Mobile Development Intern", "bullets": []}
    if any("real-time bus tracking" in x.lower() for x in exp):
        asis["bullets"].append("Built mobile application features for real-time bus tracking and card balance inquiry.")
    if any("open data apis" in x.lower() for x in exp):
        asis["bullets"].append("Integrated open data APIs to support live transportation and balance-related functionality.")
    if any("mvvm architecture" in x.lower() for x in exp):
        asis["bullets"].append("Developed within an Android MVVM architecture to keep implementation structured and maintainable.")
    if asis["bullets"]:
        entries.append(asis)

    projects = {"company": "Academic and Project Work", "title": "Software Projects", "bullets": []}
    if any("django" in x.lower() and "react" in x.lower() and "python" in x.lower() for x in exp):
        projects["bullets"].append("Built projects with Django, React, MySQL, and Python across web development and data-oriented problem spaces.")
    if any("machine learning" in x.lower() or "route optimization" in x.lower() for x in exp):
        projects["bullets"].append("Applied machine learning, data science, and route optimization work in academic projects.")
    if projects["bullets"]:
        entries.append(projects)

    return entries


def build_experience(profile, job_signals):
    return infer_experience_entries(profile)


def build_skills(profile, job_signals):
    original_items = collect_skill_entries(profile)
    seen = set()
    prioritized = []
    leftovers = []
    for kw in job_signals["priority_keywords"]:
        for item in original_items:
            key = item.lower()
            if key in seen:
                continue
            if contains_term(item, kw):
                prioritized.append(item)
                seen.add(key)
    for item in original_items:
        key = item.lower()
        if key not in seen:
            leftovers.append(item)
            seen.add(key)
    return prioritized + sorted(leftovers, key=str.lower)


def dedupe_preserve_order(items):
    seen = set()
    result = []
    for item in items:
        norm = normalize_text(item).lower()
        if norm and norm not in seen:
            seen.add(norm)
            result.append(item)
    return result


def tailor_simple_items(section_name, items, job_signals):
    updated = []
    for item in items:
        text = item
        if section_name == "experience_summary":
            text = text.replace("Worked on a full-stack banking application", "Built software for a full-stack banking application")
            text = text.replace("worked on backend and BFF layers", "implemented backend and BFF functionality")
            text = text.replace("Built academic and project work in", "Built projects using")
        updated.append(text)
    return dedupe_preserve_order(updated)


def tailor_grouped_section(section_name, entries, job_signals):
    result = []
    for entry in entries:
        if isinstance(entry, dict) and "items" in entry:
            items = list(entry["items"])
            if section_name in {"target_direction", "preferences"}:
                if entry["label"] == "Desired roles":
                    priority = [
                        "Backend Engineer",
                        "Full Stack Engineer",
                        "Software Engineer",
                        "Junior Software Engineer",
                        "Full Stack Developer",
                        "Java Developer",
                        "Python Developer",
                    ]
                    items = sorted(items, key=lambda x: (priority.index(x) if x in priority else 999, x.lower()))
            result.append({"label": entry["label"], "items": dedupe_preserve_order(items)})
        elif entry.get("type") == "item":
            result.append({"type": "item", "text": entry["text"]})
        elif entry.get("type") == "field":
            result.append(entry)
    return result


def build_full_cv(profile, job_signals, summary, experience_items):
    full_cv = []
    for section_name in profile["section_order"]:
        original_entries = profile["sections"][section_name]

        if section_name == "identity":
            identity_entries = []
            for entry in original_entries:
                if entry.get("type") == "field":
                    identity_entries.append(entry)
                elif isinstance(entry, dict) and "items" in entry:
                    identity_entries.append({"label": entry["label"], "items": dedupe_preserve_order(entry["items"])})
                else:
                    identity_entries.append(entry)
            identity_entries.append({"type": "field", "label": "Tailored Headline", "value": "Junior Backend / Full-Stack Software Engineer"})
            full_cv.append({"section": section_name, "entries": identity_entries})
            continue

        if section_name == "experience_summary":
            experience_entries = []
            experience_entries.append({"type": "summary", "text": summary})
            for item in experience_items:
                experience_entries.append({
                    "type": "role",
                    "company": item["company"],
                    "title": item["title"],
                    "bullets": dedupe_preserve_order(item["bullets"]),
                })
            original_simple = collect_section_items(profile, section_name)
            original_simple = tailor_simple_items(section_name, original_simple, job_signals)
            experience_entries.append({"type": "original_items", "items": original_simple})
            full_cv.append({"section": section_name, "entries": experience_entries})
            continue

        if section_name == "skills":
            skill_items = build_skills(profile, job_signals)
            full_cv.append({"section": section_name, "entries": [{"type": "items", "items": skill_items}]})
            continue

        tailored_entries = tailor_grouped_section(section_name, original_entries, job_signals)
        full_cv.append({"section": section_name, "entries": tailored_entries})
    return full_cv


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
    return {
        "supported": supported,
        "adjacent_evidence": adjacent_evidence,
        "unsupported": unsupported,
        "notes": [
            "Keep backend/full-stack emphasis on Java, Spring Boot, PostgreSQL, React, JavaScript, Git, unit testing, and API integration where directly supported.",
            "Treat API integration as adjacent evidence for RESTful API work, not proof of API design ownership.",
            "Treat unit testing and integration testing separately; do not promote one into the other.",
            "Preserve lower-priority content such as projects, activities, volunteer work, and additional experience; deprioritize rather than remove.",
            "Do not claim NodeJS, Vue/Vue3, Google Cloud, Firestore, Redis, Memcached, or integration testing unless the candidate confirms them.",
        ],
    }


def render_entry(entry):
    if entry.get("type") == "field":
        return [f"{entry['label']}: {entry['value']}"]
    if entry.get("type") == "summary":
        return [entry["text"]]
    if entry.get("type") == "role":
        lines = [f"{entry['company']} — {entry['title']}"]
        lines.extend([f"• {b}" for b in entry["bullets"]])
        return lines
    if entry.get("type") == "items":
        return [f"• {item}" for item in entry["items"]]
    if entry.get("type") == "original_items":
        return [f"• {item}" for item in entry["items"]]
    if isinstance(entry, dict) and "items" in entry:
        lines = [entry["label"]]
        lines.extend([f"• {item}" for item in entry["items"]])
        return lines
    if entry.get("type") == "item":
        return [f"• {entry['text']}"]
    return []


def build_polished_text(profile, headline, summary, full_cv_sections):
    name = profile["identity"].get("name", "")
    lines = [name, headline, ""]
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
        section_name = section["section"]
        if section_name == "identity":
            continue
        lines.append(title_map.get(section_name, slug_title(section_name).upper()))
        for entry in section["entries"]:
            lines.extend(render_entry(entry))
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
    full_cv = build_full_cv(profile, job_signals, summary, experience)
    gap_analysis = build_gap_analysis(profile, job_signals)

    result = {
        "structured_resume": {
            "target_role": job_signals["role"],
            "headline": headline,
            "summary": summary,
            "experience": experience,
            "education": collect_section_items(profile, "education"),
            "skills": build_skills(profile, job_signals),
            "full_cv": full_cv,
            "gap_analysis": gap_analysis,
        },
        "polished_resume": build_polished_text(profile, headline, summary, full_cv),
    }

    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
