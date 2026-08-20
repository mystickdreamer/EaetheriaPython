"""
Object Builder

Generalized OasisOLC-style browsing/editing across every typeclass
world/object_schema.py knows a schema for.

Commands:

    @olist [<category>] [<search>]   - schema-driven table of matches
    @olist #<dbref>                  - full field dump of one object

    @ocreate <name>                  - create a new Item (does not open the editor)
    @oedit #<dbref>                  - edit an existing object

    @redit <name>                    - create a new Room and edit it
    @redit #<dbref>                 - edit an existing Room

@oedit deliberately does NOT edit Rooms - use @redit for those.

Object creation and object editing are two separate commands/steps -
@oedit takes a DBREF only and never creates anything, so it can never
guess wrong when multiple objects share a name (previously @objedit
<name> meant "create"; that's gone, replaced by @ocreate).

Examples:

    @ocreate sword
        -> creates a new Item named "sword", reports its DBREF

    @oedit #123
        -> opens the editor for existing object #123

The typeclass of a newly-created object starts as Item. Change it from
inside the editor with choice "1" (Typeclass) - see world/oedit_menu.py
(a fresh EvMenu; superseded world/building_menus.py's building_menu-
contrib-based _ObjEditMenu family, which is no longer used by any
command here).
"""

from evennia.objects.models import ObjectDB
from evennia.utils.create import create_object

from world.object_schema import get_schema

from world.building_menus import RoomBuildingMenu

from typeclasses.items import Item, Weapon, Armor, Altar, ThievesTool, Key
from typeclasses.rooms import Room

from commands.command import Command


# --------------------------------------------------------------------
# Category keywords accepted by @olist.
#
# Each category maps to:
#
#     (typeclass path prefix, Python class)
#
# The isinstance() check keeps the path-prefix search from returning
# unrelated typeclasses that happen to live in the same module.
# --------------------------------------------------------------------

CATEGORY_MAP = {
    "item": ("typeclasses.items", Item),
    "items": ("typeclasses.items", Item),

    "weapon": ("typeclasses.items", Weapon),
    "weapons": ("typeclasses.items", Weapon),

    "armor": ("typeclasses.items", Armor),
    "armors": ("typeclasses.items", Armor),

    "altar": ("typeclasses.items", Altar),
    "altars": ("typeclasses.items", Altar),

    "thievestool": ("typeclasses.items", ThievesTool),
    "thievestools": ("typeclasses.items", ThievesTool),
    "thief tools": ("typeclasses.items", ThievesTool),

    "room": ("typeclasses.rooms", Room),
    "rooms": ("typeclasses.rooms", Room),

    "key": ("typeclasses.items", Key),
    "keys": ("typeclasses.items", Key),
}


def _render_detail(obj, looker):
    """
    Full schema-driven field dump for one object.

    This is shared by @olist #<dbref> and @oedit so the two views
    stay synchronized with the schema definitions.
    """

    schema = get_schema(obj)

    if schema is None:
        return (
            f"{obj.get_display_name(looker)} ({obj.dbref}) has no object "
            f"schema registered for its typeclass "
            f"({type(obj).__module__}.{type(obj).__name__})."
        )

    lines = [
        f"|w{obj.get_display_name(looker)}|n "
        f"({obj.dbref}) - {schema.label}"
    ]

    current_category = None

    for field in schema.get_fields():
        if field.category != current_category:
            current_category = field.category
            lines.append(f"\n|c{current_category.title()}|n")

        lines.append(
            f"  {field.label}: {field.get_value(obj)}"
        )

    return "\n".join(lines)


def _render_table(objects, looker):
    """
    Summary table for @olist's multi-result view.
    """

    lines = [
        f"{'Dbref':<8}{'Name':<30}{'Typeclass':<20}"
    ]

    lines.append("-" * 70)

    for obj in objects:
        typeclass_name = (
            f"{type(obj).__module__}.{type(obj).__name__}"
        )

        lines.append(
            f"{obj.dbref:<8}"
            f"{obj.get_display_name(looker):<30}"
            f"{typeclass_name}"
        )

    lines.append(
        f"\n{len(objects)} match(es). "
        f"Use @olist #<dbref> or @oedit #<dbref> for full detail."
    )

    return "\n".join(lines)


# ====================================================================
# @olist
# ====================================================================

