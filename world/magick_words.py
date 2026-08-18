"""
Magick Words

Flat registry of Magick words characters can discover, study, and
learn - the vocabulary spells are eventually built from (see
MagickDesignDocument.md). Mirrors the shape of world/races.py /
world/perks.py: plain data + small accessor functions, not a
database model.

Each entry:
    word            displayed Magick word (e.g. "Ignash")
    pronunciation   phonetic guide (e.g. "ig-NASH")
    meaning         player-readable meaning (e.g. "Fire")
    skill           associated Magick skill - one of
                    world.skills.SKILL_CATEGORIES["Magick Skills"]
    min_skill       minimum rank in that skill required to even
                    understand the word exists (see CmdStudy in
                    commands/command.py - below this, studying an
                    object bearing the word only tells the character
                    they sense Magick they don't yet understand)
    complexity      how complex the word is. Doubles as the learning
                    roll's required successes for now (see CmdStudy)
                    and will later feed spell complexity/mana cost
                    once spell construction exists - design doc is
                    explicit that these numbers are examples to be
                    balanced later, not final values
    description     lore text

This is intentionally a small starter set (the design doc's own
IGNASH example, plus the three other words its "known_magick_words"
example lists - VAEL, KORUM, AETH), not the full game vocabulary.
Populating this out is its own follow-up task; the learning pipeline
(CmdStudy, Character.known_magick_words) only needs the shape below
to work, and new words can be added here without touching any of
that code.
"""

from world.skills import canonical_skill_name

MAGICK_WORDS = {
    "IGNASH": {
        "word": "Ignash",
        "pronunciation": "ig-NASH",
        "meaning": "Fire",
        "skill": "Evocation",
        "min_skill": 2,
        "complexity": 1,
        "description": (
            "One of the oldest Evocation words still spoken. Scorch "
            "marks near old battle-sites are sometimes shaped like "
            "its glyph."
        ),
    },
    "VAEL": {
        "word": "Vael",
        "pronunciation": "vay-EL",
        "meaning": "Shield",
        "skill": "Abjuration",
        "min_skill": 1,
        "complexity": 1,
        "description": (
            "A ward-word, often the first thing an Abjuration student "
            "is taught - it appears carved above doorways in old "
            "watch-towers."
        ),
    },
    "KORUM": {
        "word": "Korum",
        "pronunciation": "KOR-um",
        "meaning": "Life",
        "skill": "Necromancy",
        "min_skill": 1,
        "complexity": 1,
        "description": (
            "Despite Necromancy's grim reputation, Korum is one of "
            "its gentlest words - it speaks to what persists in a "
            "body, not what leaves it."
        ),
    },
    "AETH": {
        "word": "Aeth",
        "pronunciation": "AYTH",
        "meaning": "Magic (itself)",
        "skill": "Arcana",
        "min_skill": 1,
        "complexity": 1,
        "description": (
            "The word for Magick itself, in Magick's own tongue. "
            "Every Arcana student learns it first, and most agree "
            "it's also the hardest to ever fully understand."
        ),
    },
}

# Case-insensitive lookup: "ignash" -> "IGNASH"
_CANONICAL_LOOKUP = {word_id.lower(): word_id for word_id in MAGICK_WORDS}

# Preserves declaration order for anything that wants a stable listing.
ALL_MAGICK_WORDS = list(MAGICK_WORDS.keys())


def canonical_word_id(word_id):
    """
    Resolve a word id (or its displayed word) to its canonical
    uppercase id, case-insensitive. Returns None if unrecognized.
    """
    if not word_id:
        return None
    return _CANONICAL_LOOKUP.get(word_id.strip().lower())


def is_valid_word(word_id):
    return canonical_word_id(word_id) is not None


def get_word_data(word_id):
    """Return the full data dict for a word id, or None if unrecognized."""
    canonical = canonical_word_id(word_id)
    if canonical is None:
        return None
    return MAGICK_WORDS[canonical]


def words_for_skill(skill_name):
    """All word ids associated with a given Magick skill."""
    canonical_skill = canonical_skill_name(skill_name)
    if canonical_skill is None:
        return []
    return [
        word_id for word_id, data in MAGICK_WORDS.items()
        if data["skill"] == canonical_skill
    ]
