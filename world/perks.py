"""
Perks

Python-side parallel to the Godot `Perk` resource, sized to match what
EntityStats.apply_perk()/remove_perk() actually read: bonuses (stat ->
flat value, applied as a modifier), stackable, and max_rank.

Placeholders below — replace with your real perk data. Referenced by
race innate_perks (see world/races.py) and can also be granted directly
via Character.grant_perk().
"""

PERKS = {
    "keen_senses": {
        "display_name": "Keen Senses",
        "bonuses": {"Perception": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "iron_stomach": {
        "display_name": "Iron Stomach",
        "bonuses": {"endurance": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "quick_hands": {
        "display_name": "Quick Hands",
        "bonuses": {"Thievery": 1, "DualWield": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "toughened": {
        "display_name": "Toughened",
        "bonuses": {"max_hp": 5},
        "stackable": True,
        "max_rank": 3,
    },

    # ==================================================================
    # Racial innate perks (world/races.py). The Perk .tres resources
    # these are ported from weren't part of the upload, so the
    # bonuses/descriptions below are best-guess placeholders based on
    # the perk name and race flavor - replace with your real values.
    # ==================================================================
    "stone_cunning": {
        "display_name": "Stone Cunning",
        "description": "Dwarven instinct for stonework and buried passages.",
        "bonuses": {"Stonework": 1, "Knowledge": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "speak_with_animals": {
        "display_name": "Speak with Animals",
        "description": "Goblins can communicate simple ideas with animals.",
        "bonuses": {"Nature": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "relentless_endurance": {
        "display_name": "Relentless Endurance",
        "description": "Half-Orc grit - once per rest, shrug off what should have dropped you.",
        "bonuses": {"endurance": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "savage_attacks": {
        "display_name": "Savage Attacks",
        "description": "Half-Orc fury adds extra weight to a solid hit.",
        "bonuses": {"might": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "lucky": {
        "display_name": "Lucky",
        "description": "Lightfeet knack for narrowly avoiding disaster.",
        "bonuses": {"Evasion": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "lightfoot_nimbleness": {
        "display_name": "Lightfoot Nimbleness",
        "description": "Lightfeet can slip through the space of larger creatures.",
        "bonuses": {"Stealth": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "cats_claws": {
        "display_name": "Cat's Claws",
        "description": "Mirari natural claws, always at hand.",
        "bonuses": {"MartialArts": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "feline_agility": {
        "display_name": "Feline Agility",
        "description": "A Mirari burst of speed after holding still.",
        "bonuses": {"agility": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "hold_breath": {
        "display_name": "Hold Breath",
        "description": "Thalorim can hold their breath far longer than most.",
        "bonuses": {"endurance": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "natural_armor": {
        "display_name": "Natural Armor",
        "description": "Thalorim hide provides a baseline of protection.",
        "bonuses": {"LightArmor": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "shell_defense": {
        "display_name": "Shell Defense",
        "description": "A Thalorim can withdraw into their shell for extra defense.",
        "bonuses": {"HeavyArmor": 1},
        "stackable": False,
        "max_rank": 1,
    },
    "shrink": {
        "display_name": "Shrink",
        "description": "The Lost can resize gear and their own frame to fit tight spaces.",
        "bonuses": {},
        "stackable": False,
        "max_rank": 1,
    },
}


def get_perk_data(perk_id):
    return PERKS.get(perk_id)


def is_valid_perk(perk_id):
    return perk_id in PERKS
