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

ANALYSIS_PREFIXES = (
    "candidate has strong relevance",
    "prefer roles where",
    "tailor emphasis around",
    "source profile lacks enough",
)


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip())


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


def identity_value(profile, key, default=""):
    return profile["identity"].get(key.lower(), default)


def extract_contact(profile):
    email = ""
    phone = ""
    linkedin = ""
    for entry in profile["sections"].get("identity", []):
        if isinstance(entry, dict) and entry.get("label") == "Contact":
            for item in entry.get("items", []):
                lower = item.lower()
                if lower.startswith("email:"):
                    email = item.split(":", 1)[1].strip()
                elif lower.startswith("phone:"):
                    phone = item.split(":", 1)[1].strip()
                elif "linkedin" in lower:
                    linkedin = item
    return email, phone, linkedin


def clean_bullet(text: str) -> str:
    return re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", text).strip()


def split_title_and_area(line: str):
    parts = [p.strip() for p in line.split(",")]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], ", ".join(parts[1:])


def dedupe(items):
    seen = set()
    output = []
    for item in items:
        norm = normalize_text(item).lower()
        if norm and norm not in seen:
            seen.add(norm)
            output.append(item)
    return output


def is_analysis_line(text: str) -> bool:
    lower = normalize_text(text).lower()
    return any(lower.startswith(prefix) for prefix in ANALYSIS_PREFIXES)


def infer_label(profile, tailored):
    matched = [x.lower() for x in tailored.get("match_score", {}).get("matched_keywords", [])]
    if any(term in matched for term in ["frontend", "react", "javascript", "full-stack"]):
        return "Full-Stack Engineer"

    desired_roles = []
    for entry in profile["sections"].get("target_direction", []):
        if isinstance(entry, dict) and entry.get("label") == "Desired roles":
            desired_roles.extend(entry.get("items", []))
    preferred = [
        "Full Stack Engineer",
        "Backend Engineer",
        "Software Engineer",
        "Junior Software Engineer",
        "Full Stack Developer",
        "Java Developer",
        "Python Developer",
    ]
    for role in preferred:
        if role in desired_roles:
            return role
    return identity_value(profile, "current title") or "Software Engineer"


def infer_summary(profile, tailored):
    skills = [x.lower() for x in collect_section_items(profile, "skills")]
    exp = collect_section_items(profile, "experience_summary")

    strengths = []
    if any("javascript" in x for x in skills):
        strengths.append("JavaScript")
    if any("react" in x for x in skills):
        strengths.append("React")
    if any("postgresql" in x for x in skills):
        strengths.append("PostgreSQL")
    if any("mysql" in x.lower() for x in exp):
        strengths.append("MySQL")
    if any(x == "java" or "java spring boot" in x for x in skills):
        strengths.append("Java and Spring Boot")
    if any("api" in line.lower() for line in exp):
        strengths.append("API integration")

    lead = ", ".join(dedupe(strengths)[:4]) or "full-stack application development"
    role = infer_label(profile, tailored)
    return (
        f"Early-career {role.lower()} with internship experience building internal banking and mobile application software. "
        f"Hands-on experience with {lead}, plus exposure to backend, frontend, and database-backed product development. "
        "Strong fit for junior full-stack or backend-leaning roles that value solid engineering fundamentals, product thinking, and fast learning."
    )


def select_tailored_points(tailored, keywords, banned_keywords=None):
    banned_keywords = banned_keywords or []
    points = []
    for point in tailored.get("tailored_cv", {}).get("highlighted_experience", []):
        text = clean_bullet(point)
        lower = text.lower()
        if not text or is_analysis_line(text):
            continue
        if any(keyword in lower for keyword in keywords) and not any(bad in lower for bad in banned_keywords):
            points.append(text)
    return dedupe(points)


def ensure_sentence(text: str) -> str:
    text = normalize_text(text)
    if not text:
        return text
    if text.endswith((".", "!", "?")):
        return text
    return text + "."


