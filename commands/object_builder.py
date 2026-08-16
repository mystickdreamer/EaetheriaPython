"""
Object Builder

Generalized OasisOLC-style browsing/editing across every typeclass
world/object_schema.py knows a schema for.

Commands:

    @olist [<category>] [<search>]   - schema-driven table of matches
    @olist #<dbref>                  - full field dump of one object

    @objedit <name>                  - create a new Item and edit it
    @objedit #<dbref>               - edit an existing object

@objedit deliberately does NOT edit Rooms. Rooms will eventually have
their own @roomedit command.

A name passed to @objedit always means "create a new object".

A DBREF passed to @objedit always means "edit this existing object".

Examples:

    @objedit sword
        -> creates a new Item named "sword"

    @objedit longsword
        -> creates another new Item named "longsword"

    @objedit #123
        -> opens the editor for existing object #123

The typeclass of a newly-created object starts as Item. Change it from
inside the editor with choice "1" (Type) - see
world/building_menus.py:_ObjEditMenu and Object.editor_type in
typeclasses/objects.py.
"""

from evennia.objects.models import ObjectDB
from evennia.utils.create import create_object

from world.object_schema import get_schema

from world.building_menus import menu_class_for

from typeclasses.items import Item, Weapon, Armor, Key
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

    "room": ("typeclasses.rooms", Room),
    "rooms": ("typeclasses.rooms", Room),

    "key": ("typeclasses.items", Key),
    "keys": ("typeclasses.items", Key),
}


# Building menu dispatch now lives in world/building_menus.py as
# menu_class_for()/MENU_DISPATCH - it's shared with
# _ObjEditMenu.close(), which needs the same lookup after a "1. Type"
# change swaps an object's typeclass mid-session.


def _render_detail(obj, looker):
    """
    Full schema-driven field dump for one object.

    This is shared by @olist #<dbref> and @objedit so the two views
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
        f"Use @olist #<dbref> or @objedit <name> for full detail."
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
# @objedit
# ====================================================================

class CmdObjEdit(Command):
    """
    Create or edit non-room objects through a menu-driven editor.

    Usage:

        @objedit <name>
            Create a new Item with this name and open the editor.

        @objedit #<dbref>
            Edit an existing object.

    IMPORTANT:

        A name ALWAYS means "create a new object".

        A DBREF ALWAYS means "edit an existing object".

    Examples:

        @objedit sword
            -> creates a new Item named "sword"

        @objedit longsword
            -> creates another new Item named "longsword"

        @objedit #123
            -> edits existing object #123

    Rooms are deliberately excluded from @objedit. They will eventually
    have their own @roomedit command.

    Newly-created objects start as Item. The object editor will
    eventually provide the ability to change the typeclass from
    inside the editor itself.
    """

    key = "@objedit"
    aliases = ["objedit"]

    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def parse(self):
        """
        Store the raw target string.

        We no longer support:

            @objedit sword = weapon

        Typeclass selection will be handled inside the editor instead.
        """

        self.target_str = (
            self.args.strip()
            if self.args
            else ""
        )

    # ----------------------------------------------------------------
    # Existing object lookup
    # ----------------------------------------------------------------

    def _find_existing_target(self):
        """
        Find an existing object by explicit DBREF.

        @objedit #123

        searches globally because the DBREF explicitly identifies the
        object the builder wants to edit.

        We intentionally do NOT perform a name search here.

        This prevents:

            @objedit sword

        from accidentally editing an existing sword when the builder
        intended to create a new one.
        """

        caller = self.caller

        dbref_token = self.target_str.split()[0]

        obj = caller.search(
            dbref_token,
            global_search=True,
        )

        if not obj:
            return None

        return obj

    # ----------------------------------------------------------------
    # New object creation
    # ----------------------------------------------------------------

    def _create_new_object(self):
        """
        Create a new Item for @objedit <name>.

        The new object is placed in the builder's inventory.

        The object starts as a normal Item. Later, the object editor
        will allow the builder to change its typeclass.
        """

        caller = self.caller
        name = self.target_str.strip()

        if not name:
            caller.msg(
                "|rYou must provide a name for the new object.|n"
            )

            return None

        try:
            obj = create_object(
                typeclass=Item,
                key=name,
                location=caller,
            )

        except Exception as err:
            caller.msg(
                f"|rFailed to create object: {err}|n"
            )

            from evennia.utils import logger
            logger.log_trace()

            return None

        caller.msg(
            f"|gCreated new Item|n "
            f"|w{obj.key}|n "
            f"({obj.dbref})."
        )

        return obj

    # ----------------------------------------------------------------
    # Main command
    # ----------------------------------------------------------------

    def func(self):
        caller = self.caller

        # ------------------------------------------------------------
        # No argument.
        # ------------------------------------------------------------

        if not self.target_str:
            caller.msg(
                "Edit what? "
                "Usage: @objedit <name> or @objedit #<dbref>"
            )

            return

        # ------------------------------------------------------------
        # We intentionally do not support the old:
        #
        #     @objedit sword = weapon
        #
        # syntax.
        #
        # Typeclass changes will happen inside the editor.
        # ------------------------------------------------------------

        if "=" in self.target_str:
            caller.msg(
                "|yThe '= typeclass' syntax is no longer supported.|n\n"
                "Use |w@objedit <name>|n to create an object, "
                "then change its type from inside the object editor."
            )

            return

        # ------------------------------------------------------------
        # DBREF = edit existing object.
        #
        #     @objedit #123
        # ------------------------------------------------------------

        if self.target_str.startswith("#"):
            obj = self._find_existing_target()

            if not obj:
                return

        # ------------------------------------------------------------
        # Name = create a brand-new Item.
        #
        #     @objedit sword
        # ------------------------------------------------------------

        else:
            obj = self._create_new_object()

            if not obj:
                return

        # ------------------------------------------------------------
        # Rooms are intentionally NOT editable through @objedit.
        #
        # This gives us a clean separation:
        #
        #     @objedit  -> objects
        #     @roomedit -> rooms
        # ------------------------------------------------------------

        if isinstance(obj, Room):
            caller.msg(
                "|yRooms cannot be edited with @objedit.|n "
                "Use @roomedit for rooms."
            )

            return

        # ------------------------------------------------------------
        # Find the appropriate menu for the object's current typeclass.
        # ------------------------------------------------------------

        menu_class = menu_class_for(obj)

        if menu_class is None:
            caller.msg(
                f"{obj.get_display_name(caller)} "
                f"isn't currently an editable object type."
            )

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
            menu = menu_class(
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

        # ------------------------------------------------------------
        # Some versions/configurations of the building_menu contrib
        # require an explicit call to open().
        # ------------------------------------------------------------

        if hasattr(menu, "open") and callable(menu.open):
            try:
                menu.open()

            except Exception as err:
                caller.msg(
                    f"|rFailed to display the editor: {err}|n"
                )

                from evennia.utils import logger
                logger.log_trace()