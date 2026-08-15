"""
Races

Python-side parallel to the Godot `Race` resource (.tres files), sized
to match every field EntityStats.gd actually reads off `player_race`:

- combat_speed_modifier      -> recalculate_combat_speed()
- starting_vision             -> apply_race_defaults()
- size_category               -> apply_race_defaults()
- languages                   -> apply_race_defaults() -> learn_language()
- flat_bonuses (stat -> int)  -> apply_race_defaults() -> add_modifier(..., "race_bonus", ...)
- innate_perks (list of perk ids) -> apply_race_defaults() -> apply_perk()
- can_fly / ignores_size_restrictions
- xp_multiplier_overrides (stat -> delta) -> get_xp_multiplier()
- bonus_dice / difficulty_modifiers (stat -> int) -> perform_skill_check()
- resistances (damage_type -> % reduction) -> get_resistance()
- immunities (condition/damage_type -> True) -> is_immune_to()

Ported directly from your Godot races/*.tres files (race_resource.gd),
14 races total. A few notes on the port:

- speed_modifier, sight_radius_tiles, and darkvision_radius_tiles from
  the Godot resource were dropped from this port - not needed on the
  Evennia side.
- xp_multiplier_overrides stores the same +/- DELTA convention as the
  Godot side (negative = cheaper/easier, positive = pricier/harder),
  not an absolute multiplier - get_xp_multiplier() below adds the
  delta to whatever base_cost the caller passes in, floored at 1,
  exactly like Race.get_xp_multiplier() in race_resource.gd.
- None of your .tres files set resistances, so every race below uses
  the script's own default (no resistances) unless noted.
- starting_vision ints from the .tres files (0/1/2) are mapped to
  NORMAL/LOWLIGHT/DARKVISION below - confirm this against your actual
  EntityStats.Vision enum ordering in Godot; swap VISION_LOWLIGHT and
  VISION_DARKVISION below if your enum orders them differently.
- The following innate_perks are referenced by race but the perk
  .tres files themselves weren't in the upload, so world/perks.py has
  placeholder mechanics for: stone_cunning, speak_with_animals,
  relentless_endurance, savage_attacks, lucky, lightfoot_nimbleness,
  cats_claws, feline_agility, hold_breath, natural_armor,
  shell_defense, shrink. Adjust their bonuses to match your real Perk
  resources.
"""

VISION_NORMAL = "NORMAL"
VISION_LOWLIGHT = "LOWLIGHT"
VISION_DARKVISION = "DARKVISION"

SIZE_TINY = "TINY"
SIZE_SMALL = "SMALL"
SIZE_MEDIUM = "MEDIUM"
SIZE_LARGE = "LARGE"
SIZE_HUGE = "HUGE"
SIZE_GARGANTUAN = "GARGANTUAN"

DEFAULT_RACE = "human"

