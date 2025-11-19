import spacy

nlp = spacy.load("en_core_web_lg")

DOMAIN_MAP = {
    # Frontend / UI/UX
    "design": ["figma", "adobe xd", "prototyping", "ui", "ux"],
    "prototype": ["figma", "adobe xd", "prototyping", "ui"],
    "ui": ["figma", "adobe xd", "prototyping"],
    "ux": ["figma", "adobe xd", "prototyping"],

    # Backend
    "backend": ["python", "django", "postgresql", "api"],
    "api": ["python", "django", "postgresql"],
    "database": ["postgresql", "sql"],
    "django": ["python", "backend"],

    # Data Science
    "machine": ["machine learning", "python", "tensorflow"],
    "learning": ["machine learning", "python", "tensorflow"],
    "model": ["machine learning", "tensorflow"],
    "analysis": ["pandas", "powerbi", "python"],

    # DevOps
    "deploy": ["aws", "docker", "ci/cd"],
    "pipeline": ["ci/cd", "docker", "aws"],
    "cloud": ["aws", "docker"],
    "infrastructure": ["aws", "docker"],

    # QA / Testing
    "test": ["selenium", "cypress", "testing"],
    "automated": ["selenium", "cypress"],
    "quality": ["selenium", "cypress"],

    # PM
    "plan": ["leadership", "agile", "scrum"],
    "sprint": ["agile", "scrum"],
    "manage": ["leadership", "agile", "scrum"],
}


def extract_keywords(task_text):
    doc = nlp(task_text.lower())
    return [token.lemma_ for token in doc if token.pos_ in {"NOUN", "VERB"}]

def expand_keywords(keywords):
    expanded = set(keywords)
    for w in keywords:
        if w in DOMAIN_MAP:
            expanded.update(DOMAIN_MAP[w])
    return list(expanded)

def semantic_score(task_text, skill_text):
    if not skill_text.strip():
        return 0
    return nlp(task_text).similarity(nlp(skill_text))

def score_employee(task_text, employee_skills):
    keywords = extract_keywords(task_text)
    expanded = expand_keywords(keywords)

    # matched skills
    matched = list(set(expanded) & set(employee_skills))

    # keyword score
    if expanded:
        kw_score = len(matched) / len(expanded)
    else:
        kw_score = 0

    # semantic score
    skill_string = " ".join(employee_skills)
    sem = semantic_score(task_text, skill_string)

    # hybrid
    final = 0.6 * sem + 0.4 * kw_score

    return final, matched
