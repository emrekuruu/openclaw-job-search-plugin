#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter
from html import escape
from pathlib import Path

HEADING_RE = re.compile(r"^##\s+(.*)$")
TITLE_RE = re.compile(r"^#\s+(.*)$")
ROLE_RE = re.compile(r"^\*\*(.+?)\*\*$")
BULLET_RE = re.compile(r"^\s*[-*•]\s+")
WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/-]{1,}")
STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "their", "will", "have", "has", "had",
    "are", "was", "were", "job", "role", "team", "using", "use", "used", "you", "our", "about", "across",
    "within", "than", "then", "also", "such", "each", "other", "more", "most", "very", "not", "but", "all",
    "any", "who", "what", "when", "where", "why", "how", "can", "should", "must", "nice", "plus", "etc",
    "hiring", "strong", "required", "preferred", "experience", "responsibilities", "responsibility", "qualification",
    "qualifications", "candidate", "support", "supporting", "company", "work", "working", "ability", "build",
    "built", "develop", "developing", "development", "product", "technology", "systems", "system", "looking",
}

KEYWORD_PRIORITY = {
    "javascript": 8,
    "typescript": 8,
    "react": 9,
    "next.js": 8,
    "node.js": 8,
    "node": 7,
    "postgresql": 8,
    "mysql": 7,
    "sql": 7,
    "git": 6,
    "github": 5,
    "api": 7,
    "apis": 7,
    "rest": 7,
    "graphql": 7,
    "websockets": 7,
    "backend": 8,
    "frontend": 8,
    "full-stack": 9,
    "fullstack": 9,
    "aws": 7,
    "redis": 7,
    "mongodb": 6,
    "ci/cd": 6,
    "microservices": 6,
    "testing": 6,
}

PROJECT_RELEVANCE_HINTS = {
    "web": ["react", "django", "mysql", "postgresql", "javascript", "api", "frontend", "backend", "full-stack", "web", "e-commerce"],
    "mobile": ["android", "mobile", "mvvm", "api", "tracking"],
    "game": ["unity", "game", "gameplay", "grid", "animation", "prototype"],
    "data": ["machine learning", "data", "optimization", "route", "analytics", "python"],
}


def normalize_token(token: str):
    return token.lower().strip(".,;:!?()[]{}\"'")


def words(text: str):
    return [normalize_token(w) for w in WORD_RE.findall(text) if normalize_token(w)]


def extract_keywords(job_text: str, limit: int = 50):
    tokens = words(job_text)
    freq = Counter(w for w in tokens if len(w) > 2 and w not in STOPWORDS)
    boosted = []
    lowered = job_text.lower()
    for key, weight in KEYWORD_PRIORITY.items():
        if key in lowered:
            boosted.extend([key] * weight)
    combined = Counter(freq)
    combined.update(boosted)
    ordered = [w for w, _ in combined.most_common(limit)]
    return ordered


def parse_markdown_cv(text: str):
    result = {"name": "", "contact": "", "sections": [], "section_map": {}}
    current = None
    current_entry = None

    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        m_title = TITLE_RE.match(stripped)
        if m_title:
            result["name"] = m_title.group(1).strip()
            continue
        m_heading = HEADING_RE.match(stripped)
        if m_heading:
            current = {"title": m_heading.group(1).strip(), "entries": []}
            result["sections"].append(current)
            result["section_map"][current["title"].lower()] = current
            current_entry = None
            continue
        if not result["contact"] and not stripped.startswith("##"):
            result["contact"] = stripped
            continue
        if current is None:
            continue
        m_role = ROLE_RE.match(stripped)
        if m_role:
            current_entry = {"title": m_role.group(1).strip(), "bullets": [], "lines": []}
            current["entries"].append(current_entry)
            continue
        if BULLET_RE.match(stripped):
            bullet = BULLET_RE.sub("", stripped).strip()
            if current_entry is None:
                current_entry = {"title": "", "bullets": [], "lines": []}
                current["entries"].append(current_entry)
            current_entry["bullets"].append(bullet)
            continue
        if current_entry is None:
            current_entry = {"title": "", "bullets": [], "lines": []}
            current["entries"].append(current_entry)
        current_entry["lines"].append(stripped)
    return result


