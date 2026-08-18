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
from world import magick_words as magick_words_registry
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
from world import immortal_data
from world.immortal_data import DEFAULT_BAMF_IN, DEFAULT_BAMF_OUT

# Encumbrance tuning (mirrors the constants at the top of EntityStats.gd)
ENCUMBRANCE_OVERAGE_CAP = 50.0
MIN_SPEED_FLOOR = 20.0

# XP awarded the first time a character ever enters a given room - see
# at_post_move() below. Small and fractional on purpose (xp is a float
# specifically to let rewards like this actually accumulate instead of
# rounding to 0) - easy to retune.
EXPLORATION_XP_REWARD = 0.01

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
        # Which known language speech (see CmdSay) is currently sent
        # in. Not touched by apply_race_defaults() below (that method
        # mirrors EntityStats.apply_race_defaults() 1:1 - see its
        # docstring), so this stays a plain hardcoded default rather
        # than something derived from race data. "Common" is safe as
        # a default because every race in world/races.py starts with
        # it. Change with 'speak <language>' (commands/command.py).
        self.db.speaking_language = "Common"

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

        # ===== Memorized Teleport Locations =====
        # Player defined name -> Eaetheria room database ID
        self.db.memorized_locations = {}

        # ===== Magick words =====
        # Word ids (world/magick_words.py) this character has actually
        # learned - see CmdStudy in commands/command.py. Meeting a
        # word's min_skill only means the character COULD learn it;
        # it doesn't put the word here by itself (design doc: two
        # characters at the same skill rank can know different words).
        self.db.known_magick_words = []
        # Whether this character offers their known words up for
        # others to 'study' them as a teacher (design doc's "NPC
        # teachers" source). Off by default so two ordinary players
        # can't just study each other to instantly copy vocabulary -
        # a builder/staff member flips this on for a dedicated teacher
        # NPC (once mobs have their own typeclass) or a player can be
        # granted it as a background/perk-driven ability later. Same
        # "deliberate opt-in switch" shape as Character.holylight.
        self.db.teaches_magick_words = False

        # ===== Progression =====
        # Float, not int - lets small fractional rewards (see
        # EXPLORATION_XP_REWARD / at_post_move() below) actually
        # accumulate instead of rounding away to 0.
        self.db.xp = 0.0

        # room_id -> True for every room this character has ever
        # entered - see at_post_move() below. Dict-of-True, same shape
        # as Room.db.room_flags/Character.db.perks elsewhere in this
        # file: O(1) "have I been here" checks.
        self.db.explored_rooms = {}

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

        # ===== Immortal/staff flavor (see world/immortal_data.py) =====
        # Harmless to store on every character - only ever surfaced
        # through CmdImm, which is locked to Builder+.
        self.db.bamf_in = DEFAULT_BAMF_IN
        self.db.bamf_out = DEFAULT_BAMF_OUT

        # Off by default even for Builder+ - holylight is a deliberate
        # switch (see CmdHolylight), not something tied automatically
        # to permission level. Read by ObjectParent.get_extra_display_
        # name_info()/get_numbered_name() in typeclasses/objects.py.
        self.db.holylight = False

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
        _ensure("speaking_language", "Common")
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
        _ensure("memorized_locations", {})
        _ensure("known_magick_words", [])
        _ensure("teaches_magick_words", False)
        _ensure("xp", 0.0)
        _ensure("explored_rooms", {})
        _ensure("conditions", {})
        _ensure("can_fly", False)
        _ensure("ignores_size_restrictions", False)
        _ensure("backgrounds", {})
        _ensure("perks", {})
        _ensure("active_modifiers", {})
        _ensure("body_part_damage", {})
        _ensure("equipment", {})

        _ensure("bamf_in", DEFAULT_BAMF_IN)
        _ensure("bamf_out", DEFAULT_BAMF_OUT)
        _ensure("holylight", False)

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

    @property
    def speaking_language(self):
        """
        The language `say` (CmdSay in commands/command.py) currently
        speaks in. Plain accessor, no validation here - CmdSpeak is
        what checks the character actually knows a language before
        switching to it (same split as most Character properties:
        `race`'s setter is likewise a plain passthrough, with
        whatever command sets it doing the validation).
        """
        return self.attributes.get("speaking_language", default="Common")

    @speaking_language.setter
    def speaking_language(self, value):
        self.attributes.add("speaking_language", value)

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

    @property
    def memorized_locations(self):
        """
        Permanent teleport destinations memorized by this character

        Stored as:
            player-defined location name -> Evennia room database ID

        The room ID is intentionally never exposed to the player
        """
        return dict(self.attributes.get("memorized_locations", default={}))

    def get_memorized_location_capacity(self):
        """
        Return the number of permanent locations this character
        can memorize. Intelligence determines capacity.
        """
        return max(1, self.get_attribute_total("intelligence"))

    def has_memorized_location(self, name):
        """Return True if a location with this name is already memoriezed"""
        name_key = name.casefold()
        return any(
            stored_name.casefold() == name_key
            for stored_name in self.memorized_locations
        )

    def get_memorized_location(self, name):
        """
        Return the room database ID for a memorized location, or None 
        if the character has no location with that name
        """
        name_key = name.casefold()
        for stored_name, room_id in self.memorized_locations.items():
            if stored_name.casefold() == name_key:
                return room_id
        return None

    def memorize_location(self, name, room_id):
        """
        Permanently memorize a room under the supplied player-defined name.
        Returns True on success, False if the name already exists or the 
        character is already at capacity
        """
        locations = self.memorized_locations

        if self.has_memorized_location(name):
            return False
        if len(locations) >= self.get_memorized_location_capacity():
            return False
        locations[name] = int(room_id)
        self.attributes.add("memorized_locations", locations)
        return True

    def forget_memorized_location(self, name):
        """
        Forget a memorized location by name.

        Name matrching is case-insensitive. Returns True if a location was removed, otherwise False.
        """
        locations = self.memorized_locations
        name_key = name.casefold()

        for stored_name in list(locations):
            if stored_name.casefold() == name_key:
                del locations[stored_name]
                self.attributes.add("memorized_locations", locations)
                return True
        return False

    # ==================================================================
    # Magick words - see world/magick_words.py and CmdStudy/CmdMagickWords
    # in commands/command.py
    # ==================================================================
    @property
    def known_magick_words(self):
        """Word ids (world/magick_words.py) this character has learned."""
        return list(self.attributes.get("known_magick_words", default=[]))

    @property
    def teaches_magick_words(self):
        """Whether other characters can 'study' this one as a teacher."""
        return bool(self.attributes.get("teaches_magick_words", default=False))

    @teaches_magick_words.setter
    def teaches_magick_words(self, value):
        self.attributes.add("teaches_magick_words", bool(value))

    def knows_magick_word(self, word_id):
        """Whether this character has already learned word_id (case-insensitive)."""
        canonical = magick_words_registry.canonical_word_id(word_id)
        if canonical is None:
            return False
        return canonical in self.attributes.get("known_magick_words", default=[])

    def understands_magick_word(self, word_id):
        """
        Whether this character's skill rank meets word_id's min_skill
        requirement - i.e. whether they're even capable of learning
        it, independent of whether they've actually learned it yet.
        False for an unrecognized word id.
        """
        word_data = magick_words_registry.get_word_data(word_id)
        if word_data is None:
            return False
        return self.get_skill(word_data["skill"]) >= word_data["min_skill"]

    def learn_magick_word(self, word_id):
        """
        Add a Magick word to this character's known vocabulary.
        Returns True if it was newly learned, False if word_id is
        unrecognized or already known. Does NOT check
        understands_magick_word()/min_skill itself - that gate (plus
        the learning roll) belongs to the caller (see CmdStudy), same
        split as memorize_location() not checking capacity itself.
        """
        canonical = magick_words_registry.canonical_word_id(word_id)
        if canonical is None:
            return False
        known = self.attributes.get("known_magick_words", default=[])
        if canonical in known:
            return False
        known.append(canonical)
        self.attributes.add("known_magick_words", known)
        return True

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
    # Immortal/staff (bamf messages, tier info - see CmdImm)
    # ==================================================================
    @property
    def bamf_in(self):
        return self.attributes.get("bamf_in", default=DEFAULT_BAMF_IN)

    @bamf_in.setter
    def bamf_in(self, value):
        self.attributes.add("bamf_in", value)

    @property
    def bamf_out(self):
        return self.attributes.get("bamf_out", default=DEFAULT_BAMF_OUT)

    @bamf_out.setter
    def bamf_out(self, value):
        self.attributes.add("bamf_out", value)

    @property
    def holylight(self):
        return bool(self.attributes.get("holylight", default=False))

    @holylight.setter
    def holylight(self, value):
        self.attributes.add("holylight", bool(value))

    def get_bamf_message(self, direction):
        """
        Returns the rendered (name-substituted) bamf-in or bamf-out
        message. `direction` is "in" or "out".
        """
        template = self.bamf_in if direction == "in" else self.bamf_out
        try:
            return template.format(name=self.get_display_name(None))
        except (KeyError, IndexError):
            # A malformed custom template (stray {something}) shouldn't
            # ever crash a teleport - fall back to the raw text.
            return template

    def announce_move_from(self, destination, msg=None, mapping=None, move_type="move", **kwargs):
        """
        Evennia calls this on an object right before it leaves its
        current location, as part of move_to(). Evennia's default
        teleport command (@tel/teleport - inherited automatically via
        default_cmds.CharacterCmdSet, no custom command needed here)
        tags its moves with move_type="teleport" specifically so
        typeclasses can hook this. When that's the case, and nothing
        upstream already forced a specific msg, show this character's
        bamf-out message to the room being left instead of Evennia's
        default departure text.

        NOTE: signature/behavior of announce_move_from() is part of
        Evennia's DefaultObject and can shift slightly between
        versions - if bamf messages stop firing after an Evennia
        upgrade, check this override against the installed version's
        source first.
        """
        if move_type == "teleport" and msg is None and self.location:
            self.location.msg_contents(
                self.get_bamf_message("out"), exclude=self, from_obj=self,
            )
            return
        super().announce_move_from(
            destination, msg=msg, mapping=mapping, move_type=move_type, **kwargs
        )

    def announce_move_to(self, source_location, msg=None, mapping=None, move_type="move", **kwargs):
        """
        Mirrors announce_move_from() above, but fires in the
        destination room right after arrival.
        """
        if move_type == "teleport" and msg is None and self.location:
            self.location.msg_contents(
                self.get_bamf_message("in"), exclude=self, from_obj=self,
            )
            return
        super().announce_move_to(
            source_location, msg=msg, mapping=mapping, move_type=move_type, **kwargs
        )

    def at_post_move(self, source_location, **kwargs):
        """
        Evennia calls this right after this character successfully
        arrives somewhere via move_to() - covers ordinary movement
        through an exit as well as teleports, since both end in the
        same "now standing in a new room" state. Separate from
        announce_move_from()/announce_move_to() above: those are
        about what OTHER people in the room see (bamf messages);
        this is about this character's own progression, and Evennia
        already calls it at exactly the right moment for that.

        Awards EXPLORATION_XP_REWARD once per room, ever, the first
        time this character sets foot in it. Revisiting doesn't pay
        out again - self.db.explored_rooms is the record of what's
        already been paid.

        Only Rooms count - moving into a container/inventory (a
        Character, an open chest, etc.) is technically a move_to()
        too, and shouldn't grant exploration XP. is_typeclass() is
        used here (rather than importing typeclasses.rooms.Room) to
        avoid a characters.py <-> rooms.py import between typeclass
        modules for one check.
        """
        super().at_post_move(source_location, **kwargs)

        destination = self.location
        if destination is None:
            return
        if not destination.is_typeclass("typeclasses.rooms.Room", exact=False):
            return

        room_id = destination.id
        explored = self.attributes.get("explored_rooms", default={})
        if room_id in explored:
            return

        explored[room_id] = True
        self.attributes.add("explored_rooms", explored)

        self.xp += EXPLORATION_XP_REWARD
        self.msg(
            f"|c(You have explored a new location. Gained a small amount of XP.)|n"
        )

    def highest_staff_permission(self):
        """
        Returns the highest staff permission tier (see
        world/immortal_data.PERMISSION_ORDER) this character holds,
        checking both the Character object's own permissions and
        those of the Account currently puppeting it (permissions are
        usually granted on the Account) - or None if neither has any
        tier listed there.
        """
        perms = set(self.permissions.all())
        if self.account:
            perms |= set(self.account.permissions.all())
        return immortal_data.highest_permission(perms)

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
