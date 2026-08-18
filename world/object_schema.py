"""
Object Schema

Central definitions used by the Eaetheria object browser and object editor.

The schema describes the fields that builders can see and manipulate.
It does NOT store the actual object data.

The actual values remain on Evennia objects, primarily through the
validated properties in typeclasses.items.Item.

This lets the builder discover what an object contains without having
to hard-code every field into every command.
"""

from world.skills import ALL_SKILLS
from world.sectors import ALL_SECTORS, DEFAULT_SECTOR
from typeclasses.items import (
    ITEM_TYPES,
    WEAPON_TYPES,
    EQUIP_STATS,
    EQUIP_SKILLS,
    VALID_EQUIP_SLOTS,
)


class FieldType:
    """Types of values understood by the object builder."""

    TEXT = "text"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    CHOICE = "choice"
    STAT_BONUSES = "stat_bonuses"
    FLAGS = "flags"


class ObjectField:
    """
    Describes one field available to the object builder.
    """

    def __init__(
        self,
        name,
        label,
        field_type,
        description="",
        choices=None,
        default=None,
        category="general",
    ):
        self.name = name
        self.label = label
        self.field_type = field_type
        self.description = description
        self.choices = choices or []
        self.default = default
        self.category = category

    def get_value(self, obj):
        """
        Read the current value from an Evennia object.

        We prefer the validated property on the object when one exists.
        If it doesn't, fall back to the Attribute database.
        """
        try:
            return getattr(obj, self.name)
        except AttributeError:
            return getattr(obj.db, self.name, self.default)


class ObjectSchema:
    """
    Describes the fields belonging to a particular object type.

    Schemas may inherit from another schema.
    """

    def __init__(self, name, label=None, parent=None):
        self.name = name
        self.label = label or name
        self.parent = parent
        self.fields = []

    def add_field(self, field):
        """Add a field to this schema."""
        self.fields.append(field)
        return field

    def get_fields(self):
        """Return inherited fields followed by local fields."""
        fields = []

        if self.parent:
            fields.extend(self.parent.get_fields())

        fields.extend(self.fields)

        return fields

    def get_field(self, name):
        """Return a field by its actual attribute name."""
        for field in self.get_fields():
            if field.name == name:
                return field

        return None

    def get_categories(self):
        """
        Return the categories represented by this schema.

        Categories retain the order in which they first appear.
        """
        categories = []

        for field in self.get_fields():
            if field.category not in categories:
                categories.append(field.category)

        return categories


# ==========================================================================
# Base Item Schema
# ==========================================================================

ITEM_SCHEMA = ObjectSchema(
    "item",
    "Item",
)


# --------------------------------------------------------------------------
# Identity
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "item_id",
        "Item ID",
        FieldType.TEXT,
        "Internal identifier used by the game and prototypes.",
        category="identity",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "unidentified_name",
        "Unidentified Name",
        FieldType.TEXT,
        "Name displayed before the item has been identified.",
        category="identity",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "identified",
        "Identified",
        FieldType.BOOLEAN,
        "Whether the item's true identity is currently known.",
        default=True,
        category="identification",
    )
)


# --------------------------------------------------------------------------
# Physical
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "weight",
        "Weight",
        FieldType.FLOAT,
        "The item's physical weight.",
        default=0.0,
        category="physical",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "stackable",
        "Stackable",
        FieldType.BOOLEAN,
        "Whether multiple copies of this item can stack together.",
        default=True,
        category="physical",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "size_matters",
        "Size Matters",
        FieldType.BOOLEAN,
        "Whether the user's size must match the item's size category.",
        default=True,
        category="physical",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "size_category",
        "Size Category",
        FieldType.CHOICE,
        "The physical size category of the item.",
        choices=[
            "TINY",
            "SMALL",
            "MEDIUM",
            "LARGE",
            "HUGE",
            "GARGANTUAN",
        ],
        default="MEDIUM",
        category="physical",
    )
)


# --------------------------------------------------------------------------
# Identification
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "knowledge_difficulty",
        "Knowledge Difficulty",
        FieldType.INTEGER,
        "Difficulty for identifying the item through general knowledge.",
        default=3,
        category="identification",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "arcana_difficulty",
        "Arcana Difficulty",
        FieldType.INTEGER,
        "Difficulty for identifying magical properties through Arcana.",
        default=3,
        category="identification",
    )
)


# --------------------------------------------------------------------------
# Classification
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "item_type",
        "Item Type",
        FieldType.CHOICE,
        "Broad classification of the item.",
        choices=ITEM_TYPES,
        default="MISC",
        category="classification",
    )
)


