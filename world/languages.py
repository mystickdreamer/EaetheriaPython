"""
Languages

world/races.py already defines which languages each race starts
knowing (every RACES[...]["languages"] list) - this module doesn't
duplicate that data, it derives a flat registry from it (ALL_LANGUAGES,
canonical_language_name()) for anywhere that needs to validate or list
every language that exists in the game, so there's no second list that
could drift out of sync with world/races.py.

It also owns the deterministic word-garbling used to render speech for
listeners who don't know the language being spoken - see CmdSay/
CmdSpeak in commands/command.py.
"""

import random
import re
import zlib

from world.races import RACES

# Every language mentioned in any race's starting language list,
# deduplicated and sorted.
ALL_LANGUAGES = sorted({
    language
    for race_data in RACES.values()
    for language in race_data.get("languages", [])
})

_CANONICAL_LOOKUP = {name.lower(): name for name in ALL_LANGUAGES}


def canonical_language_name(name):
    """Case-insensitive lookup: 'elvish' -> 'Elvish'. None if unrecognized."""
    if not name:
        return None
    return _CANONICAL_LOOKUP.get(name.strip().lower())


# ==========================================================================
# Garbling
# ==========================================================================
#
# Deterministic per (language, word): the same word always garbles to
# the same nonsense in a given language, both within one session and
# across server restarts. Seeded with zlib.crc32, NOT Python's built-in
# hash() - str hashing is randomized per-process by default (security
# feature, PYTHONHASHSEED), which would make the same word garble
# differently every reload and defeat the point. A listener who hears
# a language often enough can start recognizing repeated words by
# their garbled shape even without understanding them - same texture
# as classic Diku/Rom language garbling. Different languages garble
# the same word differently, since the language name is part of the
# seed.
#
# Garbled words are built from a fixed syllable pool rather than
# random letters, so garbled speech reads as "some other language"
# instead of keyboard mash.

_GARBLE_SYLLABLES = (
    "ka", "zu", "mir", "esh", "vor", "tha", "lom", "qui", "dra", "sel",
    "nok", "fyr", "wex", "orn", "sai", "thu", "gral", "iss", "unn", "eth",
)

_WORD_RE = re.compile(r"[A-Za-z]+")


def _garble_word(word, language_name):
    seed = zlib.crc32(f"{language_name.lower()}::{word.lower()}".encode("utf-8"))
    rng = random.Random(seed)

    target_len = max(2, len(word))
    syllable_count = max(1, round(target_len / 3))
    garbled = "".join(rng.choice(_GARBLE_SYLLABLES) for _ in range(syllable_count))
    garbled = garbled[:target_len]

    if word.isupper():
        return garbled.upper()
    if word[0].isupper():
        return garbled.capitalize()
    return garbled


def garble_text(text, language_name):
    """
    Return `text` with every alphabetic word deterministically garbled
    for a listener who doesn't know `language_name`. Non-letter
    characters (spaces, punctuation, numbers) pass through unchanged,
    so sentence shape/punctuation stays recognizable even though the
    words don't.
    """
    if not text:
        return text
    return _WORD_RE.sub(lambda m: _garble_word(m.group(0), language_name), text)
