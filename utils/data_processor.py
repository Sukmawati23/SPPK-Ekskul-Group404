# utils/data_processor.py
from config import ACADEMIC_CODES as MINAT_MAP
from config import ACTIVITY_CODES as EKSKUL_MAP
from config import SKILL_LIST

def one_hot_encode_skills(skill_string: str):
    selected = [s.strip() for s in skill_string.split(",") if s.strip()]
    return [1 if skill in selected else 0 for skill in SKILL_LIST]

def student_to_vector(profile: dict):
    minat_code = MINAT_MAP.get(profile.get("minat"), 0)
    ekskul_code = EKSKUL_MAP.get(profile.get("ekskul"), 0)
    skills = profile.get("skill", "")
    skill_vector = one_hot_encode_skills(skills)
    contribution = profile.get("contribution", 0)
    achievement = profile.get("achievement", 0)
    club_count = profile.get("club_count", 0)
    return [
        minat_code,
        ekskul_code,
        *skill_vector,
        contribution,
        achievement,
        club_count
    ]