def role_buckets(job_text: str):
    lowered = job_text.lower()
    buckets = []
    if any(term in lowered for term in ["react", "next.js", "node.js", "full-stack", "frontend", "backend", "api", "graphql", "websocket"]):
        buckets.append("web")
    if any(term in lowered for term in ["android", "mobile", "ios"]):
        buckets.append("mobile")
    if any(term in lowered for term in ["machine learning", "analytics", "data science", "optimization"]):
        buckets.append("data")
    if any(term in lowered for term in ["unity", "game", "gameplay"]):
        buckets.append("game")
    return buckets or ["web"]


def score_text(text: str, keywords):
    lowered = text.lower()
    score = 0
    for kw in keywords:
        if kw in lowered:
            score += KEYWORD_PRIORITY.get(kw, 1)
    return score


def split_skills(skill_line: str):
    if "|" in skill_line:
        return [item.strip() for item in skill_line.split("|") if item.strip()]
    return [item.strip() for item in skill_line.split(",") if item.strip()]


def join_skills(skills, separator):
    sep = f" {separator} "
    return sep.join(skills)


def reorder_skills(skill_line: str, keywords):
    separator = "|" if "|" in skill_line else ","
    skills = split_skills(skill_line)

    def skill_score(skill):
        lower = skill.lower()
        score = score_text(lower, keywords)
        if any(k in lower for k in ["javascript", "react", "backend", "frontend", "full-stack", "git", "sql", "postgresql", "mysql", "api"]):
            score += 6
        if any(k in lower for k in ["turkish", "english", "german"]):
            score -= 5
        return score

    ranked = sorted(skills, key=lambda s: (-skill_score(s), skills.index(s)))
    return join_skills(ranked, separator)


def ensure_period(text: str):
    text = text.strip()
    if not text:
        return text
    if text.endswith((".", "!", "?")):
        return text
    return text + "."


def paraphrase_bullet(bullet: str, job_text: str):
    text = bullet.strip().rstrip(".")
    lower = text.lower()

    exact_rewrites = {
        "developing a full-stack banking application for internal worker use, focusing on efficiency and security": "Contributed to the development of a full-stack banking application for internal users, with an emphasis on efficiency and security",
        "utilizing react for the frontend and backend integration to streamline banking operations": "Leveraged React for frontend development and backend integration to support internal banking workflows",
        "developed backend and bff layers using java and spring boot, and managed data access via postgresql": "Developed backend and BFF layers with Java and Spring Boot while managing application data access through PostgreSQL",
        "developed a mobile application for real time bus tracking and card balance inquiry": "Developed a mobile application for real-time bus tracking and card balance inquiry",
        "integrated tfe open data api for real bus route information": "Integrated the TFE Open Data API to deliver real-time bus route information to end users",
        "utilized mvvm architecture to ensure maintainability and code efficiency": "Applied MVVM architecture to improve maintainability and code efficiency in the Android application",
        "developed a full-stack e-commerce platform for bag sales, incorporating user-friendly product display and purchase features": "Developed a full-stack e-commerce platform for bag sales, including user-friendly product display and purchase flows",
        "utilized django, mysql, and react to ensure a scalable and efficient system": "Used Django, MySQL, and React to deliver a scalable and efficient web application architecture",
        "developed a system to optimize delivery routes using smart algorithms": "Developed a decision-support system to optimize delivery routes using algorithmic approaches",
        "created a simple method for assigning parcels to nearby lockers": "Designed a parcel-assignment approach for routing deliveries to nearby lockers",
        "built a user-friendly web app to display routes on an interactive map": "Built a user-facing web application to visualize delivery routes on an interactive map",
        "created a mobile application called reciπ, where users can view and add recipes, as well as comment on them": "Developed a mobile application called Reciπ that allows users to browse, add, and comment on recipes",
        "gathered, cleaned, and analyzed data using python, creating machine learning prediction models for insights": "Collected, cleaned, and analyzed data with Python while developing machine learning models to generate predictive insights",
        "produced a podcast series on the mucilage problem affecting semi-enclosed seas such as marmara sea": "Produced a podcast series focused on the mucilage problem affecting semi-enclosed seas such as the Marmara Sea",
    }
    if lower in exact_rewrites:
        return ensure_period(exact_rewrites[lower])

    if lower.startswith("developed "):
        text = "Developed " + text[len("developed "):]
    elif lower.startswith("developing "):
        text = "Contributed to the development of " + text[len("developing "):]
    elif lower.startswith("utilizing "):
        text = "Leveraged " + text[len("utilizing "):]
    elif lower.startswith("utilized "):
        text = "Leveraged " + text[len("utilized "):]
    elif lower.startswith("worked on "):
        text = "Contributed to " + text[len("worked on "):]
    elif lower.startswith("built "):
        text = "Built " + text[len("built "):]
    elif lower.startswith("created "):
        text = "Created " + text[len("created "):]
    elif lower.startswith("integrated "):
        text = "Integrated " + text[len("integrated "):]

    text = text.replace("real time", "real-time")
    return ensure_period(text)


