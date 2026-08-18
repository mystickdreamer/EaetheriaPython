"""
Spell Rules

Validation and calculation rules for the Eaetheria Magick system.

This module does not perform casting or spell creation rolls yet.

Its purpose is to answer questions such as:

    - Is this recipe structurally valid?
    - Does the character know every word?
    - Does the character possess the required primary skill?
    - What secondary Magick skills does the spell contain?
    - What is the spell's current complexity?

The actual creation and casting rolls will be added later.
"""

from dataclasses import dataclass, field

from world.magick_words import (
    canonical_word_id,
    get_word_data,
)
from world.skills import canonical_skill_name

from world.spell_recipe import (
    DELIVERY_TYPES,
    SpellRecipe,
)


@dataclass
class ValidationResult:
    """Result of validating a SpellRecipe."""

    valid: bool
    errors: list = field(default_factory=list)
    warnings: list = field(default_factory=list)

    def add_error(self, message):
        self.errors.append(message)
        self.valid = False

    def add_warning(self, message):
        self.warnings.append(message)


def _get_character_skill(character, skill_name):
    """
    Get a character's skill rating.

    Character skill storage is kept behind this helper so the spell
    system does not need to know the exact character implementation.

    Goes through Character.get_skill() (typeclasses/characters.py),
    which is the actual public accessor - characters do not expose a
    bare `.skills` dict attribute.
    """
    if character is None:
        return 0

    canonical = canonical_skill_name(skill_name)

    if canonical is None:
        return 0

    get_skill = getattr(character, "get_skill", None)

    if callable(get_skill):
        return get_skill(canonical)

    return 0


def _known_magick_words(character):
    """
    Return the character's known Magick word IDs as canonical IDs.
    """
    if character is None:
        return set()

    known = getattr(character, "known_magick_words", None)

    if not known:
        return set()

    result = set()

    for word_id in known:
        canonical = canonical_word_id(word_id)

        if canonical:
            result.add(canonical)

    return result

def known_words_by_category(character, category):
    """
    Return the character's known Magick words belonging to a category.

    The returned values are canonical Magick word IDs.
    """

    if not category:
        return []

    category = category.strip().lower()

    # Make sure character data has been initialized.
    if hasattr(character, "ensure_data_integrity"):
        character.ensure_data_integrity()

    known_words = _known_magick_words(character)

    result = []

    for word_id in known_words:
        data = get_word_data(word_id)

        if not data:
            continue

        if data.get("category", "").lower() == category:
            result.append(word_id)

    return result


def get_known_words_for_category(character, category):
    """
    Public API for the spell-crafting menu (and anything else outside
    this module).

    Callers should use this instead of reaching into
    known_magick_words / MAGICK_WORDS / category strings themselves -
    it's the one place that knows how "does this character know a
    word in this category" is actually answered. Currently a thin
    wrapper around known_words_by_category(), kept separate so the
    internal name/shape of that function can change without breaking
    callers like world/spell_menu.py.
    """
    return known_words_by_category(character, category)


def validate_recipe(recipe, character=None):
    """
    Validate a spell recipe.

    If a character is supplied, character-specific requirements such
    as known words and primary skill are checked.

    If no character is supplied, only structural validation occurs.
    """

    result = ValidationResult(valid=True)

    if not isinstance(recipe, SpellRecipe):
        result.add_error("Invalid spell recipe.")
        return result

    # --------------------------------------------------------------
    # PRIMARY SKILL
    # --------------------------------------------------------------

    if not recipe.primary_skill:
        result.add_error(
            "A primary Magick skill must be selected."
        )

    elif canonical_skill_name(recipe.primary_skill) is None:
        result.add_error(
            f"Unknown primary Magick skill: {recipe.primary_skill}"
        )

    # --------------------------------------------------------------
    # DELIVERY
    # --------------------------------------------------------------

    if not recipe.delivery:
        result.add_error(
            "A delivery/target type must be selected."
        )

    elif recipe.delivery not in DELIVERY_TYPES:
        result.add_error(
            f"Unknown delivery/target type: {recipe.delivery}"
        )

    # --------------------------------------------------------------
    # COMPONENTS
    # --------------------------------------------------------------

    if not recipe.components:
        result.add_error(
            "A spell must contain at least one Magick word."
        )

    # --------------------------------------------------------------
    # WORD VALIDATION
    # --------------------------------------------------------------

    known_words = _known_magick_words(character)

    for word_id in recipe.all_word_ids():

        data = get_word_data(word_id)

        if data is None:
            result.add_error(
                f"Unknown Magick word: {word_id}"
            )
            continue

        # If we are validating for a character, make sure the
        # character actually knows the word.
        if character is not None and word_id not in known_words:
            result.add_error(
                f"You do not know the Magick word "
                f"{data['word']}."
            )

    # --------------------------------------------------------------
    # PRIMARY SKILL REQUIREMENT
    # --------------------------------------------------------------

    if character is not None and recipe.primary_skill:
        skill_rating = _get_character_skill(
            character,
            recipe.primary_skill,
        )

        if skill_rating <= 0:
            result.add_error(
                f"You do not possess the Magick skill "
                f"{recipe.primary_skill}."
            )

    # --------------------------------------------------------------
    # WORD MINIMUM SKILLS
    # --------------------------------------------------------------

    if character is not None:

        checked_words = set()

        for word_id in recipe.all_word_ids():

            if word_id in checked_words:
                continue

            checked_words.add(word_id)

            data = get_word_data(word_id)

            if data is None:
                continue

            required = data.get("min_skill", 0)
            skill = data.get("skill")

            rating = _get_character_skill(
                character,
                skill,
            )

            if rating < required:
                result.add_error(
                    f"The Magick word {data['word']} requires "
                    f"{skill} {required}."
                )

    return result


def calculate_complexity(recipe):
    """
    Calculate the current spell complexity.

    Every Magick word/component contributes its own complexity.

    This follows the design document's rule that adding components
    increases the overall complexity of the spell.
    """
    if not isinstance(recipe, SpellRecipe):
        return 0

    return recipe.word_complexity()


def calculate_creation_difficulty(recipe):
    """
    Calculate the creation difficulty from spell complexity.

    The exact balancing formula is intentionally kept simple for now.

    The design document states that complexity determines creation
    difficulty but leaves the exact formula for balancing.
    """
    complexity = calculate_complexity(recipe)

    if complexity <= 0:
        return 0

    return complexity


def calculate_mana_cost(recipe):
    """
    Calculate the eventual mana cost.

    The design document explicitly leaves the exact formula open for
    balancing, so the initial implementation uses a simple linear
    relationship.
    """
    complexity = calculate_complexity(recipe)

    if complexity <= 0:
        return 0

    return complexity * 2