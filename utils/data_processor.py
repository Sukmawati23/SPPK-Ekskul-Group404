# utils/data_processor.py

MINAT_MAP = {
    "IPA": 1,
    "IPS": 2,
    "Bahasa": 3
}

EKSKUL_MAP = {
    "Paskibra": 1,
    "Musik": 2,
    "Tari": 3,
    "Science Club": 4,
    "Futsal": 5,
    "Teater": 6,
    "Robotik": 7,
    "PMR": 8,
    "Basket": 9,
    "Jurnalistik": 10
}

SKILL_LIST = [
    "Public Speaking",
    "Analisis Data",
    "Menulis",
    "Leadership",
    "Desain",
    "Negoisasi"
]

def one_hot_encode_skills(skill_string: str):
    selected = [s.strip() for s in skill_string.split(",") if s.strip()]
    return [1 if skill in selected else 0 for skill in SKILL_LIST]


def student_to_vector(profile: dict):
    """Mengubah satu data siswa (dict) menjadi vektor numerik lengkap"""

    minat_code = MINAT_MAP.get(profile.get("minat"), 0)
    ekskul_code = EKSKUL_MAP.get(profile.get("ekskul"), 0)

    skills = profile.get("skill", "")
    skill_vector = one_hot_encode_skills(skills)

    contribution = profile.get("contribution", 0)
    achievement = profile.get("achievement", 0)
    club_count = profile.get("club_count", 0)

    # Vektor lengkap
    return [
        minat_code,
        ekskul_code,
        *skill_vector,
        contribution,
        achievement,
        club_count
    ]