def tailor_experience(section, keywords, job_text):
    for entry in section["entries"]:
        bullets = entry.get("bullets", [])
        scored = sorted(bullets, key=lambda b: (-score_text(b, keywords), bullets.index(b)))
        entry["bullets"] = [paraphrase_bullet(b, job_text) for b in scored]
    return section


def project_bucket_score(entry, active_buckets, keywords):
    text = " ".join([entry.get("title", "")] + entry.get("bullets", []) + entry.get("lines", [])).lower()
    bucket_score = 0
    for bucket in active_buckets:
        bucket_score += sum(KEYWORD_PRIORITY.get(hint, 2) for hint in PROJECT_RELEVANCE_HINTS[bucket] if hint in text)
    return bucket_score + score_text(text, keywords)


def parse_additional_info_projects(additional_info_text):
    additional_lines = [ln.rstrip() for ln in additional_info_text.splitlines() if ln.strip()]
    extra_entries = []
    current = []
    current_title = None
    for line in additional_lines:
        stripped = line.strip()
        if stripped.startswith("**") and stripped.endswith("**"):
            if current_title:
                extra_entries.append({"title": current_title, "bullets": current, "lines": []})
            current_title = stripped.strip("*")
            current = []
        elif BULLET_RE.match(stripped):
            current.append(BULLET_RE.sub("", stripped).strip())
    if current_title:
        extra_entries.append({"title": current_title, "bullets": current, "lines": []})
    return extra_entries


def swap_projects(section, additional_info_text, job_text, keywords):
    active_buckets = role_buckets(job_text)
    entries = list(section["entries"])
    entries.sort(key=lambda e: -project_bucket_score(e, active_buckets, keywords))

    ranked_extra = [e for e in parse_additional_info_projects(additional_info_text) if project_bucket_score(e, active_buckets, keywords) > 0]
    ranked_extra.sort(key=lambda e: -project_bucket_score(e, active_buckets, keywords))

    if ranked_extra and entries:
        worst_existing = min(entries, key=lambda e: project_bucket_score(e, active_buckets, keywords))
        best_extra = ranked_extra[0]
        if project_bucket_score(best_extra, active_buckets, keywords) > project_bucket_score(worst_existing, active_buckets, keywords) + 5:
            entries.remove(worst_existing)
            entries.append(best_extra)

    entries.sort(key=lambda e: -project_bucket_score(e, active_buckets, keywords))
    for entry in entries:
        entry["bullets"] = [paraphrase_bullet(b, job_text) for b in entry.get("bullets", [])]
    section["entries"] = entries
    return section


def render_markdown(cv):
    lines = [f"# {cv['name']}", cv["contact"], ""]
    for section in cv["sections"]:
        lines.append(f"## {section['title']}")
        for entry in section["entries"]:
            if entry.get("title"):
                lines.append(f"**{entry['title']}**")
            for line in entry.get("lines", []):
                lines.append(line)
            for bullet in entry.get("bullets", []):
                lines.append(f"- {bullet}")
            lines.append("")
    return "\n".join(lines).strip() + "\n"