class CmdOList(Command):
    """
    Browse objects with a schema-driven table.

    Usage:

        @olist
        @olist <category>
        @olist <category> <search>
        @olist <search>
        @olist #<dbref>

    Categories:

        item
        weapon
        armor
        altar
        room
        key

    Plurals are accepted.

    With no category, defaults to items.

    A bare non-category argument is treated as a name search within
    the default Item category.

    @olist #<dbref> shows the full schema-driven field dump for one
    object.

    Examples:

        @olist
            -> table of every Item

        @olist weapons
            -> just Weapons

        @olist rooms tavern
            -> Rooms with "tavern" in their name

        @olist keys
            -> every Key

        @olist sword
            -> Items with "sword" in their name

        @olist #42
            -> full detail dump of #42
    """

    key = "@olist"
    aliases = ["olist"]

    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller
        args = self.args.strip() if self.args else ""

        # ------------------------------------------------------------
        # DBREF lookup.
        #
        # @olist #42
        # ------------------------------------------------------------

        if args.startswith("#"):
            dbref_token = args.split()[0]

            obj = caller.search(
                dbref_token,
                global_search=True,
            )

            if not obj:
                return

            caller.msg(
                _render_detail(obj, caller)
            )

            return

        # ------------------------------------------------------------
        # Category/search parsing.
        # ------------------------------------------------------------

        parts = (
            args.split(None, 1)
            if args
            else []
        )

        category = "item"
        term = ""

        if parts and parts[0].lower() in CATEGORY_MAP:
            category = parts[0].lower()
            term = parts[1] if len(parts) > 1 else ""
        else:
            term = args

        path_prefix, base_cls = CATEGORY_MAP[category]

        # ------------------------------------------------------------
        # Find objects belonging to the requested category.
        # ------------------------------------------------------------

        matches = [
            obj
            for obj in ObjectDB.objects.filter(
                db_typeclass_path__startswith=path_prefix
            )
            if isinstance(obj, base_cls)
        ]

        # ------------------------------------------------------------
        # Optional name search.
        # ------------------------------------------------------------

        if term:
            term_lower = term.lower()

            matches = [
                obj
                for obj in matches
                if term_lower in obj.key.lower()
            ]

        if not matches:
            caller.msg(
                "No matching objects found."
            )

            return

        caller.msg(
            _render_table(matches, caller)
        )


# ====================================================================
# @ocreate
# ====================================================================

class CmdOCreate(Command):
    """
    Create a new Item, ready for @oedit.

    Usage:

        @ocreate <name>

    Creates a bare Item (typeclasses.items.Item) in your inventory and
    reports its DBREF. It does NOT open the editor - follow up with:

        @oedit #<dbref>

    Change the object's typeclass (Weapon, Armor, Altar, Key) from
    inside @oedit itself, once it exists - see @oedit's own help.

    This replaces the old @objedit <name> creation path. Object
    creation and object editing are now two separate steps rather than
    one command doing both, on request.
    """

    key = "@ocreate"
    aliases = ["ocreate"]

    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller
        name = self.args.strip() if self.args else ""

        if not name:
            caller.msg("Usage: @ocreate <name>")
            return

        try:
            obj = create_object(
                typeclass=Item,
                key=name,
                location=caller,
            )

        except Exception as err:
            caller.msg(f"|rFailed to create object: {err}|n")

            from evennia.utils import logger
            logger.log_trace()

            return

        caller.msg(
            f"|gCreated new Item|n |w{obj.key}|n ({obj.dbref}). "
            f"Use |w@oedit {obj.dbref}|n to edit it."
        )


# ====================================================================
# @oedit
# ====================================================================

class CmdOEdit(Command):
    """
    Edit an existing Item/Weapon/Armor/Altar/Key through a menu-driven
    editor.

    Usage:

        @oedit #<dbref>

    @oedit is edit-only and always takes a DBREF - it deliberately does
    NOT create objects and does NOT search by name, so it can never
    guess wrong when several objects share a name. To create a new
    object first, use:

        @ocreate <name>

    then edit the DBREF it reports:

        @oedit #123

    Rooms are deliberately excluded from @oedit - use @redit for those.

    The editor works on a draft copy of the object: nothing is written
    back until you choose "S" to save, and "Q" will warn you first if
    you have unsaved changes. Typeclass can be changed from inside the
    editor ("1. Typeclass") without needing to reopen it.
    """

    key = "@oedit"
    aliases = ["oedit", "objedit"]

    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller
        target_str = self.args.strip() if self.args else ""

        if not target_str:
            caller.msg("Usage: @oedit #<dbref>")
            return

        if not target_str.startswith("#"):
            caller.msg(
                "|y@oedit only takes a DBREF now.|n\n"
                "Use |w@ocreate <name>|n to create a new object, "
                "then |w@oedit #<dbref>|n on the DBREF it reports."
            )
            return

        dbref_token = target_str.split()[0]
        obj = caller.search(dbref_token, global_search=True)

        if not obj:
            return

        # ------------------------------------------------------------
        # Rooms are intentionally NOT editable through @oedit.
        #
        # This gives us a clean separation:
        #
        #     @oedit  -> objects
        #     @redit  -> rooms
        # ------------------------------------------------------------

        if isinstance(obj, Room):
            caller.msg(
                "|yRooms cannot be edited with @oedit.|n "
                "Use @redit for rooms."
            )
            return

        if get_schema(obj) is None:
            caller.msg(
                f"{obj.get_display_name(caller)} "
                f"isn't currently an editable object type."
            )
            return

        # ------------------------------------------------------------
        # Show the schema-driven detail view before opening the menu.
        # ------------------------------------------------------------

        caller.msg(_render_detail(obj, caller))

        # ------------------------------------------------------------
        # Open the oedit menu (world/oedit_menu.py - a fresh EvMenu,
        # not the building_menu contrib the old @objedit used).
        # ------------------------------------------------------------

        try:
            from world.oedit_menu import start_oedit
            start_oedit(caller, obj)

        except Exception as err:
            caller.msg(f"|rFailed to open the editor: {err}|n")

            from evennia.utils import logger
            logger.log_trace()



