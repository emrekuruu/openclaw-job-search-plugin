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


def slugify(text: str) -> str:
    value = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return value or "item"


def clean_bullet(text: str) -> str:
    return re.sub(r"^\s*(?:[-*•]|\d+[.)])\s+", "", text).strip()


def split_title_and_area(line: str):
    parts = [p.strip() for p in line.split(",")]
    if not parts:
        return "", ""
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], ", ".join(parts[1:])


def infer_label(profile, tailored):
    desired_roles = []
    for entry in profile["sections"].get("target_direction", []):
        if isinstance(entry, dict) and entry.get("label") == "Desired roles":
            desired_roles.extend(entry.get("items", []))
    preferred = [
        "Backend Engineer",
        "Full Stack Engineer",
        "Software Engineer",
        "Junior Software Engineer",
        "Full Stack Developer",
        "Java Developer",
        "Python Developer",
    ]
    for role in preferred:
        if role in desired_roles:
            return role
    current_title = identity_value(profile, "current title")
    if current_title:
        return current_title
    matched = tailored.get("match_score", {}).get("matched_keywords", [])
    if "backend" in matched:
        return "Backend Engineer"
    if "full" in matched and "stack" in matched:
        return "Full Stack Engineer"
    return "Software Engineer"


def infer_summary(profile, tailored):
    summary = tailored.get("tailored_cv", {}).get("summary", "").strip()
    if summary:
        return summary
    exp = collect_section_items(profile, "experience_summary")
    return exp[0] if exp else "Early-career software engineer with truthful, profile-grounded experience."


def infer_work_entries(profile, tailored):
    experience_lines = collect_section_items(profile, "experience_summary")
    tailored_points = [clean_bullet(x) for x in tailored.get("tailored_cv", {}).get("highlighted_experience", []) if clean_bullet(x)]
    entries = []

    if any("yapı kredi teknoloji" in line.lower() for line in experience_lines):
        bullets = []
        for point in tailored_points:
            lower = point.lower()
            if any(term in lower for term in ["bank", "react", "spring", "postgres", "backend", "bff"]):
                bullets.append(point)
        if not bullets:
            bullets = [
                "Built software for internal banking applications with a focus on efficiency and security.",
                "Worked across React frontend flows plus Java and Spring Boot backend/BFF layers.",
                "Managed PostgreSQL-backed data access for internal application workflows.",
            ]
        entries.append({
            "name": "Yapı Kredi Teknoloji",
            "position": "Software Engineering Intern",
            "summary": "Internal banking application engineering internship.",
            "highlights": bullets[:4],
        })

    if any("asis elektronik" in line.lower() for line in experience_lines):
        bullets = []
        for point in tailored_points:
            lower = point.lower()
            if any(term in lower for term in ["bus", "mvvm", "android", "api"]):
                bullets.append(point)
        if not bullets:
            bullets = [
                "Developed mobile application features for real-time bus tracking and card balance inquiry.",
                "Integrated open data APIs in an Android MVVM architecture.",
            ]
        entries.append({
            "name": "Asis Elektronik ve Bilişim Sistemleri",
            "position": "Software Engineering / Mobile Development Intern",
            "summary": "Mobile application and API-integration internship.",
            "highlights": bullets[:4],
        })

    project_lines = [line for line in experience_lines if any(term in line.lower() for term in ["django", "machine learning", "route optimization", "mysql", "python"])]
    if project_lines:
        entries.append({
            "name": "Academic and Project Work",
            "position": "Software Projects",
            "summary": "Selected academic and personal software projects.",
            "highlights": project_lines[:4],
        })

    return entries


def infer_skills(profile, tailored):
    skill_items = collect_section_items(profile, "skills")
    matched = tailored.get("match_score", {}).get("matched_keywords", [])
    prioritized = []
    leftovers = []
    for item in skill_items:
        lower = item.lower()
        if any(keyword.lower() in lower for keyword in matched):
            prioritized.append(item)
        else:
            leftovers.append(item)
    ordered = []
    seen = set()
    for item in prioritized + leftovers:
        norm = item.lower()
        if norm not in seen:
            seen.add(norm)
            ordered.append(item)
    return ordered


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
            "summary": item["summary"],
            "highlights": item["highlights"],
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

    skills = []
    for item in infer_skills(profile, tailored):
        skills.append({"name": item, "level": "", "keywords": []})

    projects = []
    for item in infer_work_entries(profile, tailored):
        if item["name"] == "Academic and Project Work":
            projects.append({
                "name": item["position"],
                "description": item["summary"],
                "highlights": item["highlights"],
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
        for bullet in work.get("highlights", []):
            lines.append(f"• {bullet}")
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
