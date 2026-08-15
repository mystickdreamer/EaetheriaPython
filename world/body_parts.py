"""
Body Parts

Defines the set of body parts a character has, keyed off race. This
exists for two reasons:

1. Hit locations - a body part can take targeted ("called shot")
   damage separately from general self.db.hp, tracked via
   Character.damage_body_part()/get_body_part_damage(). A part that's
   taken enough damage is "disabled" (see is_body_part_disabled()),
   which can carry gameplay consequences - e.g. Character.if_flying()
   already checks a disabled "wings" part and grounds the character
   even if their race can normally fly.
2. Equipment slots - each body part exposes one or more wear slots
   (see BODY_PARTS[...]["equip_slots"]). Character.equip()/unequip()
   only allow gear onto slots that exist on the character's actual
   body, derived from race - a Human can't equip anything to "tail"
   or "wings", a Mirari can't use "wings", etc.

Every race gets the same baseline humanoid frame (BASE_BODY_PARTS).
On top of that, RACE_BODY_PART_EXTRAS adds racial parts pulled from
the Godot appearance data (races/*.tres available_tails/available_wings/
available_horns/available_shells): a tail for Drakari/Mirari/Thalorim/
Veilborn, wings for Drakari/The Lost, horns for Drakari/Half Orc/
Veilborn, and a shell for Thalorim.

vitality_weight is each part's rough share of the character's overall
max_hp, used as the default disable threshold in
is_body_part_disabled() - the 10 base parts sum to 0.90, leaving
headroom so a race with a racial part (tail/wings, 0.05 each) doesn't
have its base parts renormalized every time a new racial part gets
added later.

Equip slots, listed body-part by body-part:
  head        -> head, ears
  torso       -> torso, back, neck, waist
  left_arm    -> arms, left_wrist, shoulders  ("arms" is one two-armed
  right_arm   -> arms, right_wrist, shoulders  garment, like sleeves/
                                                bracers, shared with the
                                                other arm; "shoulders" is
                                                likewise one pauldron set
                                                shared across both arms;
                                                wrists split left/right)
  left_hand   -> left_ring, wielded
  right_hand  -> right_ring, offhand
  left_leg    -> legs
  right_leg   -> legs
  left_foot   -> feet
  right_foot  -> feet
  tail        -> tail                     (Drakari/Mirari/Thalorim/Veilborn)
  wings       -> wings                    (Drakari/The Lost)
  horns       -> horns                    (Drakari/Half Orc/Veilborn)
  shell       -> shell                    (Thalorim)

Plus UNIVERSAL_EQUIP_SLOTS, granted to every character regardless of
race/body parts:
  floaty      -> a hovering trinket/accessory not tied to any specific
                 body part (a familiar orb, an orbiting rune, etc.)
"""

BODY_PARTS = {
    "head": {
        "display_name": "Head",
        "damageable": True,
        "vitality_weight": 0.20,
        "equip_slots": ["head", "ears"],
        "critical": True,
    },
    "torso": {
        "display_name": "Torso",
        "damageable": True,
        "vitality_weight": 0.30,
        "equip_slots": ["torso", "back", "neck", "waist"],
        "critical": True,
    },
    "left_arm": {
        "display_name": "Left Arm",
        "damageable": True,
        "vitality_weight": 0.075,
        "equip_slots": ["arms", "left_wrist", "shoulders"],
        "critical": False,
    },
    "right_arm": {
        "display_name": "Right Arm",
        "damageable": True,
        "vitality_weight": 0.075,
        "equip_slots": ["arms", "right_wrist", "shoulders"],
        "critical": False,
    },
    "left_hand": {
        "display_name": "Left Hand",
        "damageable": True,
        "vitality_weight": 0.025,
        "equip_slots": ["left_ring", "wielded"],
        "critical": False,
    },
    "right_hand": {
        "display_name": "Right Hand",
        "damageable": True,
        "vitality_weight": 0.025,
        "equip_slots": ["right_ring", "offhand"],
        "critical": False,
    },
    "left_leg": {
        "display_name": "Left Leg",
        "damageable": True,
        "vitality_weight": 0.075,
        "equip_slots": ["legs"],
        "critical": False,
    },
    "right_leg": {
        "display_name": "Right Leg",
        "damageable": True,
        "vitality_weight": 0.075,
        "equip_slots": ["legs"],
        "critical": False,
    },
    "left_foot": {
        "display_name": "Left Foot",
        "damageable": True,
        "vitality_weight": 0.025,
        "equip_slots": ["feet"],
        "critical": False,
    },
    "right_foot": {
        "display_name": "Right Foot",
        "damageable": True,
        "vitality_weight": 0.025,
        "equip_slots": ["feet"],
        "critical": False,
    },
    # ---- Racial parts (see RACE_BODY_PART_EXTRAS below) ----
    "tail": {
        "display_name": "Tail",
        "damageable": True,
        "vitality_weight": 0.05,
        "equip_slots": ["tail"],
        "critical": False,
    },
    "wings": {
        "display_name": "Wings",
        "damageable": True,
        "vitality_weight": 0.05,
        "equip_slots": ["wings"],
        "critical": False,
    },
    "horns": {
        "display_name": "Horns",
        "damageable": True,
        "vitality_weight": 0.025,
        "equip_slots": ["horns"],
        "critical": False,
    },
    "shell": {
        "display_name": "Shell",
        "damageable": True,
        "vitality_weight": 0.05,
        "equip_slots": ["shell"],
        "critical": False,
    },
}