# --------------------------------------------------------------------------
# Equipment
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "wear_slot",
        "Wear Slot",
        FieldType.CHOICE,
        "Body slot where the item can be equipped.",
        choices=VALID_EQUIP_SLOTS,
        default=None,
        category="equipment",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "equip_stat",
        "Equip Attribute",
        FieldType.CHOICE,
        "Character attribute associated with using the item.",
        choices=EQUIP_STATS,
        default="agility",
        category="equipment",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "equip_skill",
        "Equip Skill",
        FieldType.CHOICE,
        "Skill associated with using the item.",
        choices=EQUIP_SKILLS,
        default=None,
        category="equipment",
    )
)


# --------------------------------------------------------------------------
# Bonuses
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "stat_bonuses",
        "Stat/Skill Bonuses",
        FieldType.STAT_BONUSES,
        (
            "Bonuses granted by this item. Keys are attribute or skill "
            "names and values are flat integer bonuses."
        ),
        choices=ALL_SKILLS + EQUIP_STATS,
        default={},
        category="bonuses",
    )
)


# --------------------------------------------------------------------------
# Magick
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "is_magick",
        "Magick Item",
        FieldType.BOOLEAN,
        "Whether this item is magical.",
        default=False,
        category="magick",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "is_enchantable",
        "Enchantable",
        FieldType.BOOLEAN,
        "Whether this item can receive enchantments.",
        default=False,
        category="magick",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "enchanting_mana_limit",
        "Enchanting Mana Limit",
        FieldType.INTEGER,
        "Maximum mana available for enchantments.",
        default=0,
        category="magick",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "magick_words",
        "Magick Words",
        FieldType.TEXT,
        (
            "Word ids (world/magick_words.py) this object teaches via "
            "'study'. Only meaningful when is_magick is set. Edit via "
            "@objedit's 'magick words' choice, not directly - it's a "
            "list, not a single text field."
        ),
        default=[],
        category="magick",
    )
)


# --------------------------------------------------------------------------
# Tools
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "is_thief_tools",
        "Thief Tools",
        FieldType.BOOLEAN,
        "Whether this item functions as thief's tools.",
        default=False,
        category="tools",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "thief_tools_bonus_dice",
        "Thief Tools Bonus Dice",
        FieldType.INTEGER,
        "Bonus dice granted when using these thief tools.",
        default=2,
        category="tools",
    )
)


# --------------------------------------------------------------------------
# Light
# --------------------------------------------------------------------------

ITEM_SCHEMA.add_field(
    ObjectField(
        "light_radius_tiles",
        "Light Radius",
        FieldType.FLOAT,
        "Radius of light emitted by the item in tiles.",
        default=0.0,
        category="light",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "light_energy",
        "Light Energy",
        FieldType.FLOAT,
        "Intensity of the emitted light.",
        default=1.0,
        category="light",
    )
)

ITEM_SCHEMA.add_field(
    ObjectField(
        "light_color",
        "Light Color",
        FieldType.TEXT,
        "RGB light color stored by the item.",
        default=(1.0, 0.85, 0.6),
        category="light",
    )
)


# ==========================================================================
# Weapon Schema
# ==========================================================================

WEAPON_SCHEMA = ObjectSchema(
    "weapon",
    "Weapon",
    parent=ITEM_SCHEMA,
)

WEAPON_SCHEMA.add_field(
    ObjectField(
        "weapon_type",
        "Weapon Type",
        FieldType.CHOICE,
        "Physical/fighting type of the weapon.",
        choices=WEAPON_TYPES,
        default="NONE",
        category="combat",
    )
)

WEAPON_SCHEMA.add_field(
    ObjectField(
        "stamina_cost",
        "Stamina Cost",
        FieldType.INTEGER,
        "Stamina consumed when this weapon is used.",
        default=0,
        category="combat",
    )
)


# ==========================================================================
# Armor Schema
# ==========================================================================

ARMOR_SCHEMA = ObjectSchema(
    "armor",
    "Armor",
    parent=ITEM_SCHEMA,
)

# No armor-specific fields are defined yet.
#
# We'll add them when the actual Eaetheria armor mechanics are established.
# We don't want the builder inventing rules that the game doesn't use.


# ==========================================================================
# Altar Schema
# ==========================================================================
#
# No altar-specific fields are defined yet - an Altar dropped in a
# room is what CmdCraftSpell checks for (isinstance, not a field), so
# there's nothing here to expose yet beyond the base Item fields.
# Same "don't invent unused fields" reasoning as ARMOR_SCHEMA above.

ALTAR_SCHEMA = ObjectSchema(
    "altar",
    "Altar",
    parent=ITEM_SCHEMA,
)


