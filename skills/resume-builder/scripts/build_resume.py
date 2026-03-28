#!/usr/bin/env python3
import argparse
import json
import re
from pathlib import Path


def parse_candidate_profile(text: str):
    data = {
        "identity": {},
        "experience_summary": [],
        "skills": [],
        "education": [],
        "notes": [],
    }
    section = None
    for raw in text.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped == '## Identity':
            section = 'identity'
            continue
        if stripped == '## Experience Summary':
            section = 'experience_summary'
            continue
        if stripped == '## Skills / Keywords':
            section = 'skills'
            continue
        if stripped == '## Education':
            section = 'education'
            continue
        if stripped == '## Notes':
            section = 'notes'
            continue
        if stripped.startswith('## '):
            section = None
            continue

        if section == 'identity' and stripped.startswith('- '):
            body = stripped[2:]
            if ':' in body:
                k, v = body.split(':', 1)
                data['identity'][k.strip().lower()] = v.strip()
        elif section in {'experience_summary', 'skills', 'education', 'notes'} and stripped.startswith('- '):
            key = 'skills' if section == 'skills' else section
            data[key].append(stripped[2:].strip())
    return data


def contains_any(text: str, terms):
    lowered = text.lower()
    return any(term.lower() in lowered for term in terms)


def extract_job_signals(job_text: str):
    signals = {
        'role': 'Software Engineer, Fullstack' if 'fullstack' in job_text.lower() else 'Software Engineer',
        'backend_fullstack': True,
        'must_have': [],
        'nice_to_have': [],
    }
    must_terms = [
        'NodeJS', 'JavaScript', 'HTML', 'CSS', 'Vue', 'React', 'RESTful APIs', 'Git', 'unit/integration testing', 'English'
    ]
    nice_terms = ['Google Cloud', 'Pub/Sub', 'Functions', 'App Engine', 'Vue3', 'Firestore', 'Redis', 'Memcached']
    for term in must_terms:
        if term.lower() in job_text.lower():
            signals['must_have'].append(term)
    for term in nice_terms:
        if term.lower() in job_text.lower():
            signals['nice_to_have'].append(term)
    return signals


def strongest_techs(skills):
    ordered = ['Java', 'Spring Boot', 'React', 'PostgreSQL', 'JavaScript', 'Python', 'SQL', 'Git']
    skill_text = ' | '.join(skills)
    return [tech for tech in ordered if tech.lower() in skill_text.lower()]


def build_summary(profile, job_signals):
    techs = strongest_techs(profile['skills'])
    lead = ', '.join(techs[:4]) if techs else 'Java, React, PostgreSQL, Python'
    title = 'Junior Backend / Full-Stack Software Engineer'
    return (
        f"{title} with hands-on experience building software using {lead}. "
        "Background includes backend and BFF development for an internal banking application, frontend implementation in React, "
        "data access with PostgreSQL, and API-integrated application development. "
        "Targeting backend and full-stack roles where strong engineering fundamentals, product thinking, and maintainable delivery matter."
    )


def build_experience(profile):
    return [
        {
            'company': 'Yapı Kredi Teknoloji',
            'title': 'Software Engineering Intern',
            'bullets': [
                'Built features for an internal banking application using React on the frontend and Java with Spring Boot on backend and BFF layers, supporting efficient and secure workflows for internal users.',
                'Implemented full-stack application logic across frontend, backend, and data-access layers, using PostgreSQL to support core banking application functionality.',
                'Delivered software in a banking technology environment where application reliability, maintainability, and secure behavior were central to the product context.'
            ]
        },
        {
            'company': 'Asis Elektronik ve Bilişim Sistemleri',
            'title': 'Software Engineering / Mobile Development Intern',
            'bullets': [
                'Built mobile application functionality for real-time bus tracking and card balance inquiry, focusing on user-facing transport and balance features.',
                'Integrated open data APIs into the application flow to support live data retrieval and feature behavior tied to real-time public transportation use cases.',
                'Developed within an Android MVVM architecture to keep mobile application code organized and maintainable as features evolved.'
            ]
        },
        {
            'company': 'Academic and Project Work',
            'title': 'Software Projects',
            'bullets': [
                'Built software projects with Django, React, MySQL, and Python across web development, data-oriented systems, and route optimization use cases.',
                'Applied machine learning and data science techniques in academic and project settings to support analytical and software engineering problem-solving.'
            ]
        }
    ]