def rewrite_ykt_bullets(profile):
    experience_lines = collect_section_items(profile, "experience_summary")
    bullets = []
    if any("internal banking applications" in line.lower() for line in experience_lines):
        bullets.append("Built software for internal banking applications with a focus on secure and efficient internal workflows.")
    if any("react on the frontend" in line.lower() for line in experience_lines) and any("java and spring boot" in line.lower() for line in experience_lines):
        bullets.append("Implemented React frontend flows and contributed to backend and BFF functionality using Java and Spring Boot.")
    if any("postgresql" in line.lower() for line in experience_lines):
        bullets.append("Worked with PostgreSQL-backed data access to support application behavior and user-facing flows.")
    if any("full-stack banking application" in line.lower() for line in experience_lines):
        bullets.append("Contributed to a full-stack banking application used by internal users in a product-oriented engineering environment.")
    return dedupe(bullets)


def rewrite_asis_bullets(profile):
    experience_lines = collect_section_items(profile, "experience_summary")
    bullets = []
    if any("real-time bus tracking" in line.lower() for line in experience_lines):
        bullets.append("Developed mobile application features for real-time bus tracking and card balance inquiry.")
    if any("open data apis" in line.lower() for line in experience_lines):
        bullets.append("Integrated open data APIs to support live transportation and balance-related functionality.")
    if any("mvvm architecture" in line.lower() for line in experience_lines):
        bullets.append("Worked within an Android MVVM architecture to keep implementation structured and maintainable.")
    return dedupe(bullets)


def rewrite_project_bullets(profile):
    experience_lines = collect_section_items(profile, "experience_summary")
    bullets = []
    if any(all(term in line.lower() for term in ["django", "react", "python"]) for line in experience_lines):
        bullets.append("Built academic and personal projects using Django, React, MySQL, and Python across web development scenarios.")
    if any("machine learning" in line.lower() or "route optimization" in line.lower() for line in experience_lines):
        bullets.append("Worked on data-oriented projects involving machine learning, data science, and route optimization.")
    return dedupe(bullets)


def infer_work_entries(profile, tailored):
    experience_lines = collect_section_items(profile, "experience_summary")
    entries = []

    if any("yapı kredi teknoloji" in line.lower() for line in experience_lines):
        entries.append({
            "name": "Yapı Kredi Teknoloji",
            "position": "Software Engineering Intern",
            "summary": "Contributed to internal banking product development in a full-stack engineering environment.",
            "highlights": rewrite_ykt_bullets(profile)[:4],
        })

    if any("asis elektronik" in line.lower() for line in experience_lines):
        entries.append({
            "name": "Asis Elektronik ve Bilişim Sistemleri",
            "position": "Software Engineering / Mobile Development Intern",
            "summary": "Contributed to mobile application development and API-driven features.",
            "highlights": rewrite_asis_bullets(profile)[:4],
        })

    if any(any(term in line.lower() for term in ["django", "react", "mysql", "python", "machine learning", "route optimization"]) for line in experience_lines):
        entries.append({
            "name": "Academic and Project Work",
            "position": "Software Projects",
            "summary": "Built academic and personal projects across web development and data-oriented problem solving.",
            "highlights": rewrite_project_bullets(profile)[:4],
        })

    return entries


def infer_skills(profile, tailored):
    skill_items = collect_section_items(profile, "skills")
    matched = [x.lower() for x in tailored.get("match_score", {}).get("matched_keywords", [])]
    priority_terms = [
        "javascript", "react", "postgresql", "mysql", "git", "api", "backend", "frontend", "full stack", "python", "java", "spring"
    ]
    prioritized = []
    leftovers = []
    for item in skill_items:
        lower = item.lower()
        if any(term in lower for term in matched + priority_terms):
            prioritized.append(item)
        else:
            leftovers.append(item)
    return dedupe(prioritized + leftovers)


def infer_languages(profile):
    notes = collect_section_items(profile, "notes")
    languages = []
    for line in notes:
        if ":" not in line:
            continue
        name, fluency = [part.strip() for part in line.split(":", 1)]
        if name.lower() in {"turkish", "english", "german"}:
            languages.append({"language": name, "fluency": fluency})
    return languages


