"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

This typeclass mirrors Godot's `EntityStats.gd` resource as closely as
possible, field for field, so character data and rules stay portable
between the MUD and the game. One structural difference worth calling
out: Evennia's `.db` attributes persist to the database automatically,
so there's no equivalent needed here of EntityStats' to_save_dict() /
apply_save_dict() — every property below already survives a restart on
its own.

A second structural difference: Godot keeps four separate skill
dictionaries (combat_skills, magick_skills, life_skills,
survival_skills). Here they're stored as one flat dict keyed by skill
name, with world/skills.py's SKILL_CATEGORIES providing the same
category grouping for display purposes. get_skill_total_by_name()'s
"search all four dicts" behavior collapses into a single lookup as a
result.
"""

from evennia.objects.objects import DefaultCharacter

from .objects import ObjectParent
from world import body_parts as body_parts_registry
from world import dice
from world import perks as perks_registry
from world.races import (
    DEFAULT_RACE,
    SIZE_MEDIUM,
    VISION_NORMAL,
    get_bonus_dice,
    get_difficulty_modifier,
    get_race_data,
    get_resistance,
    get_xp_multiplier,
    is_immune_to,
)
from world.skills import (
    SKILL_CATEGORIES,
    canonical_skill_name,
    default_skills_dict,
)

# Encumbrance tuning (mirrors the constants at the top of EntityStats.gd)
ENCUMBRANCE_OVERAGE_CAP = 50.0
MIN_SPEED_FLOOR = 20.0

ATTRIBUTE_NAMES = (
    "might", "agility", "endurance",
    "intelligence", "cunning", "willpower",
    "charisma", "influence", "appearance",
)
VITAL_NAMES = ("hp", "max_hp", "mana", "max_mana", "stamina", "max_stamina")


class Character(ObjectParent, DefaultCharacter):
    """
    The Character just re-implements some of the Object's methods and hooks
    to represent a Character entity in-game.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Object child classes like this.

    """

    def at_object_creation(self):
        """
        Called once, when the object is first created.
        """
        super().at_object_creation()

        # ===== Identity =====
        self.db.sex = "unknown"  # NONE / MALE / FEMALE in Godot; free text here
        self.db.race = DEFAULT_RACE

        # ===== Vision (overwritten by apply_race_defaults() below) =====
        self.db.vision = VISION_NORMAL
        self.db.size_category = SIZE_MEDIUM

        # ===== Languages =====
        self.db.languages = []

        # ===== Movement =====
        self.db.base_speed = 300.0

        # ===== Attributes (default 1) =====
        self.db.might = 1
        self.db.agility = 1
        self.db.endurance = 1
        self.db.intelligence = 1
        self.db.cunning = 1
        self.db.willpower = 1
        self.db.charisma = 1
        self.db.influence = 1
        self.db.appearance = 1

        # ===== Vitals (matches EntityStats defaults exactly) =====
        self.db.hp = 5
        self.db.max_hp = 5
        self.db.mana = 1
        self.db.max_mana = 1
        self.db.stamina = 1
        self.db.max_stamina = 1
        self.db.weight = 0
        self.db.max_weight = 0

        # ===== Skills (flat dict, see module docstring) =====
        self.db.skills = default_skills_dict()

        # ===== Progression =====
        self.db.xp = 0

        # ===== Conditions (status effects: tag -> stacks) =====
        self.db.conditions = {}

        self.db.can_fly = False
        self.db.ignores_size_restrictions = False

        # ===== Backgrounds (id -> True) =====
        self.db.backgrounds = {}

        # ===== Perks (perk_id -> rank) =====
        self.db.perks = {}

        # ===== Modifiers: stat_or_skill_name -> {source_id: value} =====
        self.db.active_modifiers = {}

        # ===== Body parts (hit locations + equip slots, see body_parts) =====
        # part_id -> accumulated damage. Missing/0 = undamaged. Which
        # parts are even valid is derived from race (see body_parts
        # property below), not stored here.
        self.db.body_part_damage = {}
        # slot_id -> equipped item. Which slots are valid is likewise
        # derived from race (see equip_slots property below).
        self.db.equipment = {}

        # Apply race defaults (vision, size, languages, flat_bonuses,
        # innate_perks, can_fly, ignores_size_restrictions) then derive
        # max_weight.
        self.apply_race_defaults()

    def at_init(self):
        """
        Called every time this object is loaded into memory - e.g. on
        server reload/restart, and whenever an Account puppets it.

        NOTE: does NOT call ensure_data_integrity() here. at_init()
        also fires during the portal<->server session resync that
        happens on every reload, and writing attributes at that point
        throws "instance is on database None, value is on database
        default" - a database-routing timing issue with the resync,
        not something safe to paper over. The self-heal still runs
        safely from CmdSheet (a normal command context) - this hook
        is kept as a documented no-op spot rather than removed, so
        it's easy to find if reload-time healing is worth revisiting.
        """
        super().at_init()

    def ensure_data_integrity(self):
        """
        Self-healing check: fills in any .db fields this typeclass
        expects but that this particular object doesn't have yet
        (typically because the object was created before those fields
        existed). Safe to call as often as you like - existing values
        are never touched, only genuinely missing ones are filled in.

        Returns True if anything was healed (useful if a caller wants
        to know/announce that a repair happened).
        """
        healed = False

        def _ensure(key, default):
            nonlocal healed
            if not self.attributes.has(key):
                self.attributes.add(key, default)
                healed = True

        _ensure("sex", "unknown")
        _ensure("race", DEFAULT_RACE)

        _ensure("vision", VISION_NORMAL)
        _ensure("size_category", SIZE_MEDIUM)

        _ensure("languages", [])
        _ensure("base_speed", 300.0)

        for attr_name in ATTRIBUTE_NAMES:
            _ensure(attr_name, 1)

        _ensure("hp", 5)
        _ensure("max_hp", 5)
        _ensure("mana", 1)
        _ensure("max_mana", 1)
        _ensure("stamina", 1)
        _ensure("max_stamina", 1)
        _ensure("weight", 0)
        _ensure("max_weight", 0)

        _ensure("skills", default_skills_dict())
        _ensure("xp", 0)
        _ensure("conditions", {})
        _ensure("can_fly", False)
        _ensure("ignores_size_restrictions", False)
        _ensure("backgrounds", {})
        _ensure("perks", {})
        _ensure("active_modifiers", {})
        _ensure("body_part_damage", {})
        _ensure("equipment", {})

        # If skills existed but a newer skill was added to world/skills.py
        # since this character was created, backfill just the missing
        # keys rather than clobbering ranks the player already has.
        skills = self.attributes.get("skills", default={})
        defaults = default_skills_dict()
        missing_skills = {k: v for k, v in defaults.items() if k not in skills}
        if missing_skills:
            skills.update(missing_skills)
            self.attributes.add("skills", skills)
            healed = True

        return healed

    # ==================================================================
    # Race
    # ==================================================================
    @property
    def race(self):
        return self.attributes.get("race", default=DEFAULT_RACE)

    @race.setter
    def race(self, value):
        self.attributes.add("race", value)

    @property
    def race_data(self):
        return get_race_data(self.race)

    def apply_race_defaults(self):
        """Mirrors EntityStats.apply_race_defaults()."""
        race_data = self.race_data

        self.db.vision = race_data.get("starting_vision", VISION_NORMAL)
        self.db.size_category = race_data.get("size_category", SIZE_MEDIUM)

        for language_name in race_data.get("languages", []):
            self.learn_language(language_name)

        for stat_name, bonus in race_data.get("flat_bonuses", {}).items():
            self.add_modifier(stat_name, "race_bonus", bonus)

        for perk_id in race_data.get("innate_perks", []):
            self.grant_perk(perk_id)

        self.db.can_fly = race_data.get("can_fly", False)
        self.db.ignores_size_restrictions = race_data.get("ignores_size_restrictions", False)

        self.recalculate_max_weight()

    def remove_race_defaults(self):
        """Mirrors EntityStats.remove_race_defaults() (used by change_race)."""
        race_data = self.race_data
        for stat_name in race_data.get("flat_bonuses", {}):
            self.remove_modifier(stat_name, "race_bonus")
        for perk_id in race_data.get("innate_perks", []):
            self.remove_perk(perk_id)

    def change_race(self, new_race_key):
        """Mirrors EntityStats.change_race()."""
        self.remove_race_defaults()
        self.race = new_race_key
        self.apply_race_defaults()

        # Drop tracked damage/equipment for parts/slots the new race
        # doesn't have (e.g. losing tracked tail damage when a Mirari
        # changes into a Human).
        valid_parts = set(self.body_parts)
        damage = self.attributes.get("body_part_damage", default={})
        for part_id in list(damage):
            if part_id not in valid_parts:
                del damage[part_id]
        self.attributes.add("body_part_damage", damage)

        valid_slots = set(self.equip_slots)
        equipment = self.attributes.get("equipment", default={})
        for slot_id in list(equipment):
            if slot_id not in valid_slots:
                del equipment[slot_id]
        self.attributes.add("equipment", equipment)

    def get_resistance(self, damage_type):
        """Mirrors Race.get_resistance() - % reduction (0-100) from race data."""
        return get_resistance(self.race_data, damage_type)

    def is_immune_to(self, condition_name):
        """Mirrors Race.is_immune_to() - race-granted immunity, e.g. 'disease'."""
        return is_immune_to(self.race_data, condition_name)

    # ==================================================================
    # Body parts (hit locations) - see world/body_parts.py
    # ==================================================================
    @property
    def body_parts(self):
        """List of body part ids this character has, derived from race."""
        return body_parts_registry.get_body_parts_for_race(self.race)

    def has_body_part(self, part_id):
        return part_id in self.body_parts

    def get_body_part_damage(self, part_id):
        return self.attributes.get("body_part_damage", default={}).get(part_id, 0)

    def damage_body_part(self, part_id, amount):
        """
        Applies hit-location damage to a specific body part - separate
        from general self.db.hp, this is for called-shot/limb-specific
        damage tracking. Returns the part's new accumulated damage, or
        None if this character doesn't have that part at all (e.g.
        damaging "tail" on a Human is a no-op).
        """
        if not self.has_body_part(part_id):
            return None
        damage = self.attributes.get("body_part_damage", default={})
        damage[part_id] = max(0, damage.get(part_id, 0) + amount)
        self.attributes.add("body_part_damage", damage)
        return damage[part_id]

    def heal_body_part(self, part_id, amount=None):
        """Heals accumulated damage on a body part. amount=None clears it fully."""
        damage = self.attributes.get("body_part_damage", default={})
        if part_id not in damage:
            return
        if amount is None or damage[part_id] - amount <= 0:
            del damage[part_id]
        else:
            damage[part_id] -= amount
        self.attributes.add("body_part_damage", damage)

    def is_body_part_disabled(self, part_id, threshold=None):
        """
        A part is disabled once its tracked damage meets/exceeds a
        threshold. Defaults to that part's vitality_weight share of
        max_hp (so a tougher character's tail/limbs can absorb more
        before going limp) - pass an explicit threshold to override.
        """
        part_data = body_parts_registry.get_body_part_data(part_id)
        if not part_data or not self.has_body_part(part_id):
            return False
        if threshold is None:
            threshold = max(1, round(self.max_hp * part_data["vitality_weight"]))
        return self.get_body_part_damage(part_id) >= threshold

    @property
    def body_part_damage(self):
        return dict(self.attributes.get("body_part_damage", default={}))

    # ==================================================================
    # Equipment (body-part-driven wear slots) - see world/body_parts.py
    # ==================================================================
    @property
    def equip_slots(self):
        """Wear slots available to this character, derived from race body parts."""
        return body_parts_registry.get_equip_slots_for_race(self.race)

    def can_use_slot(self, slot_id):
        return slot_id in self.equip_slots

    def get_equipped(self, slot_id):
        return self.attributes.get("equipment", default={}).get(slot_id)

    def can_equip_item(self, item, slot_id):
        """
        Checks whether `item` could be equipped to slot_id right now,
        without actually equipping it. Mirrors Equipment.can_equip()
        on the Godot side (item size vs. wielder size, unless the
        wielder's race sets ignores_size_restrictions - currently just
        The Lost). Returns (True, None) on success, or
        (False, reason_str) explaining why not.
        """
        if not self.can_use_slot(slot_id):
            available = ", ".join(
                body_parts_registry.slot_display_name(s) for s in self.equip_slots
            )
            return False, (
                f"You don't have a '{body_parts_registry.slot_display_name(slot_id)}' slot. "
                f"Your available slots: {available}."
            )
        if item.location != self:
            return False, "You aren't carrying that."
        if self.get_equipped(slot_id) is not None:
            occupant = self.get_equipped(slot_id)
            return False, (
                f"You're already wearing {occupant.get_display_name(self)} "
                f"on your {body_parts_registry.slot_display_name(slot_id)}. Remove it first."
            )

        size_matters = item.attributes.get("size_matters", default=True)
        if size_matters and not self.attributes.get("ignores_size_restrictions", default=False):
            item_size = item.attributes.get("size_category", default=None)
            if item_size is not None and item_size != self.size_category:
                return False, (
                    f"That's sized for a {item_size} wearer; you're {self.size_category}."
                )

        return True, None

    def equip(self, item, slot_id):
        """
        Wears `item` (an Object this character is carrying) in
        slot_id. Fails (returns False) if can_equip_item() rejects it
        - see that method for the specific reasons. On success
        returns True.
        """
        can_equip, _reason = self.can_equip_item(item, slot_id)
        if not can_equip:
            return False
        equipment = self.attributes.get("equipment", default={})
        equipment[slot_id] = item
        self.attributes.add("equipment", equipment)
        return True

    def unequip(self, slot_id):
        """Removes whatever is worn in slot_id. Returns the item, or None."""
        equipment = self.attributes.get("equipment", default={})
        item = equipment.pop(slot_id, None)
        if item is not None:
            self.attributes.add("equipment", equipment)
        return item

    @property
    def equipment(self):
        return dict(self.attributes.get("equipment", default={}))

    # ==================================================================
    # Vision / size / languages
    # ==================================================================
    @property
    def vision(self):
        return self.attributes.get("vision", default=VISION_NORMAL)

    @vision.setter
    def vision(self, value):
        self.attributes.add("vision", value)

    @property
    def size_category(self):
        return self.attributes.get("size_category", default=SIZE_MEDIUM)

    @property
    def languages(self):
        return list(self.attributes.get("languages", default=[]))

    def knows_language(self, language_name):
        return language_name in self.languages

    def learn_language(self, language_name):
        languages = self.attributes.get("languages", default=[])
        if language_name not in languages:
            languages.append(language_name)
            self.attributes.add("languages", languages)

    # ==================================================================
    # Attributes
    # ==================================================================
    @property
    def might(self):
        return self.attributes.get("might", default=1)

    @might.setter
    def might(self, value):
        self.attributes.add("might", value)

    @property
    def agility(self):
        return self.attributes.get("agility", default=1)

    @agility.setter
    def agility(self, value):
        self.attributes.add("agility", value)

    @property
    def endurance(self):
        return self.attributes.get("endurance", default=1)

    @endurance.setter
    def endurance(self, value):
        self.attributes.add("endurance", value)

    @property
    def intelligence(self):
        return self.attributes.get("intelligence", default=1)

    @intelligence.setter
    def intelligence(self, value):
        self.attributes.add("intelligence", value)

    @property
    def cunning(self):
        return self.attributes.get("cunning", default=1)

    @cunning.setter
    def cunning(self, value):
        self.attributes.add("cunning", value)

    @property
    def willpower(self):
        return self.attributes.get("willpower", default=1)

    @willpower.setter
    def willpower(self, value):
        self.attributes.add("willpower", value)

    @property
    def charisma(self):
        return self.attributes.get("charisma", default=1)

    @charisma.setter
    def charisma(self, value):
        self.attributes.add("charisma", value)

    @property
    def influence(self):
        return self.attributes.get("influence", default=1)

    @influence.setter
    def influence(self, value):
        self.attributes.add("influence", value)

    @property
    def appearance(self):
        return self.attributes.get("appearance", default=1)

    @appearance.setter
    def appearance(self, value):
        self.attributes.add("appearance", value)

    @property
    def sex(self):
        return self.attributes.get("sex", default="unknown")

    @sex.setter
    def sex(self, value):
        self.attributes.add("sex", value)

    # ==================================================================
    # Vitals
    # ==================================================================
    @property
    def hp(self):
        return self.attributes.get("hp", default=5)

    @hp.setter
    def hp(self, value):
        self.attributes.add("hp", value)

    @property
    def max_hp(self):
        return self.attributes.get("max_hp", default=5)

    @max_hp.setter
    def max_hp(self, value):
        self.attributes.add("max_hp", value)

    @property
    def mana(self):
        return self.attributes.get("mana", default=1)

    @mana.setter
    def mana(self, value):
        self.attributes.add("mana", value)

    @property
    def max_mana(self):
        return self.attributes.get("max_mana", default=1)

    @max_mana.setter
    def max_mana(self, value):
        self.attributes.add("max_mana", value)

    @property
    def stamina(self):
        return self.attributes.get("stamina", default=1)

    @stamina.setter
    def stamina(self, value):
        self.attributes.add("stamina", value)

    @property
    def max_stamina(self):
        return self.attributes.get("max_stamina", default=1)

    @max_stamina.setter
    def max_stamina(self, value):
        self.attributes.add("max_stamina", value)

    @property
    def weight(self):
        return self.attributes.get("weight", default=0)

    @weight.setter
    def weight(self, value):
        self.attributes.add("weight", value)
        self.recalculate_encumbrance()

    @property
    def max_weight(self):
        return self.attributes.get("max_weight", default=0)

    @max_weight.setter
    def max_weight(self, value):
        self.attributes.add("max_weight", value)

    def recalculate_max_weight(self):
        """Mirrors EntityStats.recalculate_max_weight()."""
        self.db.max_weight = (self.might * 10) + 25

    @property
    def combat_speed(self):
        """
        Derived: agility * 2 + player_race.combat_speed_modifier.
        Reads base agility (not get_attribute_total()) — matches
        recalculate_combat_speed()'s comment that equipment/condition
        modifiers to agility don't factor in here.
        """
        return (self.agility * 2) + self.race_data.get("combat_speed_modifier", 0)

    def is_incapacitated(self):
        """Mirrors is_incapacitated(): true at 0 HP."""
        return self.hp <= 0

    def is_dead(self):
        """Mirrors is_dead(): true at negative max HP."""
        return self.hp <= -self.max_hp

    # ==================================================================
    # Encumbrance / movement
    # ==================================================================
    def recalculate_encumbrance(self):
        """Mirrors EntityStats.recalculate_encumbrance()."""
        if self.max_weight <= 0:
            return

        overage = self.weight - self.max_weight
        if overage <= 0:
            self.remove_modifier("speed", "encumbrance")
            return

        full_speed = self.base_speed
        usable_range = full_speed - MIN_SPEED_FLOOR
        rate = usable_range / ENCUMBRANCE_OVERAGE_CAP

        clamped_overage = min(overage, ENCUMBRANCE_OVERAGE_CAP)
        penalty = -clamped_overage * rate

        self.add_modifier("speed", "encumbrance", int(penalty))

    @property
    def base_speed(self):
        return self.attributes.get("base_speed", default=300.0)

    @base_speed.setter
    def base_speed(self, value):
        self.attributes.add("base_speed", value)

    def get_effective_speed(self):
        """Mirrors EntityStats.get_effective_speed()."""
        speed = self.base_speed
        speed += self.get_modifier_total("speed")
        return max(speed, 20.0)

    # ==================================================================
    # Skills
    # ==================================================================
    def get_skill(self, skill_name):
        """Return the base rank of a skill (0 if untrained/unrecognized)."""
        canonical = canonical_skill_name(skill_name)
        if canonical is None:
            return 0
        skills = self.attributes.get("skills", default={})
        return skills.get(canonical, 0)

    # Mirrors EntityStats.get_skill_rank_by_name()
    get_skill_rank = get_skill

    def set_skill(self, skill_name, rank):
        """
        Set a skill's rank directly. Raises ValueError if the skill name
        isn't recognized (see world/skills.py for the full list).
        """
        canonical = canonical_skill_name(skill_name)
        if canonical is None:
            raise ValueError(f"'{skill_name}' is not a recognized skill.")
        skills = self.attributes.get("skills", default={})
        skills[canonical] = max(0, int(rank))
        self.attributes.add("skills", skills)

    def improve_skill(self, skill_name, amount=1):
        """Raise a skill's rank by `amount` (can be negative)."""
        self.set_skill(skill_name, self.get_skill(skill_name) + amount)

    def get_skill_total(self, skill_name):
        """
        Mirrors get_skill_total_by_name(): base rank + active modifiers.
        """
        canonical = canonical_skill_name(skill_name)
        if canonical is None:
            return 0
        return self.get_skill(canonical) + self.get_modifier_total(canonical)

    # ==================================================================
    # Modifiers ( stat_or_skill_name -> {source_id: value} )
    # ==================================================================
    def get_modifier_total(self, stat_name):
        active_modifiers = self.attributes.get("active_modifiers", default={})
        sources = active_modifiers.get(stat_name)
        if not sources:
            return 0
        return sum(sources.values())

    def add_modifier(self, stat_name, source_id, value):
        active_modifiers = self.attributes.get("active_modifiers", default={})
        active_modifiers.setdefault(stat_name, {})[source_id] = value
        self.attributes.add("active_modifiers", active_modifiers)

    def remove_modifier(self, stat_name, source_id):
        active_modifiers = self.attributes.get("active_modifiers", default={})
        if stat_name in active_modifiers:
            active_modifiers[stat_name].pop(source_id, None)
            if not active_modifiers[stat_name]:
                del active_modifiers[stat_name]
            self.attributes.add("active_modifiers", active_modifiers)

    @property
    def active_modifiers(self):
        return dict(self.attributes.get("active_modifiers", default={}))

    def get_attribute_total(self, attribute_name):
        """For attributes/vitals (direct properties, e.g. 'might', 'max_hp')."""
        return getattr(self, attribute_name) + self.get_modifier_total(attribute_name)

    # ==================================================================
    # Conditions (status effects)
    # ==================================================================
    def add_condition(self, condition_name, value=1):
        conditions = self.attributes.get("conditions", default={})
        conditions[condition_name] = value
        self.attributes.add("conditions", conditions)

    def remove_condition(self, condition_name):
        conditions = self.attributes.get("conditions", default={})
        if condition_name in conditions:
            del conditions[condition_name]
            self.attributes.add("conditions", conditions)

    def has_condition(self, condition_name):
        conditions = self.attributes.get("conditions", default={})
        return condition_name in conditions

    def get_condition_value(self, condition_name):
        conditions = self.attributes.get("conditions", default={})
        return conditions.get(condition_name, 0)

    @property
    def conditions(self):
        return dict(self.attributes.get("conditions", default={}))

    def get_required_stealth_successes(self):
        """Mirrors get_required_stealth_successes()."""
        return self.get_condition_value("sneaking")

    def if_flying(self):
        """
        Mirrors if_flying(). A wing-flying race whose wings are
        disabled (see is_body_part_disabled()) can't fly on that
        racial ability alone, though magical/condition-based flight
        (e.g. a "flying" condition from a spell) still works.
        """
        can_fly_racially = bool(self.attributes.get("can_fly", default=False))
        if can_fly_racially and self.has_body_part("wings") and self.is_body_part_disabled("wings"):
            can_fly_racially = False
        return can_fly_racially or self.has_condition("flying")

    # ==================================================================
    # Backgrounds
    # ==================================================================
    def has_background(self, background_id):
        backgrounds = self.attributes.get("backgrounds", default={})
        return background_id in backgrounds

    def add_background(self, background_id):
        backgrounds = self.attributes.get("backgrounds", default={})
        backgrounds[background_id] = True
        self.attributes.add("backgrounds", backgrounds)

    @property
    def backgrounds(self):
        return dict(self.attributes.get("backgrounds", default={}))

    # ==================================================================
    # Perks
    # ==================================================================
    def has_perk(self, perk_id):
        perks = self.attributes.get("perks", default={})
        return perk_id in perks

    def get_perk_rank(self, perk_id):
        perks = self.attributes.get("perks", default={})
        return perks.get(perk_id, 0)

    def add_perk(self, perk_id):
        """Bare rank bump, no bonuses attached — mirrors add_perk()."""
        perks = self.attributes.get("perks", default={})
        perks[perk_id] = self.get_perk_rank(perk_id) + 1
        self.attributes.add("perks", perks)

    def grant_perk(self, perk_id):
        """
        Grants a registered perk (world/perks.py) and applies its
        bonuses as modifiers. Mirrors apply_perk(perk: Perk). Respects
        stackable/max_rank: a non-stackable perk you already have is a
        no-op, and rank never exceeds max_rank.
        """
        perk_data = perks_registry.get_perk_data(perk_id)
        if not perk_data:
            return

        current_rank = self.get_perk_rank(perk_id)
        if current_rank > 0 and not perk_data.get("stackable", False):
            return

        new_rank = min(current_rank + 1, perk_data.get("max_rank", 1))
        if new_rank == current_rank:
            return

        perks = self.attributes.get("perks", default={})
        perks[perk_id] = new_rank
        self.attributes.add("perks", perks)

        for stat_name, bonus in perk_data.get("bonuses", {}).items():
            self.add_modifier(stat_name, f"perk_{perk_id}", bonus * new_rank)

    def remove_perk(self, perk_id):
        """Mirrors remove_perk(): drops rank to 0 and removes its modifiers."""
        perks = self.attributes.get("perks", default={})
        if perk_id not in perks:
            return
        perk_data = perks_registry.get_perk_data(perk_id)

        del perks[perk_id]
        self.attributes.add("perks", perks)

        if perk_data:
            for stat_name in perk_data.get("bonuses", {}):
                self.remove_modifier(stat_name, f"perk_{perk_id}")

    @property
    def perks(self):
        return dict(self.attributes.get("perks", default={}))

    # ==================================================================
    # Progression / XP spending
    # ==================================================================
    @property
    def xp(self):
        return self.attributes.get("xp", default=0)

    @xp.setter
    def xp(self, value):
        self.attributes.add("xp", value)

    def try_increase_attribute(self, attribute_name):
        """Mirrors try_increase_attribute(): base cost 10 * new rank."""
        return self._try_increase(attribute_name, 10)

    def try_increase_vital(self, vital_name):
        """Mirrors try_increase_vital(): max_hp costs 10/rank, others 8/rank."""
        base_cost = 10 if vital_name == "max_hp" else 8
        return self._try_increase(vital_name, base_cost)

    def try_increase_skill(self, skill_name):
        """Mirrors try_increase_skill()."""
        canonical = canonical_skill_name(skill_name)
        if canonical is None:
            return False
        current = self.get_skill(canonical)
        new_rank = current + 1
        base_cost = 8
        multiplier = get_xp_multiplier(self.race_data, canonical, base_cost)
        cost = new_rank * multiplier

        if self.xp < cost:
            return False
        self.xp -= cost
        self.set_skill(canonical, new_rank)
        return True

    def try_decrease_skill(self, skill_name, floor=0):
        """Mirrors try_decrease_skill(): refunds what the current rank cost."""
        canonical = canonical_skill_name(skill_name)
        if canonical is None:
            return False
        current = self.get_skill(canonical)
        if current <= floor:
            return False
        base_cost = 8
        multiplier = get_xp_multiplier(self.race_data, canonical, base_cost)
        refund = current * multiplier

        self.xp += refund
        self.set_skill(canonical, current - 1)
        return True

    def try_decrease_attribute(self, attribute_name, floor=1):
        return self._try_decrease(attribute_name, 10, floor)

    def try_decrease_vital(self, vital_name, floor):
        base_cost = 10 if vital_name == "max_hp" else 8
        return self._try_decrease(vital_name, base_cost, floor)

    def _try_increase(self, property_name, base_multiplier):
        current = getattr(self, property_name)
        new_rank = current + 1
        multiplier = get_xp_multiplier(self.race_data, property_name, base_multiplier)
        cost = new_rank * multiplier

        if self.xp < cost:
            return False

        self.xp -= cost
        setattr(self, property_name, new_rank)
        if property_name == "might":
            self.recalculate_max_weight()
        return True

    def _try_decrease(self, property_name, base_multiplier, floor):
        current = getattr(self, property_name)
        if current <= floor:
            return False
        multiplier = get_xp_multiplier(self.race_data, property_name, base_multiplier)
        refund = current * multiplier

        self.xp += refund
        setattr(self, property_name, current - 1)
        if property_name == "might":
            self.recalculate_max_weight()
        return True

    # ==================================================================
    # Dice checks
    # ==================================================================
    def perform_skill_check(self, attribute_name, skill_name, required_successes,
                             extra_bonus_dice=0, announce=True):
        """
        Mirrors EntityStats.perform_skill_check() exactly: attribute
        total + skill total form the base pool, race bonus_dice/
        difficulty_modifiers adjust bonus dice and threshold, and
        extra_bonus_dice covers situational bonuses (e.g. thief's tools)
        that aren't part of the character's permanent data.

        Returns a dice.DiceRollResult.
        """
        attribute_name = attribute_name.lower()
        canonical_skill = canonical_skill_name(skill_name)
        if canonical_skill is None:
            raise ValueError(f"'{skill_name}' is not a recognized skill.")

        attr_total = self.get_attribute_total(attribute_name)
        skill_total = self.get_skill_total(canonical_skill)
        pool_size = attr_total + skill_total

        race_data = self.race_data
        race_attr_bonus = get_bonus_dice(race_data, attribute_name)
        race_skill_bonus = get_bonus_dice(race_data, canonical_skill)
        bonus_dice = extra_bonus_dice + race_attr_bonus + race_skill_bonus

        race_attr_diff = get_difficulty_modifier(race_data, attribute_name)
        race_skill_diff = get_difficulty_modifier(race_data, canonical_skill)
        threshold = dice.DEFAULT_SUCCESS_THRESHOLD + race_attr_diff + race_skill_diff

        result = dice.roll_pool(
            pool_size,
            required_successes=required_successes,
            threshold=threshold,
            bonus_dice=bonus_dice,
        )

        if announce:
            label = f"{attribute_name.capitalize()} / {canonical_skill}"
            self.msg(f"|c[{label}]|n {result}")

        return result

    # Convenience alias matching the simpler API used by earlier commands.
    def roll_check(self, attribute_name, skill_name, required_successes=1,
                    extra_bonus_dice=0, announce=True):
        return self.perform_skill_check(
            attribute_name, skill_name, required_successes,
            extra_bonus_dice=extra_bonus_dice, announce=announce,
        )