# ====================================================================
# @redit
# ====================================================================

class CmdRoomEdit(Command):
    """
    Create or edit Rooms through a menu-driven editor.

    Usage:

        @redit <name>
            Create a new Room with this name and open the editor.

        @redit #<dbref>
            Edit an existing Room.

    IMPORTANT:

        A name ALWAYS means "create a new Room".

        A DBREF ALWAYS means "edit an existing Room".

    Examples:

        @redit tavern
            -> creates a new Room named "tavern"

        @redit #123
            -> edits existing Room #123

    This is the Room-only sibling of @oedit, which deliberately
    excludes Rooms - see commands/object_builder.py:CmdOEdit.

    Unlike @oedit, there is no "change type" choice in this editor:
    Room isn't built on the same typeclasses.objects.Object base as
    Item/Weapon/Armor/Key, and rooms were never meant to switch type
    the way those are.

    A newly-created Room has no location of its own (Evennia default
    for Room) - it isn't placed anywhere or connected to anything.
    Link it in with exits once it's built.
    """

    key = "@redit"
    aliases = ["redit"]

    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def parse(self):
        self.target_str = (
            self.args.strip()
            if self.args
            else ""
        )

    # ----------------------------------------------------------------
    # Existing room lookup
    # ----------------------------------------------------------------

    def _find_existing_target(self):
        """
        Find an existing Room by explicit DBREF.

        @redit #123

        searches globally, same reasoning as CmdOEdit's DBREF-only
        rule: no name search here, so `@redit tavern` can never
        accidentally re-open an existing room named "tavern" when the
        builder meant to create a new one.
        """

        caller = self.caller

        dbref_token = self.target_str.split()[0]

        obj = caller.search(
            dbref_token,
            global_search=True,
        )

        if not obj:
            return None

        if not isinstance(obj, Room):
            caller.msg(
                f"{obj.get_display_name(caller)} isn't a Room. "
                f"Use @oedit for non-Room objects."
            )

            return None

        return obj

    # ----------------------------------------------------------------
    # New room creation
    # ----------------------------------------------------------------

    def _create_new_room(self):
        """
        Create a new Room for @redit <name>.

        Unlike @ocreate's new Items, a new Room has no location at
        all (location=None, the normal state for a Room) - it isn't
        placed inside the builder's inventory the way an Item is,
        since a Room isn't something you carry.
        """

        caller = self.caller
        name = self.target_str.strip()

        if not name:
            caller.msg(
                "|rYou must provide a name for the new room.|n"
            )

            return None

        try:
            obj = create_object(
                typeclass=Room,
                key=name,
            )

        except Exception as err:
            caller.msg(
                f"|rFailed to create room: {err}|n"
            )

            from evennia.utils import logger
            logger.log_trace()

            return None

        caller.msg(
            f"|gCreated new Room|n "
            f"|w{obj.key}|n "
            f"({obj.dbref})."
        )

        return obj

    # ----------------------------------------------------------------
    # Main command
    # ----------------------------------------------------------------

    def func(self):
        caller = self.caller

        if not self.target_str:
            caller.msg(
                "Edit what? "
                "Usage: @redit <name> or @redit #<dbref>"
            )

            return

        # ------------------------------------------------------------
        # DBREF = edit existing room.
        #
        #     @redit #123
        # ------------------------------------------------------------

        if self.target_str.startswith("#"):
            obj = self._find_existing_target()

            if not obj:
                return

            # Defensive self-heal, same pattern as CmdImm/CmdHolylight -
            # catches rooms created before room_flags/sector existed.
            if obj.ensure_data_integrity():
                caller.msg(
                    "|x(@redit: found and repaired missing room data)|n"
                )

        # ------------------------------------------------------------
        # Name = create a brand-new Room.
        #
        #     @redit tavern
        # ------------------------------------------------------------

        else:
            obj = self._create_new_room()

            if not obj:
                return

        # ------------------------------------------------------------
        # Show the schema-driven detail view before opening the menu.
        # ------------------------------------------------------------

        caller.msg(
            _render_detail(obj, caller)
        )

        # ------------------------------------------------------------
        # Open the building menu.
        # ------------------------------------------------------------

        try:
            menu = RoomBuildingMenu(
                caller,
                obj,
            )

        except Exception as err:
            caller.msg(
                f"|rFailed to open the editor: {err}|n"
            )

            from evennia.utils import logger
            logger.log_trace()

            return

        if hasattr(menu, "open") and callable(menu.open):
            try:
                menu.open()

            except Exception as err:
                caller.msg(
                    f"|rFailed to display the editor: {err}|n"
                )

                from evennia.utils import logger
                logger.log_trace()