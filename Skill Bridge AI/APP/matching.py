def normalize_skills(value):
    if isinstance(value, str):
        return [x.strip().lower() for x in value.split(",") if x.strip()]
    return [str(x).strip().lower() for x in (value or []) if str(x).strip()]

def match_opportunity(student_skills, required_skills):
    """
    Explainable baseline matcher:
    - score = proportion of required skills evidenced by the student
    - level and evidence confidence are shown separately, not hidden in an opaque model
    """
    have = {s["name"].strip().lower(): s for s in student_skills}
    required = normalize_skills(required_skills)
    if not required:
        return {"score": 0, "matched": [], "missing": [], "explanation": "No required skills were provided."}
    matched, missing = [], []
    for skill in required:
        if skill in have:
            matched.append(skill)
        else:
            missing.append(skill)
    score = round((len(matched) / len(required)) * 100)
    if score >= 80:
        explanation = "Strong match: most required skills are present in your Skill Passport."
    elif score >= 50:
        explanation = "Promising match: build the missing skills before or alongside applying."
    else:
        explanation = "Early-stage match: use the gap list to prepare for this opportunity."
    return {"score": score, "matched": matched, "missing": missing, "explanation": explanation}
