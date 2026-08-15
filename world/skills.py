"""
Skills

Mirrors the skill dictionaries from EntityStats in the Godot port
(combat_skills, magick_skills, life_skills, survival_skills). Keeping
the exact same skill names/categories here means character data stays
portable between the two implementations.

Skill names are stored and displayed in the same PascalCase used on
the Godot side; lookups are case-insensitive.
"""

SKILL_CATEGORIES = {
    "Combat Skills": [
        "Archery", "DualWield", "Evasion", "GreatWeapon",
        "HeavyArmor", "MediumArmor", "LightArmor",
        "MartialArts", "OneHand", "ThrownWeapon",
    ],
    "Magick Skills": [
        "Abjuration", "Arcana", "Charm", "Conjuration",
        "Divination", "Evocation", "Illusion",
        "Necromancy", "Transmutation",
    ],
    "Survival Skills": [
        "Athletics", "Deception", "FirstAid", "History",
        "Insight", "Intimidation", "Investigation", "Knowledge",
        "Nature", "Perception", "Performance", "Religion",
        "Ride", "Stealth", "Survival", "Thievery",
    ],
    "Life Skills": [
        "Alchemy", "ArmorSmithing", "Blacksmithing", "Carpentry",
        "Cooking", "Enchanting", "Fishing", "Leatherworking",
        "Logging", "Mining", "Stonework", "Weaponsmithing",
    ],
}

# Flat list of every skill name, in canonical PascalCase.
ALL_SKILLS = [
    skill
    for category_skills in SKILL_CATEGORIES.values()
    for skill in category_skills
]

# Case-insensitive lookup: "archery" -> "Archery"
_CANONICAL_LOOKUP = {name.lower(): name for name in ALL_SKILLS}

# Reverse lookup: skill name -> category
_SKILL_TO_CATEGORY = {
    skill: category
    for category, skills in SKILL_CATEGORIES.items()
    for skill in skills
}


def canonical_skill_name(name):
    """
    Resolve a skill name to its canonical PascalCase form, case-insensitive.
    Returns None if the skill doesn't exist.
    """
    if not name:
        return None
    return _CANONICAL_LOOKUP.get(name.lower())


def is_valid_skill(name):
    return canonical_skill_name(name) is not None


def get_skill_category(name):
    """Return the category name a skill belongs to, or None."""
    canonical = canonical_skill_name(name)
    if canonical is None:
        return None
    return _SKILL_TO_CATEGORY.get(canonical)


def default_skills_dict():
    """Return a fresh {skill_name: 0} dict covering every known skill."""
    return {skill: 0 for skill in ALL_SKILLS}
