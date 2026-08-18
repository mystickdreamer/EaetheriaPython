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

    # ------------------------------------------------------------------
    # ARCANA
    # Fundamental Magick concepts
    # ------------------------------------------------------------------

    "AETH": {
        "word": "Aeth",
        "pronunciation": "AYTH",
        "meaning": "Magick",
        "skill": "Arcana",
        "category": "concept",
        "min_skill": 1,
        "complexity": 1,
        "description": "The fundamental word for Magick itself and the force that binds all workings together.",
    },

    "SAEL": {
        "word": "Sael",
        "pronunciation": "SAYL",
        "meaning": "Knowledge",
        "skill": "Arcana",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "The concept of knowledge, understanding, and things that are known.",
    },

    "VAEN": {
        "word": "Vaen",
        "pronunciation": "VAYN",
        "meaning": "Sense",
        "skill": "Arcana",
        "category": "effect",
        "min_skill": 2,
        "complexity": 1,
        "description": "The act of perceiving through magical senses rather than ordinary sight or hearing.",
    },

    "ORYN": {
        "word": "Oryn",
        "pronunciation": "OR-in",
        "meaning": "Truth",
        "skill": "Arcana",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "The fundamental nature of what is true and what is real.",
    },

    "THAEL": {
        "word": "Thael",
        "pronunciation": "THAYL",
        "meaning": "Pattern",
        "skill": "Arcana",
        "category": "concept",
        "min_skill": 4,
        "complexity": 2,
        "description": "The underlying pattern that gives magical workings their structure.",
    },

    "ERYN": {
        "word": "Eryn",
        "pronunciation": "AIR-in",
        "meaning": "Power",
        "skill": "Arcana",
        "category": "concept",
        "min_skill": 5,
        "complexity": 3,
        "description": "Raw magical power and the force required to impose a will upon reality.",
    },

    # ------------------------------------------------------------------
    # EVOCATION
    # Energy and elemental forces
    # ------------------------------------------------------------------

    "IGNASH": {
        "word": "Ignash",
        "pronunciation": "ig-NASH",
        "meaning": "Fire",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "The primal concept of flame, heat, and consuming fire.",
    },

    "VEYR": {
        "word": "Veyr",
        "pronunciation": "VAIR",
        "meaning": "Air",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "The element of air, wind, breath, and movement through the atmosphere.",
    },

    "DORAN": {
        "word": "Doran",
        "pronunciation": "DOH-ran",
        "meaning": "Earth",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "The fundamental substance of earth, soil, and stone.",
    },

    "THALOS": {
        "word": "Thalos",
        "pronunciation": "THAY-los",
        "meaning": "Water",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "The element of water, liquid flow, and the currents of nature.",
    },

    "KAEL": {
        "word": "Kael",
        "pronunciation": "KAYL",
        "meaning": "Lightning",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "Electrical force, lightning, and the violent discharge of energy.",
    },

    "RUUN": {
        "word": "Ruun",
        "pronunciation": "ROON",
        "meaning": "Cold",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "The absence of heat and the supernatural imposition of freezing cold.",
    },

    "SAHR": {
        "word": "Sahr",
        "pronunciation": "SAHR",
        "meaning": "Heat",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "Pure thermal energy independent of flame.",
    },

    "VARESH": {
        "word": "Varesh",
        "pronunciation": "VAIR-esh",
        "meaning": "Force",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 4,
        "complexity": 2,
        "description": "Pure magical force capable of striking, pushing, crushing, or restraining.",
    },

    "ZORATH": {
        "word": "Zorath",
        "pronunciation": "ZOR-ath",
        "meaning": "Storm",
        "skill": "Evocation",
        "category": "concept",
        "min_skill": 5,
        "complexity": 3,
        "description": "The combined violence of wind, rain, lightning, and atmospheric power.",
    },

    # ------------------------------------------------------------------
    # ABJURATION
    # Protection, wards, binding, and negation
    # ------------------------------------------------------------------

    "VAEL": {
        "word": "Vael",
        "pronunciation": "VAYL",
        "meaning": "Shield",
        "skill": "Abjuration",
        "category": "concept",
        "min_skill": 1,
        "complexity": 1,
        "description": "The fundamental concept of magical protection and shielding.",
    },

    "WYR": {
        "word": "Wyr",
        "pronunciation": "WEER",
        "meaning": "Ward",
        "skill": "Abjuration",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "A magical boundary established to protect an area, person, or object.",
    },

    "SAETH": {
        "word": "Saeth",
        "pronunciation": "SAYTH",
        "meaning": "Barrier",
        "skill": "Abjuration",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "A magical barrier that prevents passage or interference.",
    },

    "ORVAK": {
        "word": "Orvak",
        "pronunciation": "OR-vak",
        "meaning": "Protect",
        "skill": "Abjuration",
        "category": "effect",
        "min_skill": 2,
        "complexity": 1,
        "description": "The act of protecting something from harm or magical influence.",
    },

    "NETH": {
        "word": "Neth",
        "pronunciation": "NETH",
        "meaning": "Bind",
        "skill": "Abjuration",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical act of restricting movement or holding something in place.",
    },

    "KARESH": {
        "word": "Karesh",
        "pronunciation": "KAH-resh",
        "meaning": "Negate",
        "skill": "Abjuration",
        "category": "effect",
        "min_skill": 4,
        "complexity": 2,
        "description": "The act of suppressing or canceling an existing magical effect.",
    },

    "VORA": {
        "word": "Vora",
        "pronunciation": "VOH-rah",
        "meaning": "Silence",
        "skill": "Abjuration",
        "category": "effect",
        "min_skill": 4,
        "complexity": 2,
        "description": "The magical suppression of sound and spoken words.",
    },

    "THAUM": {
        "word": "Thaum",
        "pronunciation": "THAWM",
        "meaning": "Dispel",
        "skill": "Abjuration",
        "category": "effect",
        "min_skill": 5,
        "complexity": 3,
        "description": "The deliberate unraveling and removal of magical workings.",
    },

    "AVAR": {
        "word": "Avar",
        "pronunciation": "AH-var",
        "meaning": "Seal",
        "skill": "Abjuration",
        "category": "effect",
        "min_skill": 6,
        "complexity": 3,
        "description": "The act of permanently or temporarily sealing magic, objects, or passages.",
    },

    # ------------------------------------------------------------------
    # NECROMANCY
    # Life, death, flesh, and spirit
    # ------------------------------------------------------------------

    "KORUM": {
        "word": "Korum",
        "pronunciation": "KOR-um",
        "meaning": "Life",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 1,
        "complexity": 1,
        "description": "The animating force of living things.",
    },

    "VETH": {
        "word": "Veth",
        "pronunciation": "VETH",
        "meaning": "Death",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "The ending of life and the transition from living to dead.",
    },

    "SURA": {
        "word": "Sura",
        "pronunciation": "SOO-rah",
        "meaning": "Flesh",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "Living tissue, muscle, and the physical substance of the body.",
    },

    "NURA": {
        "word": "Nura",
        "pronunciation": "NOO-rah",
        "meaning": "Bone",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "The hard structure underlying the living body.",
    },

    "KARETH": {
        "word": "Kareth",
        "pronunciation": "KAH-reth",
        "meaning": "Blood",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "The vital fluid that carries life through the body.",
    },

    "OTHAR": {
        "word": "Othar",
        "pronunciation": "OH-thar",
        "meaning": "Spirit",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "The animating spiritual essence that exists beyond the physical body.",
    },

    "VELUM": {
        "word": "Velum",
        "pronunciation": "VEL-um",
        "meaning": "Soul",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 4,
        "complexity": 3,
        "description": "The deepest spiritual essence of a living being.",
    },

    "DRAVEN": {
        "word": "Draven",
        "pronunciation": "DRAY-ven",
        "meaning": "Decay",
        "skill": "Necromancy",
        "category": "effect",
        "min_skill": 4,
        "complexity": 2,
        "description": "The breakdown of living or once-living matter.",
    },

    "KORASH": {
        "word": "Korash",
        "pronunciation": "KOR-ash",
        "meaning": "Undeath",
        "skill": "Necromancy",
        "category": "concept",
        "min_skill": 5,
        "complexity": 3,
        "description": "The unnatural state between life and death.",
    },

    # ------------------------------------------------------------------
    # TRANSMUTATION
    # Matter, form, and physical change
    # ------------------------------------------------------------------

    "TAREN": {
        "word": "Taren",
        "pronunciation": "TAIR-en",
        "meaning": "Stone",
        "skill": "Transmutation",
        "category": "concept",
        "min_skill": 1,
        "complexity": 1,
        "description": "Stone, rock, and the solid mineral substance of the earth.",
    },

    "MERAK": {
        "word": "Merak",
        "pronunciation": "MEH-rak",
        "meaning": "Metal",
        "skill": "Transmutation",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "Metal and the properties of forged or naturally occurring metallic substances.",
    },

    "VESH": {
        "word": "Vesh",
        "pronunciation": "VESH",
        "meaning": "Wood",
        "skill": "Transmutation",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "Wood, timber, and the fibrous substance of plants.",
    },

    "OREN": {
        "word": "Oren",
        "pronunciation": "OR-en",
        "meaning": "Form",
        "skill": "Transmutation",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "The physical shape and arrangement of matter.",
    },

    "RAVA": {
        "word": "Rava",
        "pronunciation": "RAH-vah",
        "meaning": "Strengthen",
        "skill": "Transmutation",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical strengthening or reinforcement of physical matter.",
    },

    "NAREK": {
        "word": "Narek",
        "pronunciation": "NAIR-ek",
        "meaning": "Weaken",
        "skill": "Transmutation",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical weakening or degradation of physical matter.",
    },

    "VEYRA": {
        "word": "Veyra",
        "pronunciation": "VAIR-ah",
        "meaning": "Grow",
        "skill": "Transmutation",
        "category": "effect",
        "min_skill": 4,
        "complexity": 2,
        "description": "The magical acceleration or enlargement of physical growth.",
    },

    "ZETH": {
        "word": "Zeth",
        "pronunciation": "ZETH",
        "meaning": "Transform",
        "skill": "Transmutation",
        "category": "effect",
        "min_skill": 5,
        "complexity": 3,
        "description": "The fundamental transformation of one form of matter into another.",
    },

    # ------------------------------------------------------------------
    # CONJURATION
    # Calling, creating, moving, and binding
    # ------------------------------------------------------------------

    "ARAN": {
        "word": "Aran",
        "pronunciation": "AH-ran",
        "meaning": "Summon",
        "skill": "Conjuration",
        "category": "effect",
        "min_skill": 2,
        "complexity": 1,
        "description": "The magical act of calling a creature, object, or force into one's presence.",
    },

    "VAAL": {
        "word": "Vaal",
        "pronunciation": "VAHL",
        "meaning": "Call",
        "skill": "Conjuration",
        "category": "effect",
        "min_skill": 2,
        "complexity": 1,
        "description": "The act of calling something toward the caster.",
    },

    "SERIN": {
        "word": "Serin",
        "pronunciation": "SEH-rin",
        "meaning": "Create",
        "skill": "Conjuration",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical creation of a temporary object or substance.",
    },

    "OVAR": {
        "word": "Ovar",
        "pronunciation": "OH-var",
        "meaning": "Space",
        "skill": "Conjuration",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "The empty distance between places and the magical structure of space itself.",
    },

    "TARETH": {
        "word": "Tareth",
        "pronunciation": "TAIR-eth",
        "meaning": "Anchor",
        "skill": "Conjuration",
        "category": "concept",
        "min_skill": 4,
        "complexity": 3,
        "description": "A fixed magical point that establishes a connection to a place or object.",
    },

    "VARESH": {
        "word": "Varesh",
        "pronunciation": "VAIR-esh",
        "meaning": "Portal",
        "skill": "Conjuration",
        "category": "concept",
        "min_skill": 5,
        "complexity": 3,
        "description": "A magical opening connecting two otherwise separate locations.",
    },

    "ORIN": {
        "word": "Orin",
        "pronunciation": "OR-in",
        "meaning": "Banish",
        "skill": "Conjuration",
        "category": "effect",
        "min_skill": 5,
        "complexity": 3,
        "description": "The magical act of forcing a creature, object, or summoned entity away.",
    },

    "KETH": {
        "word": "Keth",
        "pronunciation": "KETH",
        "meaning": "Return",
        "skill": "Conjuration",
        "category": "effect",
        "min_skill": 5,
        "complexity": 3,
        "description": "The act of returning something to a previous or established location.",
    },

    "ZAAR": {
        "word": "Zaar",
        "pronunciation": "ZAHR",
        "meaning": "Teleport",
        "skill": "Conjuration",
        "category": "effect",
        "min_skill": 7,
        "complexity": 5,
        "description": "The instantaneous movement of a creature or object from one location to another.",
    },

    # ------------------------------------------------------------------
    # DIVINATION
    # Perception, discovery, and hidden knowledge
    # ------------------------------------------------------------------

    "RETH": {
        "word": "Reth",
        "pronunciation": "RETH",
        "meaning": "Reveal",
        "skill": "Divination",
        "category": "effect",
        "min_skill": 2,
        "complexity": 1,
        "description": "The act of bringing something hidden or obscured into magical perception.",
    },

    "OTH": {
        "word": "Oth",
        "pronunciation": "OTH",
        "meaning": "Detect",
        "skill": "Divination",
        "category": "effect",
        "min_skill": 2,
        "complexity": 1,
        "description": "The magical detection of a particular presence, substance, or condition.",
    },

    "VARYN": {
        "word": "Varyn",
        "pronunciation": "VAIR-in",
        "meaning": "Seek",
        "skill": "Divination",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The act of magically searching for something known or suspected to exist.",
    },

    "ESHAR": {
        "word": "Eshar",
        "pronunciation": "ESH-ar",
        "meaning": "Locate",
        "skill": "Divination",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical determination of the location of a person, object, or place.",
    },

    "THAEN": {
        "word": "Thaen",
        "pronunciation": "THAY-en",
        "meaning": "Scry",
        "skill": "Divination",
        "category": "effect",
        "min_skill": 4,
        "complexity": 3,
        "description": "The act of magically perceiving a distant location or subject.",
    },

    "ORATH": {
        "word": "Orath",
        "pronunciation": "OR-ath",
        "meaning": "Foresee",
        "skill": "Divination",
        "category": "effect",
        "min_skill": 5,
        "complexity": 3,
        "description": "The difficult art of perceiving possible future events.",
    },

    "NETHAR": {
        "word": "Nethar",
        "pronunciation": "NETH-ar",
        "meaning": "Foresight",
        "skill": "Divination",
        "category": "concept",
        "min_skill": 6,
        "complexity": 4,
        "description": "A deeper understanding of possible futures and the paths leading toward them.",
    },

    # ------------------------------------------------------------------
    # ILLUSION
    # Appearance, perception, light, shadow, and deception
    # ------------------------------------------------------------------

    "SHAEL": {
        "word": "Shael",
        "pronunciation": "SHAYL",
        "meaning": "Appearance",
        "skill": "Illusion",
        "category": "concept",
        "min_skill": 1,
        "complexity": 1,
        "description": "The visible or perceivable appearance of a thing.",
    },

    "VEY": {
        "word": "Vey",
        "pronunciation": "VAY",
        "meaning": "Image",
        "skill": "Illusion",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "A magically created visual representation.",
    },

    "NIRA": {
        "word": "Nira",
        "pronunciation": "NEER-ah",
        "meaning": "Sound",
        "skill": "Illusion",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "Sound and the perception of sound.",
    },

    "OSHA": {
        "word": "Osha",
        "pronunciation": "OH-shah",
        "meaning": "Light",
        "skill": "Illusion",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "Light as perceived by the senses rather than as physical energy.",
    },

    "DRAEL": {
        "word": "Drael",
        "pronunciation": "DRAYL",
        "meaning": "Shadow",
        "skill": "Illusion",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "Darkness, obscurity, and the manipulation of visual perception.",
    },

    "VAESH": {
        "word": "Vaesh",
        "pronunciation": "VAYSH",
        "meaning": "Disguise",
        "skill": "Illusion",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical alteration of perceived appearance.",
    },

    "RYN": {
        "word": "Ryn",
        "pronunciation": "RIN",
        "meaning": "Hide",
        "skill": "Illusion",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical concealment of something from perception.",
    },

    "SARETH": {
        "word": "Sareth",
        "pronunciation": "SAIR-eth",
        "meaning": "Deceive",
        "skill": "Illusion",
        "category": "effect",
        "min_skill": 4,
        "complexity": 2,
        "description": "The deliberate creation of a false perception.",
    },

    "ZHAEL": {
        "word": "Zhael",
        "pronunciation": "ZHAYL",
        "meaning": "Phantasm",
        "skill": "Illusion",
        "category": "concept",
        "min_skill": 5,
        "complexity": 3,
        "description": "A complex magical illusion capable of presenting an apparently independent presence.",
    },

    # ------------------------------------------------------------------
    # CHARM
    # Emotion, influence, and control
    # ------------------------------------------------------------------

    "SELA": {
        "word": "Sela",
        "pronunciation": "SAY-lah",
        "meaning": "Emotion",
        "skill": "Charm",
        "category": "concept",
        "min_skill": 1,
        "complexity": 1,
        "description": "The magical concept of emotion and feeling.",
    },

    "RALA": {
        "word": "Rala",
        "pronunciation": "RAH-lah",
        "meaning": "Fear",
        "skill": "Charm",
        "category": "concept",
        "min_skill": 2,
        "complexity": 1,
        "description": "Fear, dread, and the instinctive response to perceived danger.",
    },

    "VAEN_CALM": {
        "word": "Vaen",
        "pronunciation": "VAYN",
        "meaning": "Calm",
        "skill": "Charm",
        "category": "effect",
        "min_skill": 2,
        "complexity": 1,
        "description": "The magical suppression of agitation, fear, and hostility.",
    },

    "OREN_TRUST": {
        "word": "Oren",
        "pronunciation": "OR-en",
        "meaning": "Trust",
        "skill": "Charm",
        "category": "concept",
        "min_skill": 3,
        "complexity": 2,
        "description": "The feeling of confidence and trust toward another being.",
    },

    "SHAAR": {
        "word": "Shaar",
        "pronunciation": "SHAHR",
        "meaning": "Compel",
        "skill": "Charm",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical imposition of a suggestion or desired action.",
    },

    "VETHAR": {
        "word": "Vethar",
        "pronunciation": "VETH-ar",
        "meaning": "Persuade",
        "skill": "Charm",
        "category": "effect",
        "min_skill": 3,
        "complexity": 2,
        "description": "The magical strengthening of an argument, suggestion, or desired belief.",
    },

    "NALA": {
        "word": "Nala",
        "pronunciation": "NAH-lah",
        "meaning": "Enrage",
        "skill": "Charm",
        "category": "effect",
        "min_skill": 4,
        "complexity": 2,
        "description": "The magical intensification of anger and hostility.",
    },

    "SAEVA": {
        "word": "Saeva",
        "pronunciation": "SAY-vah",
        "meaning": "Confuse",
        "skill": "Charm",
        "category": "effect",
        "min_skill": 4,
        "complexity": 2,
        "description": "The disruption of thought, judgment, and coherent decision-making.",
    },

    "ORASH": {
        "word": "Orash",
        "pronunciation": "OR-ash",
        "meaning": "Command",
        "skill": "Charm",
        "category": "effect",
        "min_skill": 5,
        "complexity": 3,
        "description": "A powerful magical command imposed upon another mind.",
    },

    "ZARETH": {
        "word": "Zareth",
        "pronunciation": "ZAIR-eth",
        "meaning": "Dominate",
        "skill": "Charm",
        "category": "effect",
        "min_skill": 7,
        "complexity": 5,
        "description": "The extreme magical domination of another will.",
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