# ==========================================================================
# Room Schema
# ==========================================================================
#
# key/desc are the two fields every Evennia Room already has.
# room_flags/sector are classification/metadata only for now (see
# world/room_flags.py and world/sectors.py) - nothing in the engine
# yet reads them to actually change behavior (no combat, NPCs, or
# magick system exists to consult PEACEFUL/NOMOB/NOMAGIC; no movement
# system exists to consult sector). Same reasoning as the "no
# armor-specific fields yet" note on ARMOR_SCHEMA above: we don't want
# the builder inventing rules the game doesn't use - these are here so
# builders can start tagging rooms now, with enforcement to follow
# once the systems that would enforce them exist.

ROOM_SCHEMA = ObjectSchema(
    "room",
    "Room",
)

ROOM_SCHEMA.add_field(
    ObjectField(
        "key",
        "Name",
        FieldType.TEXT,
        "The room's display name.",
        category="general",
    )
)

ROOM_SCHEMA.add_field(
    ObjectField(
        "desc",
        "Description",
        FieldType.TEXT,
        "What `look` shows for the room.",
        category="general",
    )
)

ROOM_SCHEMA.add_field(
    ObjectField(
        "sector",
        "Sector",
        FieldType.CHOICE,
        "Terrain classification for this room.",
        choices=ALL_SECTORS,
        default=DEFAULT_SECTOR,
        category="terrain",
    )
)

ROOM_SCHEMA.add_field(
    ObjectField(
        "flags",
        "Flags",
        FieldType.FLAGS,
        "Currently-set ROOM_* flags - see 'help room flags'.",
        default=[],
        category="flags",
    )
)

ROOM_SCHEMA.add_field(
    ObjectField(
        "is_magick_location",
        "Magick Location",
        FieldType.BOOLEAN,
        "Whether this room itself teaches Magick words via 'study here'.",
        default=False,
        category="magick",
    )
)

ROOM_SCHEMA.add_field(
    ObjectField(
        "magick_words",
        "Magick Words",
        FieldType.TEXT,
        (
            "Word ids (world/magick_words.py) this room teaches via "
            "'study here'. Only meaningful when is_magick_location is "
            "set. Edit via @redit's 'magick words' choice, not "
            "directly - it's a list, not a single text field."
        ),
        default=[],
        category="magick",
    )
)


# ==========================================================================
# Key Schema
# ==========================================================================
#
# Key (typeclasses.items.Key) is NOT an Item subclass - it's a plain
# Object with its own single validated field (key_id, see
# typeclasses/items.py). Its own top-level schema, same reasoning
# as Room: keep it to the fields that actually exist.

KEY_SCHEMA = ObjectSchema(
    "key",
    "Key",
)

KEY_SCHEMA.add_field(
    ObjectField(
        "key_id",
        "Key ID",
        FieldType.TEXT,
        "Tag that must match a LockableExit's key_id for this key to unlock it.",
        default="",
        category="general",
    )
)


# ==========================================================================
# Registry
# ==========================================================================

OBJECT_SCHEMAS = {
    "item": ITEM_SCHEMA,
    "weapon": WEAPON_SCHEMA,
    "armor": ARMOR_SCHEMA,
    "altar": ALTAR_SCHEMA,
    "room": ROOM_SCHEMA,
    "key": KEY_SCHEMA,
}


def _build_objedit_types():
    """
    Lazily-built {name: typeclass} registry for @objedit's "1. Type"
    choice (Object.editor_type in typeclasses/objects.py). A function
    rather than a module-level dict so it can do the same local import
    get_schema() below already does, keeping this file's only
    typeclasses.items dependency at call-time rather than load-time.
    """

    from typeclasses.items import Item, Weapon, Armor, Altar, Key

    return {
        "item": Item,
        "weapon": Weapon,
        "armor": Armor,
        "altar": Altar,
        "key": Key,
    }


OBJEDIT_TYPES = _build_objedit_types()


def get_schema(obj):
    """
    Determine the appropriate schema for an actual Evennia object.
    """

    from typeclasses.items import Item, Weapon, Armor, Altar, Key
    from typeclasses.rooms import Room

    if isinstance(obj, Weapon):
        return WEAPON_SCHEMA

    if isinstance(obj, Armor):
        return ARMOR_SCHEMA

    if isinstance(obj, Altar):
        return ALTAR_SCHEMA

    if isinstance(obj, Item):
        return ITEM_SCHEMA

    if isinstance(obj, Room):
        return ROOM_SCHEMA

    if isinstance(obj, Key):
        return KEY_SCHEMA

    return None