def build_skills(profile, job_signals):
    all_skills = profile['skills']
    categories = {
        'Languages': ['Java', 'Python', 'JavaScript', 'SQL', 'C#', 'C++'],
        'Frameworks & Platforms': ['Spring Boot', 'React', 'Django', 'PostgreSQL', 'MongoDB', 'Android Studio'],
        'Engineering': ['backend', 'full stack', 'frontend', 'unit testing', 'Git'],
    }
    result = {}
    joined = ' | '.join(all_skills)
    for k, vals in categories.items():
        result[k] = [v for v in vals if v.lower() in joined.lower()]
    return result


def build_gap_analysis(profile, job_signals):
    joined = ' | '.join(profile['skills'] + profile['experience_summary'])
    missing = []
    for term in job_signals['must_have'] + job_signals['nice_to_have']:
        if term.lower() not in joined.lower():
            missing.append(term)
    return {
        'supported': [term for term in job_signals['must_have'] if term.lower() in joined.lower()],
        'unsupported': missing,
        'notes': [
            'Keep backend/full-stack emphasis on React, Java, Spring Boot, PostgreSQL, JavaScript, Git, unit testing, and API integration where supported.',
            'Do not claim NodeJS, Vue/Vue3, GCP, Firestore, Redis, Memcached, or integration testing unless the candidate confirms them.'
        ]
    }


def build_polished_text(name, headline, summary, experience, education, skills, notes):
    lines = []
    lines.append(name)
    lines.append(headline)
    lines.append('')
    lines.append('SUMMARY')
    lines.append(summary)
    lines.append('')
    lines.append('EXPERIENCE')
    for item in experience:
        lines.append(f"{item['company']} — {item['title']}")
        for bullet in item['bullets']:
            lines.append(f"- {bullet}")
        lines.append('')
    lines.append('EDUCATION')
    for item in education:
        lines.append(f"- {item}")
    lines.append('')
    lines.append('SKILLS')
    for k, vals in skills.items():
        if vals:
            lines.append(f"- {k}: {', '.join(vals)}")
    lines.append('')
    lines.append('LANGUAGES')
    for n in notes:
        if n.lower().startswith('turkish:') or n.lower().startswith('english:') or n.lower().startswith('german:'):
            lines.append(f"- {n}")
    return '\n'.join(lines).strip()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('candidate_profile')
    parser.add_argument('job_description')
    parser.add_argument('--out', default='resume_builder_output.json')
    args = parser.parse_args()

    profile_text = Path(args.candidate_profile).read_text(encoding='utf-8')
    job_text = Path(args.job_description).read_text(encoding='utf-8')
    profile = parse_candidate_profile(profile_text)
    job_signals = extract_job_signals(job_text)

    name = profile['identity'].get('name', '')
    headline = 'Junior Backend / Full-Stack Software Engineer'
    summary = build_summary(profile, job_signals)
    experience = build_experience(profile)
    education = profile['education']
    skills = build_skills(profile, job_signals)
    gaps = build_gap_analysis(profile, job_signals)

    result = {
        'structured_resume': {
            'target_role': job_signals['role'],
            'headline': headline,
            'summary': summary,
            'experience': experience,
            'education': education,
            'skills': skills,
            'gap_analysis': gaps,
        },
        'polished_resume': build_polished_text(name, headline, summary, experience, education, skills, profile['notes'])
    }

    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'Wrote {args.out}')


if __name__ == '__main__':
    main()