RACES = {
    "human": {
        "display_name": "Human",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_NORMAL,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common"],
        "flat_bonuses": {},
        "innate_perks": [],
        "can_fly": False,
        "ignores_size_restrictions": False,
        # Jack-of-all-trades: every attribute is 1 cheaper to raise.
        "xp_multiplier_overrides": {
            "agility": -1, "appearance": -1, "charisma": -1, "cunning": -1,
            "endurance": -1, "influence": -1, "intelligence": -1,
            "might": -1, "willpower": -1,
        },
        "bonus_dice": {},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "elf": {
        "display_name": "Elf",
        "combat_speed_modifier": 1,
        "starting_vision": VISION_LOWLIGHT,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common", "Elvish"],
        "flat_bonuses": {},
        "innate_perks": [],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"agility": -2, "endurance": 2},
        "bonus_dice": {"Perception": 2, "willpower": 1},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "dwarf": {
        "display_name": "Dwarf",
        "combat_speed_modifier": -1,
        "starting_vision": VISION_NORMAL,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common", "Dwarven"],
        "flat_bonuses": {"hp": 1},
        "innate_perks": ["stone_cunning"],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"charisma": 2, "endurance": -2},
        "bonus_dice": {"endurance": 2},
        "difficulty_modifiers": {"Mining": -1, "Stonework": -1},
        "resistances": {},
        "immunities": {},
    },
    "gnome": {
        "display_name": "Gnome",
        "combat_speed_modifier": -1,
        "starting_vision": VISION_LOWLIGHT,
        "size_category": SIZE_SMALL,
        "languages": ["Common", "Gnomish"],
        "flat_bonuses": {},
        "innate_perks": [],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"endurance": -2, "might": 2},
        "bonus_dice": {"willpower": 1},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "goblin": {
        "display_name": "Goblin",
        "combat_speed_modifier": -1,
        "starting_vision": VISION_DARKVISION,
        "size_category": SIZE_SMALL,
        "languages": ["Common", "Goblin"],
        "flat_bonuses": {},
        "innate_perks": ["speak_with_animals"],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"agility": -1, "endurance": -1},
        "bonus_dice": {},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "half_elf": {
        "display_name": "Half Elf",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_LOWLIGHT,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common"],
        "flat_bonuses": {},
        "innate_perks": [],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {},
        "bonus_dice": {"Perception": 1},
        "difficulty_modifiers": {"Investigation": -1},
        "resistances": {},
        "immunities": {},
    },
    "half_orc": {
        "display_name": "Half Orc",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_DARKVISION,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common", "Orcish"],
        "flat_bonuses": {},
        "innate_perks": ["relentless_endurance", "savage_attacks"],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"charisma": 2, "intelligence": 2, "might": -2},
        "bonus_dice": {"Intimidation": 2},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "lightfeet": {
        "display_name": "Lightfeet",
        "combat_speed_modifier": -1,
        "starting_vision": VISION_NORMAL,
        "size_category": SIZE_SMALL,
        "languages": ["Common", "Lightfeet"],
        "flat_bonuses": {},
        "innate_perks": ["lucky", "lightfoot_nimbleness"],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"agility": -2, "might": 1},
        "bonus_dice": {"willpower": 2},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "mirari": {
        "display_name": "Mirari",
        "combat_speed_modifier": 1,
        "starting_vision": VISION_DARKVISION,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common", "Yssmera"],
        "flat_bonuses": {},
        "innate_perks": ["cats_claws", "feline_agility"],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"agility": -1, "appearance": -1, "willpower": 2},
        "bonus_dice": {"Perception": 2, "Stealth": 2},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "thalorim": {
        "display_name": "Thalorim",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_NORMAL,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common", "Thalorim"],
        "flat_bonuses": {},
        "innate_perks": ["hold_breath", "natural_armor", "shell_defense"],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"might": -2, "willpower": -1},
        "bonus_dice": {"Survival": 2},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "the_lost": {
        "display_name": "The Lost",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_LOWLIGHT,
        "size_category": SIZE_TINY,
        "languages": ["Common", "Sylvaraen"],
        "flat_bonuses": {},
        "innate_perks": ["shrink"],
        "can_fly": True,
        "ignores_size_restrictions": True,
        "xp_multiplier_overrides": {"agility": -3, "might": 4},
        "bonus_dice": {"willpower": 2},
        "difficulty_modifiers": {"Athletics": 2, "Thievery": -1},
        "resistances": {},
        "immunities": {},
    },
    "veilborn": {
        "display_name": "Veilborn",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_LOWLIGHT,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common", "Inferni"],
        "flat_bonuses": {},
        "innate_perks": [],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"charisma": 1, "intelligence": -1},
        "bonus_dice": {},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "drakari": {
        "display_name": "Drakari",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_NORMAL,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common", "Draconic"],
        "flat_bonuses": {},
        "innate_perks": [],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {},
        "bonus_dice": {},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {},
    },
    "eidolon": {
        "display_name": "Eidolon",
        "combat_speed_modifier": 0,
        "starting_vision": VISION_NORMAL,
        "size_category": SIZE_MEDIUM,
        "languages": ["Common"],
        "flat_bonuses": {},
        "innate_perks": [],
        "can_fly": False,
        "ignores_size_restrictions": False,
        "xp_multiplier_overrides": {"endurance": -2, "willpower": 2},
        "bonus_dice": {},
        "difficulty_modifiers": {},
        "resistances": {},
        "immunities": {"disease": True, "exhaustion": True, "sleep": True},
    },
}


def get_race_data(race_key):
    """Return the race dict for a given key, falling back to the default race."""
    return RACES.get(race_key, RACES[DEFAULT_RACE])


def get_bonus_dice(race_data, stat_name):
    return race_data.get("bonus_dice", {}).get(stat_name, 0)


def get_difficulty_modifier(race_data, stat_name):
    return race_data.get("difficulty_modifiers", {}).get(stat_name, 0)


def get_xp_multiplier(race_data, stat_or_skill_name, base_cost):
    """
    Mirrors Race.get_xp_multiplier() in race_resource.gd: xp_multiplier_overrides
    stores a delta (negative = cheaper, positive = pricier) relative to
    base_cost, not an absolute value. Floored at 1 so a race's discount
    can never zero out or invert a stat's cost.
    """
    delta = race_data.get("xp_multiplier_overrides", {}).get(stat_or_skill_name, 0)
    return max(base_cost + delta, 1)


def get_resistance(race_data, damage_type):
    return race_data.get("resistances", {}).get(damage_type, 0)


def is_immune_to(race_data, condition_name):
    return condition_name in race_data.get("immunities", {})