# Every race starts from this same humanoid frame.
BASE_BODY_PARTS = [
    "head", "torso",
    "left_arm", "right_arm",
    "left_hand", "right_hand",
    "left_leg", "right_leg",
    "left_foot", "right_foot",
]

# Racial parts on top of the base frame - ported from which races
# expose available_tails/available_wings/available_horns/available_shells
# in their Godot Race resource.
RACE_BODY_PART_EXTRAS = {
    "drakari": ["tail", "wings", "horns"],
    "mirari": ["tail"],
    "thalorim": ["tail", "shell"],
    "veilborn": ["tail", "horns"],
    "the_lost": ["wings"],
    "half_orc": ["horns"],
}

# Slots every character gets regardless of race/body parts - not tied
# to a specific limb.
UNIVERSAL_EQUIP_SLOTS = ["floaty"]

# Display order + labels for equipment/body sheets. Not every slot
# here maps to a body part (see UNIVERSAL_EQUIP_SLOTS).
SLOT_DISPLAY_NAMES = {
    "floaty": "Floating",
    "head": "Head",
    "ears": "Ears",
    "neck": "Neck",
    "torso": "Torso",
    "back": "Back",
    "waist": "Waist",
    "shoulders": "Shoulders",
    "arms": "Arms",
    "left_wrist": "Left Wrist",
    "right_wrist": "Right Wrist",
    "left_ring": "Left Ring",
    "right_ring": "Right Ring",
    "legs": "Legs",
    "feet": "Feet",
    "wielded": "Wielded",
    "offhand": "Offhand",
    "tail": "Tail",
    "wings": "Wings",
    "horns": "Horns",
    "shell": "Shell",
}

SLOT_DISPLAY_ORDER = [
    "floaty", "head", "ears", "neck", "torso", "back", "waist", "shoulders",
    "arms", "left_wrist", "right_wrist", "left_ring", "right_ring",
    "legs", "feet", "wielded", "offhand", "tail", "wings", "horns", "shell",
]


def get_body_parts_for_race(race_key):
    """Return the full ordered list of body part ids this race has."""
    parts = list(BASE_BODY_PARTS)
    for part_id in RACE_BODY_PART_EXTRAS.get(race_key, []):
        if part_id not in parts:
            parts.append(part_id)
    return parts


def get_body_part_data(part_id):
    return BODY_PARTS.get(part_id)


def get_equip_slots_for_race(race_key):
    """
    Return the deduped, display-ordered list of equip slot ids
    available to this race - e.g. both legs share one "legs" slot
    (pants cover both), so this collapses duplicates rather than
    exposing them per-part. Always includes UNIVERSAL_EQUIP_SLOTS.
    """
    slots = set(UNIVERSAL_EQUIP_SLOTS)
    for part_id in get_body_parts_for_race(race_key):
        part_data = BODY_PARTS.get(part_id, {})
        slots.update(part_data.get("equip_slots", []))
    return [slot_id for slot_id in SLOT_DISPLAY_ORDER if slot_id in slots]


def get_parts_for_slot(race_key, slot_id):
    """Which of this race's body parts does a given equip slot cover?"""
    return [
        part_id
        for part_id in get_body_parts_for_race(race_key)
        if slot_id in BODY_PARTS.get(part_id, {}).get("equip_slots", [])
    ]


def slot_display_name(slot_id):
    return SLOT_DISPLAY_NAMES.get(slot_id, slot_id)


def is_critical_part(part_id):
    return BODY_PARTS.get(part_id, {}).get("critical", False)
