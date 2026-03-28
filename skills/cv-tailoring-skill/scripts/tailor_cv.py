#!/usr/bin/env python3
import argparse
import json
import re
from collections import Counter
from pathlib import Path

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9+.#/-]{1,}")
BULLET_RE = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s+")

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "your", "their", "will", "have", "has", "had",
    "are", "was", "were", "job", "role", "team", "using", "use", "used", "you", "our", "about", "across",
    "within", "than", "then", "also", "such", "each", "other", "more", "most", "very", "not", "but", "all",
    "any", "who", "what", "when", "where", "why", "how", "can", "should", "must", "nice", "plus", "etc",
    "hiring", "strong", "required", "preferred", "experience", "responsibilities", "responsibility", "qualification",
    "qualifications", "candidate", "support", "supporting"
}

SECTION_HINTS = [
    "summary",
    "experience",
    "work experience",
    "projects",
    "skills",
    "education",
    "certifications",
]


def normalize_token(token: str):
    return token.lower().strip(".,;:!?()[]{}\"'")


def words(text: str):
    return [normalize_token(w) for w in WORD_RE.findall(text) if normalize_token(w)]


def sentence_split(text: str):
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def extract_keywords(job_text: str, limit: int = 40):
    freq = Counter(w for w in words(job_text) if len(w) > 2 and w not in STOPWORDS)
    return [w for w, _ in freq.most_common(limit)]


def extract_lines(text: str):
    lines = [ln.rstrip() for ln in text.splitlines()]
    return [ln for ln in lines if ln.strip()]


def score_line(line: str, keywords):
    lowered = line.lower()
    score = 0
    hits = []
    for kw in keywords:
        if kw in lowered:
            score += 1
            hits.append(kw)
    return score, hits


def extract_relevant_points(profile_text: str, keywords, limit: int = 12):
    candidates = []
    for line in extract_lines(profile_text):
        clean = BULLET_RE.sub("", line).strip()
        if not clean:
            continue
        score, hits = score_line(clean, keywords)
        if score > 0:
            candidates.append((score, len(clean), clean, hits))

    if not candidates:
        for sent in sentence_split(profile_text):
            score, hits = score_line(sent, keywords)
            if score > 0:
                candidates.append((score, len(sent), sent, hits))

    candidates.sort(key=lambda x: (-x[0], x[1]))
    seen = set()
    selected = []
    for score, _, text, hits in candidates:
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        selected.append({"text": text, "matched_keywords": hits})
        if len(selected) >= limit:
            break
    return selected


def build_summary(points, keywords):
    if not points:
        return "Candidate profile needs more role-relevant detail before a truthful tailored summary can be produced."

    top_terms = []
    seen = set()
    for item in points:
        for kw in item["matched_keywords"]:
            if kw not in seen:
                seen.add(kw)
                top_terms.append(kw)
            if len(top_terms) >= 6:
                break
        if len(top_terms) >= 6:
            break

    if not top_terms:
        top_terms = keywords[:6]

    return (
        "Profile emphasizes experience relevant to "
        + ", ".join(top_terms)
        + ". Tailor section ordering and bullet emphasis around these verified areas only."
    )


def compute_match_score(keywords, profile_text):
    profile_words = set(words(profile_text))
    matched = [kw for kw in keywords if kw in profile_words]
    missing = [kw for kw in keywords if kw not in profile_words]
    score = round(100 * len(matched) / max(len(keywords), 1), 1)
    return score, matched, missing


def build_gap_analysis(missing_keywords, matched_keywords):
    strengths = matched_keywords[:12]
    gaps = missing_keywords[:12]
    notes = []
    if gaps:
        notes.append("These keywords appear in the job description but are not clearly supported in the candidate profile.")
        notes.append("Do not add them unless the candidate confirms real experience.")
    else:
        notes.append("The profile already covers most top keywords extracted from the job description.")

    return {
        "strengths": strengths,
        "gaps": gaps,
        "notes": notes,
    }


def build_tailored_cv(profile_text, points, summary_text):
    skills_lines = []
    for line in extract_lines(profile_text):
        lowered = line.lower()
        if any(hint in lowered for hint in ["python", "sql", "excel", "aws", "docker", "kubernetes", "product", "analytics", "api"]):
            cleaned = BULLET_RE.sub("", line).strip()
            if cleaned and cleaned not in skills_lines:
                skills_lines.append(cleaned)
        if len(skills_lines) >= 8:
            break

    return {
        "summary": summary_text,
        "highlighted_experience": [p["text"] for p in points[:8]],
        "skills_or_keywords": skills_lines[:8],
        "source_preservation_note": "All content is derived from the provided candidate profile. Reorder and rewrite only."
    }


def main():
    parser = argparse.ArgumentParser(description="Tailor a CV to a job description without inventing experience.")
    parser.add_argument("candidate_profile_txt", help="Path to candidate profile or CV text file")
    parser.add_argument("job_description_txt", help="Path to job description text file")
    parser.add_argument("--out", default="cv_tailoring_output.json", help="Output JSON file path")
    args = parser.parse_args()

    profile_text = Path(args.candidate_profile_txt).read_text(encoding="utf-8")
    job_text = Path(args.job_description_txt).read_text(encoding="utf-8")

    keywords = extract_keywords(job_text)
    match_score, matched, missing = compute_match_score(keywords, profile_text)
    points = extract_relevant_points(profile_text, keywords)
    summary_text = build_summary(points, keywords)

    payload = {
        "tailored_cv": build_tailored_cv(profile_text, points, summary_text),
        "match_score": {
            "score": match_score,
            "matched_keywords": matched,
            "missing_keywords": missing,
            "method": "Simple keyword coverage against extracted job-description terms"
        },
        "gap_analysis": build_gap_analysis(missing, matched),
        "keyword_pool": keywords
    }

    Path(args.out).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