def build_json_resume(profile, tailored):
    email, phone, linkedin = extract_contact(profile)
    name = identity_value(profile, "name")
    location = identity_value(profile, "location")
    basics = {
        "name": name,
        "label": infer_label(profile, tailored),
        "email": email,
        "phone": phone,
        "location": {"city": location.split(",")[0].strip() if location else "", "countryCode": "TR", "region": location},
        "summary": infer_summary(profile, tailored),
        "profiles": [],
    }
    if linkedin:
        basics["profiles"].append({"network": "LinkedIn", "username": "", "url": ""})

    work = []
    for item in infer_work_entries(profile, tailored):
        work.append({
            "name": item["name"],
            "position": item["position"],
            "startDate": "",
            "endDate": "",
            "summary": ensure_sentence(item["summary"]),
            "highlights": [ensure_sentence(x) for x in item["highlights"]],
        })

    education = []
    edu_lines = collect_section_items(profile, "education")
    degree, institution = "", ""
    gpa = ""
    for line in edu_lines:
        lower = line.lower()
        if "bachelor" in lower:
            degree, institution = split_title_and_area(line)
        elif lower.startswith("gpa:"):
            gpa = line.split(":", 1)[1].strip()
    if degree or institution:
        education.append({
            "institution": institution or "Sabancı University",
            "area": degree,
            "studyType": "Bachelor's Degree",
            "startDate": "",
            "endDate": "2025",
            "score": gpa,
        })

    skills = [{"name": item, "level": "", "keywords": []} for item in infer_skills(profile, tailored)]

    projects = []
    for item in infer_work_entries(profile, tailored):
        if item["name"] == "Academic and Project Work":
            projects.append({
                "name": item["position"],
                "description": ensure_sentence(item["summary"]),
                "highlights": [ensure_sentence(x) for x in item["highlights"]],
                "keywords": [],
            })

    languages = infer_languages(profile)

    return {
        "$schema": "https://raw.githubusercontent.com/jsonresume/resume-schema/v1.0.0/schema.json",
        "basics": basics,
        "work": work,
        "education": education,
        "skills": skills,
        "languages": languages,
        "projects": projects,
        "meta": {
            "tailoring": {
                "matchScore": tailored.get("match_score", {}).get("score"),
                "matchedKeywords": tailored.get("match_score", {}).get("matched_keywords", []),
                "missingKeywords": tailored.get("match_score", {}).get("missing_keywords", []),
            }
        },
    }


def build_preview_text(json_resume):
    lines = [
        json_resume["basics"].get("name", ""),
        json_resume["basics"].get("label", ""),
        "",
        "SUMMARY",
        json_resume["basics"].get("summary", ""),
        "",
        "EXPERIENCE",
    ]
    for work in json_resume.get("work", []):
        lines.append(f"{work.get('name', '')} — {work.get('position', '')}")
        if work.get("summary"):
            lines.append(work["summary"])
        for bullet in work.get("highlights", []):
            lines.append(f"• {bullet}")
        lines.append("")
    lines.append("EDUCATION")
    for edu in json_resume.get("education", []):
        area = edu.get("area", "")
        institution = edu.get("institution", "")
        score = edu.get("score", "")
        lines.append(f"• {area} — {institution}".strip())
        if score:
            lines.append(f"  GPA: {score}")
    lines.append("")
    lines.append("SKILLS")
    for skill in json_resume.get("skills", [])[:16]:
        lines.append(f"• {skill.get('name', '')}")
    return "\n".join(lines).strip()


def main():
    parser = argparse.ArgumentParser(description="Convert profile + tailored CV output into JSON Resume.")
    parser.add_argument("candidate_profile")
    parser.add_argument("--tailored-cv", required=True, help="Path to cv-tailoring-skill JSON output")
    parser.add_argument("--out", default="resume_builder_output.json")
    args = parser.parse_args()

    profile_text = Path(args.candidate_profile).read_text(encoding="utf-8")
    tailored = json.loads(Path(args.tailored_cv).read_text(encoding="utf-8"))
    profile = parse_candidate_profile(profile_text)
    json_resume = build_json_resume(profile, tailored)

    result = {
        "json_resume": json_resume,
        "preview_text": build_preview_text(json_resume),
        "source_bridge": {
            "profilePath": str(Path(args.candidate_profile).resolve()),
            "tailoredCvPath": str(Path(args.tailored_cv).resolve()),
        },
    }

    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