def render_html(cv):
    body = [f"<h1>{escape(cv['name'])}</h1>", f"<div class='contact'>{escape(cv['contact'])}</div>"]
    for section in cv["sections"]:
        body.append(f"<h2>{escape(section['title'])}</h2>")
        for entry in section["entries"]:
            if entry.get("title"):
                body.append(f"<div class='entry-title'>{escape(entry['title'])}</div>")
            for line in entry.get("lines", []):
                body.append(f"<div class='line'>{escape(line)}</div>")
            if entry.get("bullets"):
                body.append("<ul>")
                for bullet in entry["bullets"]:
                    body.append(f"<li>{escape(bullet)}</li>")
                body.append("</ul>")
    return f"""<!doctype html>
<html><head><meta charset='utf-8'><title>{escape(cv['name'])}</title>
<style>
body {{ font-family: Arial, Helvetica, sans-serif; color:#111; background:#fff; margin:0; }}
.page {{ width:210mm; min-height:297mm; padding:16mm; box-sizing:border-box; margin:0 auto; }}
h1 {{ font-size:26px; margin:0 0 6px; }}
.contact {{ color:#555; font-size:12.5px; margin-bottom:14px; }}
h2 {{ font-size:15px; margin:16px 0 8px; border-bottom:1px solid #ddd; padding-bottom:4px; }}
.entry-title {{ font-size:13px; font-weight:700; margin:8px 0 4px; }}
.line, li {{ font-size:12.5px; line-height:1.38; }}
ul {{ margin:6px 0 10px 18px; padding:0; }}
</style></head><body><div class='page'>{''.join(body)}</div></body></html>"""


def main():
    parser = argparse.ArgumentParser(description="Preserve base CV structure while tailoring wording and ordering to a job description.")
    parser.add_argument("base_cv", help="Path to base CV in markdown/text form")
    parser.add_argument("job_description", help="Path to job description text file")
    parser.add_argument("--additional-info", default="", help="Optional path to additional verified info in markdown/text form")
    parser.add_argument("--out-md", required=True, help="Output tailored markdown CV path")
    parser.add_argument("--out-html", help="Optional output HTML path")
    parser.add_argument("--plan-out", help="Optional output JSON plan path")
    args = parser.parse_args()

    base_text = Path(args.base_cv).read_text(encoding="utf-8")
    job_text = Path(args.job_description).read_text(encoding="utf-8")
    additional_info_text = Path(args.additional_info).read_text(encoding="utf-8") if args.additional_info else ""

    cv = parse_markdown_cv(base_text)
    keywords = extract_keywords(job_text)

    for section in cv["sections"]:
        title = section["title"].lower()
        if title == "skills" and section["entries"]:
            joined = " | ".join(section["entries"][0].get("lines", []))
            reordered = reorder_skills(joined, keywords)
            section["entries"] = [{"title": "", "bullets": [], "lines": [reordered]}]
        elif title == "experience":
            tailor_experience(section, keywords, job_text)
        elif title == "projects":
            swap_projects(section, additional_info_text, job_text, keywords)

    out_md = Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    out_md.write_text(render_markdown(cv), encoding="utf-8")

    if args.out_html:
        out_html = Path(args.out_html)
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(render_html(cv), encoding="utf-8")

    if args.plan_out:
        plan = {
            "template_lock": {
                "section_order": [s["title"] for s in cv["sections"]],
                "preserve_titles": True,
                "preserve_style": True,
            },
            "editable_regions": {
                "skills": "reorder-only",
                "experience": "rewrite-and-reorder-bullets",
                "projects": "reorder-or-swap-with-verified-additional-info",
                "education": "preserve",
                "volunteer_work": "preserve",
                "activities": "preserve",
            },
            "keyword_pool": keywords,
        }
        Path(args.plan_out).write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {out_md}")
    if args.out_html:
        print(f"Wrote {args.out_html}")


if __name__ == "__main__":
    main()
