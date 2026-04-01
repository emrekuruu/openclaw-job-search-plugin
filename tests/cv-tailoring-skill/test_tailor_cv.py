from pathlib import Path
import importlib.util

SCRIPT = Path(__file__).resolve().parents[2] / 'skills/cv-tailoring-skill/scripts/tailor_cv.py'
spec = importlib.util.spec_from_file_location('tailor_cv', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def test_extract_keywords_filters_generic_terms():
    job_text = (
        'We are hiring a data analyst with strong SQL, Python, dashboarding, '
        'stakeholder communication, and analytics experience. Product analytics and documentation are a plus.'
    )
    keywords = mod.extract_keywords(job_text)
    assert 'sql' in keywords
    assert 'python' in keywords
    assert 'analytics' in keywords
    assert 'hiring' not in keywords
    assert 'strong' not in keywords
    assert 'experience' not in keywords


def test_compute_match_score_separates_matched_and_missing_keywords():
    keywords = ['sql', 'python', 'dashboarding', 'communication']
    profile_text = 'Data analyst with SQL and Python automation experience.'
    score, matched, missing = mod.compute_match_score(keywords, profile_text)
    assert score == 50.0
    assert matched == ['sql', 'python']
    assert missing == ['dashboarding', 'communication']


def test_extract_relevant_points_prefers_supported_lines_only():
    profile_text = '\n'.join([
        'Junior data analyst',
        '- Built SQL dashboards for weekly reporting',
        '- Worked with product and engineering on API analytics',
        '- Automated recurring reporting tasks with Python',
        '- Enjoys learning quickly',
    ])
    keywords = ['sql', 'python', 'analytics', 'api']
    points = mod.extract_relevant_points(profile_text, keywords)
    texts = [item['text'] for item in points]
    assert 'Built SQL dashboards for weekly reporting' in texts
    assert 'Worked with product and engineering on API analytics' in texts
    assert 'Automated recurring reporting tasks with Python' in texts
    assert 'Enjoys learning quickly' not in texts


def test_build_tailored_cv_preserves_source_grounding():
    profile_text = 'Data analyst with SQL and Python experience.'
    points = [
        {'text': 'Built SQL dashboards for weekly reporting', 'matched_keywords': ['sql']},
        {'text': 'Automated recurring reporting tasks with Python', 'matched_keywords': ['python']},
    ]
    result = mod.build_tailored_cv(profile_text, points, 'Grounded summary')
    assert result['summary'] == 'Grounded summary'
    assert result['highlighted_experience'] == [
        'Built SQL dashboards for weekly reporting',
        'Automated recurring reporting tasks with Python',
    ]
    assert 'Do not invent experience' in result['source_preservation_note']


def test_build_gap_analysis_warns_against_adding_unsupported_requirements():
    result = mod.build_gap_analysis(['sql', 'python'], ['dashboarding', 'communication'])
    assert result['strengths'] == ['sql', 'python']
    assert result['gaps'] == ['dashboarding', 'communication']
    assert any('Do not add' in note for note in result['notes'])
