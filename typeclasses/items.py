"""
Items

Physical items with in-game behavior beyond a plain Object. Includes
the Key type (unlocks LockableExits, see typeclasses/exits.py) and the
Item type (the Evennia parallel to the Godot `Item` resource -
resources/items/itemdata.gd - for anything wearable/wieldable).
"""

from typeclasses.objects import Object
from world import body_parts as body_parts_registry
from world.races import SIZE_MEDIUM
from world.skills import canonical_skill_name


class Key(Object):
    """
    A key that can unlock any LockableExit whose key_id matches this
    key's key_id. Matching is by value, not by specific object
    identity - so multiple copies of "the same key" (e.g. spawned
    from a prototype) all work on the same door(s). An empty key_id
    ("") never matches anything, including a door with an empty
    key_id - both sides must set a real, non-empty matching value.

    Keys are reusable: using one to unlock a door does not consume
    or destroy it.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.key_id = ""

    @property
    def key_id(self):
        return self.db.key_id

    @key_id.setter
    def key_id(self, value):
        self.db.key_id = str(value).strip()

    def matches(self, exit_obj):
        """Whether this key can unlock the given LockableExit."""
        my_id = (self.key_id or "").strip()
        door_id = (getattr(exit_obj, "key_id", "") or "").strip()
        return bool(my_id) and my_id == door_id


# ==========================================================================
# Item - the Evennia parallel to Godot's Item resource (itemdata.gd)
# ==========================================================================
#
# Ported field-for-field where it makes sense for a text MUD; a few
# notes on the port:
#
# - icon / worn_sprite_sheet (Texture2D) are Godot-only visual fields
#   and have no Evennia equivalent - dropped.
# - display_name / description map onto Evennia's own `key` and
#   `db.desc` (what `look` already shows) instead of separate custom
#   Attributes, so items behave like every other Evennia Object.
# - equip_slot: Godot's EquipSlot enum only had 9 values (NONE, ARMOR,
#   WEAPON, RING, NECKLACE, BELT, OFFHAND, HEAD, FEET) - far fewer
#   than the ~20 slots world/body_parts.py now defines (ears, neck,
#   waist, shoulders, left/right wrist, left/right ring, tail, wings,
#   horns, shell, floaty, ...). Rather than keep the old 9-value enum,
#   items here store `wear_slot` as one of body_parts.SLOT_DISPLAY_ORDER's
#   string ids directly - see GODOT_EQUIP_SLOT_MAP below for how the
#   old Godot values map onto the new slot ids if you're porting
#   specific item instances over.
# - size_category reuses world/races.py's SIZE_* constants (the same
#   ones player_race.size_category uses) rather than a separate enum,
#   matching the comment in itemdata.gd that these are meant to be
#   compared directly.
# - equip_stat/equip_skill are stored as the actual attribute/skill
#   name strings (e.g. "agility", "MartialArts") instead of a separate
#   enum + name-lookup table, since world/characters.py and
#   world/skills.py already work in those terms everywhere else.

ITEM_TYPE_WEAPON = "WEAPON"
ITEM_TYPE_ARMOR = "ARMOR"
ITEM_TYPE_FOOD = "FOOD"
ITEM_TYPE_POTION = "POTION"
ITEM_TYPE_MATERIAL = "MATERIAL"
ITEM_TYPE_MISC = "MISC"
ITEM_TYPES = [
    ITEM_TYPE_WEAPON, ITEM_TYPE_ARMOR, ITEM_TYPE_FOOD,
    ITEM_TYPE_POTION, ITEM_TYPE_MATERIAL, ITEM_TYPE_MISC,
]

WEAPON_TYPE_NONE = "NONE"
WEAPON_TYPE_AXE = "AXE"
WEAPON_TYPE_BOW = "BOW"
WEAPON_TYPE_CHAINED = "CHAINED"
WEAPON_TYPE_CROSSBOW = "CROSSBOW"
WEAPON_TYPE_BLUNT = "BLUNT"
WEAPON_TYPE_SLASHING = "SLASHING"
WEAPON_TYPE_PIERCING = "PIERCING"
WEAPON_TYPE_UNARMED = "UNARMED"
WEAPON_TYPES = [
    WEAPON_TYPE_NONE, WEAPON_TYPE_AXE, WEAPON_TYPE_BOW, WEAPON_TYPE_CHAINED,
    WEAPON_TYPE_CROSSBOW, WEAPON_TYPE_BLUNT, WEAPON_TYPE_SLASHING,
    WEAPON_TYPE_PIERCING, WEAPON_TYPE_UNARMED,
]

# Godot's EquipStat enum (MIGHT/AGILITY/ENDURANCE) as the actual
# attribute name strings Character already uses everywhere else.
EQUIP_STATS = ["might", "agility", "endurance"]

# Godot's EquipSkill enum values, as the actual canonical skill name
# strings from world/skills.py.
EQUIP_SKILLS = [
    "Archery", "DualWield", "GreatWeapon", "MartialArts", "OneHand",
    "ThrownWeapon", "LightArmor", "MediumArmor", "HeavyArmor",
]

# Every valid wear_slot id, pulled straight from the body_parts
# registry so this file never drifts out of sync with it.
VALID_EQUIP_SLOTS = list(body_parts_registry.SLOT_DISPLAY_ORDER)

# How Godot's old, coarser 9-value EquipSlot enum maps onto the new
# slot ids, for porting specific item instances over from Godot data.
# None means "not equippable" (Godot's EquipSlot.NONE).
GODOT_EQUIP_SLOT_MAP = {
    "NONE": None,
    "FLOATING": "floaty",
    "ARMOR": "torso",
    "WEAPON": "wielded",
    "RING": "left_ring",
    "NECKLACE": "neck",
    "BELT": "waist",
    "OFFHAND": "offhand",
    "HEAD": "head",
    "FEET": "feet",
    "EARS": "ears",
    "NECK": "neck",
    "WAIST": "waist",
    "SHOULDERS": "shoulders",
    "LEFT_WRIST": "left_wrist",
    "RIGHT_WRIST": "right_wrist",
    "LEFT_RING": "left_ring",
    "RIGHT_RING": "right_ring",
    "TAIL": "tail",
    "WINGS": "wings",
    "HORNS": "horns",
    "SHELL": "shell",
}

DEFAULT_LIGHT_COLOR = (1.0, 0.85, 0.6)  # warm torchlight, matches the Godot default


def wear_slot_from_godot(godot_equip_slot):
    """Translate an old Godot EquipSlot enum name (e.g. 'ARMOR') to a wear_slot id."""
    return GODOT_EQUIP_SLOT_MAP.get(godot_equip_slot)


_TRUTHY_STRINGS = ("true", "yes", "y", "on", "1")
_FALSY_STRINGS = ("false", "no", "n", "off", "0")


def _coerce_bool(value, current):
    """Best-effort bool parse (True/False/yes/no/on/off/1/0); keeps `current` on a miss."""
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUTHY_STRINGS:
        return True
    if text in _FALSY_STRINGS:
        return False
    return current


def _resolve_stat_or_skill_name(text):
    """
    Case-insensitively resolve `text` to a canonical stat_bonuses key -
    either one of EQUIP_STATS (might/agility/endurance) or a real
    skill name from world.skills.ALL_SKILLS. Returns None if it
    matches neither, same "leave it alone on a miss" convention as
    the rest of this module's setters.
    """
    text = (text or "").strip()
    if not text:
        return None
    for stat in EQUIP_STATS:
        if text.lower() == stat.lower():
            return stat
    return canonical_skill_name(text)


class Item(Object):
    """
    Base typeclass for all carryable/wearable items - the Evennia
    equivalent of the Godot `Item` Resource. Individual items are
    normally built as prototypes (see world/prototypes.py) rather
    than subclassed, the same way Godot authors individual items as
    .tres instances of this one script rather than separate scripts.
    """

    def at_object_creation(self):
        super().at_object_creation()

        # ===== Identity =====
        self.db.item_id = ""
        self.db.unidentified_name = ""
        self.db.identified = True  # set False on an item that needs identifying
        # self.key / self.db.desc cover display_name / description -
        # no separate Attributes needed for those.

        # ===== Physical =====
        self.db.weight = 0.0
        self.db.stackable = True
        # See the "size_matters" comment in itemdata.gd: a weapon/armor
        # piece can only be equipped by a wielder of the SAME
        # size_category unless the wielder's race sets
        # ignores_size_restrictions (currently just The Lost).
        self.db.size_matters = True
        self.db.size_category = SIZE_MEDIUM

        # ===== Identification =====
        self.db.knowledge_difficulty = 3
        self.db.arcana_difficulty = 3

        # ===== Classification =====
        self.db.item_type = ITEM_TYPE_MISC

        # ===== Equipment info =====
        self.db.wear_slot = None  # one of VALID_EQUIP_SLOTS, or None = not equippable
        self.db.weapon_type = WEAPON_TYPE_NONE
        self.db.stamina_cost = 0  # 0/unset -> caller falls back to a default attack cost
        self.db.equip_stat = "agility"  # one of EQUIP_STATS, or None
        self.db.equip_skill = None  # one of EQUIP_SKILLS, or None
        self.db.stat_bonuses = {}  # attribute/skill name -> flat int bonus while worn

        # ===== Magick =====
        self.db.is_magick = False
        self.db.is_enchantable = False
        self.db.enchanting_mana_limit = 0

        # ===== Tool info =====
        self.db.is_thief_tools = False
        self.db.thief_tools_bonus_dice = 2

        # ===== Light source =====
        self.db.light_radius_tiles = 0.0  # 0 = doesn't emit light
        self.db.light_energy = 1.0
        self.db.light_color = DEFAULT_LIGHT_COLOR

    # ==================================================================
    # Helpers
    # ==================================================================
    def is_equippable(self):
        return self.db.wear_slot is not None

    def set_wear_slot(self, slot_id):
        """Validated setter - raises ValueError on an unknown slot id."""
        if slot_id is not None and slot_id not in VALID_EQUIP_SLOTS:
            raise ValueError(
                f"'{slot_id}' isn't a valid equip slot. Valid slots: {VALID_EQUIP_SLOTS}"
            )
        self.db.wear_slot = slot_id

    # ------------------------------------------------------------
    # Validated properties (menu-safe read/write surface)
    #
    # Same pattern as typeclasses.exits.LockableExit: raw storage
    # stays on .db exactly as at_object_creation sets it up, but each
    # field also gets a plain Python property of the same name that
    # parses/clamps/validates on write and silently leaves the value
    # unchanged on bad input rather than corrupting .db or raising
    # into a menu/command. world/building_menus.ItemBuildingMenu (and
    # its Weapon/Armor subclasses) bind to these via attr=, not to
    # .db directly.
    # ------------------------------------------------------------
    def _choice_property(name, valid_values, allow_none=False):
        """Build a (getter, setter) pair for a string field restricted to a fixed set."""

        def getter(self):
            return getattr(self.db, name)

        def setter(self, value):
            if value is None and allow_none:
                setattr(self.db, name, None)
                return
            text = str(value).strip()
            if allow_none and text.lower() in ("none", "-", ""):
                setattr(self.db, name, None)
                return
            # allow case-insensitive match against the canonical values
            for candidate in valid_values:
                if text.lower() == str(candidate).lower():
                    setattr(self.db, name, candidate)
                    return
            # unrecognized value: leave unchanged

        return property(getter, setter)

    def _bool_property(name):
        def getter(self):
            return bool(getattr(self.db, name))

        def setter(self, value):
            setattr(self.db, name, _coerce_bool(value, getattr(self.db, name)))

        return property(getter, setter)

    def _int_property(name, minimum=0):
        def getter(self):
            return getattr(self.db, name)

        def setter(self, value):
            try:
                parsed = int(str(value).strip())
            except (TypeError, ValueError):
                return
            setattr(self.db, name, max(minimum, parsed))

        return property(getter, setter)

    def _float_property(name, minimum=0.0):
        def getter(self):
            return getattr(self.db, name)

        def setter(self, value):
            try:
                parsed = float(str(value).strip())
            except (TypeError, ValueError):
                return
            setattr(self.db, name, max(minimum, parsed))

        return property(getter, setter)

    def _text_property(name):
        def getter(self):
            return getattr(self.db, name)

        def setter(self, value):
            setattr(self.db, name, str(value).strip())

        return property(getter, setter)

    # --- Identity ---
    item_id = _text_property("item_id")
    unidentified_name = _text_property("unidentified_name")
    identified = _bool_property("identified")

    # --- Physical ---
    weight = _float_property("weight")
    stackable = _bool_property("stackable")
    size_matters = _bool_property("size_matters")
    size_category = _choice_property(
        "size_category",
        ["TINY", "SMALL", "MEDIUM", "LARGE", "HUGE", "GARGANTUAN"],
    )

    # --- Identification ---
    knowledge_difficulty = _int_property("knowledge_difficulty")
    arcana_difficulty = _int_property("arcana_difficulty")

    # --- Classification ---
    item_type = _choice_property("item_type", ITEM_TYPES)

    # --- Equipment ---
    @property
    def wear_slot(self):
        return self.db.wear_slot

    @wear_slot.setter
    def wear_slot(self, value):
        text = str(value).strip() if value is not None else None
        if text and text.lower() in ("none", "-", ""):
            text = None
        try:
            self.set_wear_slot(text)
        except ValueError:
            pass  # unrecognized slot id: leave unchanged

    weapon_type = _choice_property("weapon_type", WEAPON_TYPES)
    stamina_cost = _int_property("stamina_cost")
    equip_stat = _choice_property("equip_stat", EQUIP_STATS, allow_none=True)
    equip_skill = _choice_property("equip_skill", EQUIP_SKILLS, allow_none=True)

    def add_stat_bonus(self, stat_name, amount):
        """Add/overwrite one entry in stat_bonuses without touching the rest."""
        try:
            amount = int(amount)
        except (TypeError, ValueError):
            return
        bonuses = dict(self.db.stat_bonuses or {})
        bonuses[stat_name] = amount
        self.db.stat_bonuses = bonuses

    def remove_stat_bonus(self, stat_name):
        bonuses = dict(self.db.stat_bonuses or {})
        bonuses.pop(stat_name, None)
        self.db.stat_bonuses = bonuses

    @property
    def stat_bonuses_command(self):
        """
        Menu-facing view of stat_bonuses: a formatted summary of the
        current dict plus the syntax used to edit it one entry at a
        time. world.building_menus.ItemBuildingMenu's "bonuses"
        choice binds to this via attr= - since it's a property, the
        choice re-renders live (fresh summary) every time the menu
        redisplays it, the same way every other attr= choice in that
        menu does.
        """
        bonuses = self.db.stat_bonuses or {}
        if not bonuses:
            body = "  (none set)"
        else:
            body = "\n".join(
                f"  {name}: {amount:+d}" for name, amount in sorted(bonuses.items())
            )
        return (
            f"Current bonuses:\n{body}\n\n"
            "Type '<name> <amount>' to add or update a bonus (e.g. "
            "'OneHand 2'), or 'remove <name>' to delete one (e.g. "
            "'remove OneHand'). <name> matches a skill or an attribute "
            "(might/agility/endurance) case-insensitively."
        )

    @stat_bonuses_command.setter
    def stat_bonuses_command(self, value):
        text = str(value).strip()
        if not text:
            return
        parts = text.split()
        if parts[0].lower() == "remove" and len(parts) >= 2:
            name = _resolve_stat_or_skill_name(" ".join(parts[1:]))
            if name is not None:
                self.remove_stat_bonus(name)
            return
        if len(parts) >= 2:
            *name_parts, amount_text = parts
            name = _resolve_stat_or_skill_name(" ".join(name_parts))
            if name is None:
                return  # unrecognized skill/attribute name: leave unchanged
            try:
                amount = int(amount_text)
            except ValueError:
                return
            self.add_stat_bonus(name, amount)
        # anything else (a single unrecognized word, etc.) is silently
        # ignored - same convention as the other validated setters above.

    # --- Magick ---
    is_magick = _bool_property("is_magick")
    is_enchantable = _bool_property("is_enchantable")
    enchanting_mana_limit = _int_property("enchanting_mana_limit")

    # --- Tool info ---
    is_thief_tools = _bool_property("is_thief_tools")
    thief_tools_bonus_dice = _int_property("thief_tools_bonus_dice")

    # --- Light source ---
    light_radius_tiles = _float_property("light_radius_tiles")
    light_energy = _float_property("light_energy")

    del _choice_property, _bool_property, _int_property, _float_property, _text_property

    def get_display_name(self, looker=None, **kwargs):
        """
        Shows unidentified_name instead of the true name until
        identified.

        Lookers with holylight on see the dbref appended either way
        (e.g. "sword(#123)"), via ObjectParent.get_extra_display_name_
        info (typeclasses/objects.py), which gates on the looker's
        holylight toggle - see CmdHolylight in commands/command.py.
        The identified branch below gets this for free via
        super().get_display_name(); the unidentified branch has to
        add it explicitly since it returns early without calling
        super() at all.
        """
        if not self.db.identified and self.db.unidentified_name:
            return (
                self.db.unidentified_name
                + self.get_extra_display_name_info(looker, **kwargs)
            )
        return super().get_display_name(looker, **kwargs)


class Weapon(Item):
    """Convenience subtype - just sets item_type/wear_slot defaults for weapons."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.item_type = ITEM_TYPE_WEAPON
        self.db.wear_slot = "wielded"


class Armor(Item):
    """Convenience subtype - just sets item_type defaults for armor."""

    def at_object_creation(self):
        super().at_object_creation()
        self.db.item_type = ITEM_TYPE_ARMOR
        self.db.wear_slot = "torso"
