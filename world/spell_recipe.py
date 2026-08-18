"""
Spell Recipe

Represents a spell being constructed from learned Magick words.

A SpellRecipe is not necessarily a completed spell. It is the
structured representation of the components selected during spell
creation.
"""

from dataclasses import dataclass, field
from typing import List, Optional

from world.magick_words import (
    canonical_word_id,
    get_word_data,
)
from world.skills import canonical_skill_name


DELIVERY_TYPES = (
    "Self",
    "Touch",
    "Projectile",
    "Object",
    "Room",
)


@dataclass
class SpellRecipe:
    """
    A spell under construction.

    primary_skill:
        The primary Magick skill used by the spell.

    delivery:
        How the spell reaches its target.

    components:
        Ordered list of Magick word IDs.

    modifiers:
        Optional Magick word IDs that modify the spell.

    ritual:
        Whether the spell is intended for ritual casting.
    """

    primary_skill: Optional[str] = None
    delivery: Optional[str] = None
    components: List[str] = field(default_factory=list)
    modifiers: List[str] = field(default_factory=list)
    ritual: bool = False

    def __post_init__(self):
        if self.primary_skill:
            self.primary_skill = canonical_skill_name(
                self.primary_skill
            )

        if self.delivery:
            self.delivery = self._canonical_delivery(
                self.delivery
            )

        self.components = [
            canonical_word_id(word_id)
            for word_id in self.components
        ]

        self.components = [
            word_id
            for word_id in self.components
            if word_id is not None
        ]

        self.modifiers = [
            canonical_word_id(word_id)
            for word_id in self.modifiers
        ]

        self.modifiers = [
            word_id
            for word_id in self.modifiers
            if word_id is not None
        ]

    # ==============================================================
    # DELIVERY
    # ==============================================================

    @staticmethod
    def _canonical_delivery(delivery):
        """
        Convert a delivery name to its canonical form.
        """

        if not delivery:
            return None

        for delivery_type in DELIVERY_TYPES:
            if delivery_type.lower() == delivery.strip().lower():
                return delivery_type

        return None

    def set_delivery(self, delivery):
        """
        Set the delivery type using a case-insensitive lookup.
        """

        canonical = self._canonical_delivery(delivery)

        if canonical is None:
            raise ValueError(
                f"Unknown spell delivery/target: {delivery}"
            )

        self.delivery = canonical

    # ==============================================================
    # COMPONENTS
    # ==============================================================

    def add_component(self, word_id):
        """
        Add a Magick word to the spell.
        """

        canonical = canonical_word_id(word_id)

        if canonical is None:
            raise ValueError(
                f"Unknown Magick word: {word_id}"
            )

        self.components.append(canonical)

    def remove_component(self, word_id):
        """
        Remove the first occurrence of a component.
        """

        canonical = canonical_word_id(word_id)

        if canonical is None:
            return False

        if canonical not in self.components:
            return False

        self.components.remove(canonical)
        return True

    # ==============================================================
    # MODIFIERS
    # ==============================================================

    def add_modifier(self, word_id):
        """
        Add a Magick word as an optional modifier.
        """

        canonical = canonical_word_id(word_id)

        if canonical is None:
            raise ValueError(
                f"Unknown Magick word: {word_id}"
            )

        self.modifiers.append(canonical)

    def remove_modifier(self, word_id):
        """
        Remove the first occurrence of a modifier.
        """

        canonical = canonical_word_id(word_id)

        if canonical is None:
            return False

        if canonical not in self.modifiers:
            return False

        self.modifiers.remove(canonical)
        return True

    # ==============================================================
    # WORD DATA
    # ==============================================================

    def all_word_ids(self):
        """
        Return all word IDs used by the recipe.
        """

        return self.components + self.modifiers

    def get_word_data(self):
        """
        Return the registry data for every word used by the recipe.
        """

        return [
            get_word_data(word_id)
            for word_id in self.all_word_ids()
        ]

    def words_by_category(self, category):
        """
        Return the word IDs in this recipe belonging to a category.

        Category matching is case-insensitive.
        """

        if not category:
            return []

        category = category.strip().lower()

        result = []

        for word_id in self.all_word_ids():
            data = get_word_data(word_id)

            if not data:
                continue

            if data.get("category", "").lower() == category:
                result.append(word_id)

        return result

    # ==============================================================
    # SECONDARY MAGICK SKILLS
    # ==============================================================

    def secondary_skills(self):
        """
        Determine the Magick skills represented by the recipe's words.

        The primary skill is excluded.

        Secondary skills increase spell complexity but do not add
        their skill rating to the casting pool.
        """

        skills = []

        for word_id in self.all_word_ids():
            data = get_word_data(word_id)

            if not data:
                continue

            skill = data["skill"]

            if skill == self.primary_skill:
                continue

            if skill not in skills:
                skills.append(skill)

        return skills

    # ==============================================================
    # COMPLEXITY
    # ==============================================================

    def word_complexity(self):
        """
        Return the total complexity contributed by the Magick words.
        """

        total = 0

        for word_id in self.all_word_ids():
            data = get_word_data(word_id)

            if data:
                total += data.get("complexity", 0)

        return total

    # ==============================================================
    # SERIALIZATION
    # ==============================================================

    def to_dict(self):
        """
        Convert the recipe into persistent character data.
        """

        return {
            "primary_skill": self.primary_skill,
            "delivery": self.delivery,
            "components": list(self.components),
            "modifiers": list(self.modifiers),
            "ritual": self.ritual,
        }

    @classmethod
    def from_dict(cls, data):
        """
        Reconstruct a SpellRecipe from persistent data.
        """

        if not isinstance(data, dict):
            raise ValueError(
                "Spell recipe data must be a dictionary."
            )

        return cls(
            primary_skill=data.get("primary_skill"),
            delivery=data.get("delivery"),
            components=data.get("components", []),
            modifiers=data.get("modifiers", []),
            ritual=bool(data.get("ritual", False)),
        )