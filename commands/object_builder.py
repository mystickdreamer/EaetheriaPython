"""
Object Builder

Generalized OasisOLC-style browsing/editing across every typeclass
world/object_schema.py knows a schema for - currently Item/Weapon/
Armor and Room. Two commands:

    @olist [<category>] [<search>]   - schema-driven table of matches
    @olist #<dbref>                  - full field dump of one object
    @objedit <object>                - open the matching building menu
    @objedit <object> = <typeclass>  - swap typeclass first, then edit

`itemedit` (see commands/command.py: CmdItemEdit) still works exactly
as before and is unaffected by any of this - both commands here are
read-only browsing plus one new typeclass-swap path itemedit never
had. See the caveat at the top of world/building_menus.py: none of
the menu-opening code below has been smoke-tested against a live
Evennia install.
"""

from evennia.objects.models import ObjectDB
from evennia.utils.utils import class_from_module

from world.object_schema import get_schema
from world.building_menus import (
    ItemBuildingMenu, WeaponBuildingMenu, ArmorBuildingMenu, RoomBuildingMenu,
    KeyBuildingMenu,
)
from typeclasses.items import Item, Weapon, Armor, Key
from typeclasses.rooms import Room

from commands.command import Command


# --------------------------------------------------------------------
# Category keywords accepted by @olist - each maps to the typeclass
# path prefix to query ObjectDB with, and the class isinstance()
# then filters results down to (Item/Weapon/Armor all live under
# typeclasses.items alongside Key, which isinstance() excludes -
# same caution the original item-only design flagged about
# typeclass-path filtering by itself being too broad).
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

# What @objedit's "= <shorthand>" clause accepts in addition to a
# full dotted path.
TYPECLASS_SHORTHAND = {
    "item": "typeclasses.items.Item",
    "weapon": "typeclasses.items.Weapon",
    "armor": "typeclasses.items.Armor",
    "room": "typeclasses.rooms.Room",
    "key": "typeclasses.items.Key",
}

# Building menu dispatch, most-specific typeclass first - same
# ordering CmdItemEdit already uses for Item/Weapon/Armor, extended
# with Room and Key.
MENU_DISPATCH = [
    (Weapon, WeaponBuildingMenu),
    (Armor, ArmorBuildingMenu),
    (Item, ItemBuildingMenu),
    (Room, RoomBuildingMenu),
    (Key, KeyBuildingMenu),
]


def _menu_class_for(obj):
    """Return the building menu class for obj's typeclass, or None."""
    for cls, menu_class in MENU_DISPATCH:
        if isinstance(obj, cls):
            return menu_class
    return None


def _render_detail(obj, looker):
    """
    Full schema-driven field dump for one object - shared by
    `@olist #<dbref>` and `@objedit` (opened right before the menu),
    so the two views never drift apart.
    """
    schema = get_schema(obj)
    if schema is None:
        return (
            f"{obj.get_display_name(looker)} ({obj.dbref}) has no object "
            f"schema registered for its typeclass "
            f"({type(obj).__module__}.{type(obj).__name__})."
        )

    lines = [f"|w{obj.get_display_name(looker)}|n ({obj.dbref}) - {schema.label}"]

    current_category = None
    for field in schema.get_fields():
        if field.category != current_category:
            current_category = field.category
            lines.append(f"\n|c{current_category.title()}|n")
        lines.append(f"  {field.label}: {field.get_value(obj)}")

    return "\n".join(lines)


def _render_table(objects, looker):
    """Summary table for @olist's multi-result view."""
    lines = [f"{'Dbref':<8}{'Name':<30}{'Typeclass'}"]
    lines.append("-" * 70)
    for obj in objects:
        typeclass_name = f"{type(obj).__module__}.{type(obj).__name__}"
        lines.append(
            f"{obj.dbref:<8}{obj.get_display_name(looker):<30}{typeclass_name}"
        )
    lines.append(
        f"\n{len(objects)} match(es). Use @olist #<dbref> or @objedit "
        f"<name> for full detail."
    )
    return "\n".join(lines)


class CmdOList(Command):
    """
    Browse objects with a schema-driven table.

    Usage:
      @olist
      @olist <category>
      @olist <category> <search>
      @olist <search>
      @olist #<dbref>

    Categories: item, weapon, armor, room, key (plurals accepted).
    With no category, defaults to items. A bare non-category argument
    is treated as a name search within the default (item) category
    instead - so @olist sword still works exactly like before.

    @olist #<dbref> shows the same full field dump @objedit opens
    with, for that one object, regardless of category.

    Examples:
      @olist                  - table of every Item/Weapon/Armor
      @olist weapons           - just Weapons
      @olist rooms tavern      - Rooms with "tavern" in their name
      @olist keys              - every Key
      @olist sword             - Items with "sword" in their name
      @olist #42                - full detail dump of #42
    """

    key = "@olist"
    aliases = ["olist"]
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller
        args = self.args.strip() if self.args else ""

        if args.startswith("#"):
            dbref_token = args.split()[0]
            obj = caller.search(dbref_token, global_search=True)
            if not obj:
                return
            caller.msg(_render_detail(obj, caller))
            return

        parts = args.split(None, 1) if args else []
        category = "item"
        term = ""
        if parts and parts[0].lower() in CATEGORY_MAP:
            category = parts[0].lower()
            term = parts[1] if len(parts) > 1 else ""
        else:
            term = args

        path_prefix, base_cls = CATEGORY_MAP[category]
        matches = [
            obj
            for obj in ObjectDB.objects.filter(
                db_typeclass_path__startswith=path_prefix
            )
            if isinstance(obj, base_cls)
        ]

        if term:
            term_lower = term.lower()
            matches = [obj for obj in matches if term_lower in obj.key.lower()]

        if not matches:
            caller.msg("No matching objects found.")
            return

        caller.msg(_render_table(matches, caller))


class CmdObjEdit(Command):
    """
    Open a menu-driven editor for any known object type - items,
    weapons, armor, rooms, and keys (OasisOLC-style, the same
    underlying menus itemedit and doedit use).

    Usage:
      @objedit <object>
      @objedit <object> = item|weapon|armor|room|key
      @objedit <object> = <full.typeclass.path>

    Without the `=` clause, the object must already be one of the
    known types. With it, the object's typeclass is swapped first
    (via swap_typeclass, which reruns at_object_creation so every
    default .db field actually exists to edit) and the matching menu
    opens on the result.

    If the object is already exactly that typeclass, the swap is
    skipped rather than silently re-running its creation hooks and
    resetting fields you've already set.

    `@objedit here` (or the room's own name) edits your current room.
    Otherwise the search is scoped to your inventory and the current
    room's contents - same as itemedit, this doesn't do a global
    #dbref-anywhere search.

    See 'help item attributes' for what the item fields mean.
    """

    key = "@objedit"
    aliases = ["objedit"]
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def parse(self):
        args = self.args or ""
        if "=" in args:
            target, _, typeclass_spec = args.partition("=")
            self.target_str = target.strip()
            self.typeclass_spec = typeclass_spec.strip()
        else:
            self.target_str = args.strip()
            self.typeclass_spec = ""

    def _resolve_target_typeclass(self, spec):
        """
        Resolve item/weapon/armor/room or a full dotted path to an
        actual class, via class_from_module() - the same call
        Evennia's own @typeclass command uses. Returns None (and
        messages the caller) on failure.
        """
        caller = self.caller
        path = TYPECLASS_SHORTHAND.get(spec.lower(), spec)

        try:
            cls = class_from_module(path)
        except Exception:
            caller.msg(
                f"|rCouldn't find typeclass '{spec}'. Use item/weapon/"
                f"armor/room/key, or a full dotted path.|n"
            )
            return None

        if not (issubclass(cls, Item) or issubclass(cls, Room) or issubclass(cls, Key)):
            caller.msg(
                f"|r{path} isn't an Item, Room, or Key subclass - refusing "
                f"to swap (that would break @objedit's menu dispatch).|n"
            )
            return None

        return cls

    def _find_target(self):
        """
        Search scope matches itemedit's (caller's inventory + current
        room's contents), plus the current room itself so `@objedit
        here` / `@objedit <room name>` work while standing in it.
        """
        caller = self.caller
        location = caller.location

        if self.target_str.lower() == "here" and location:
            return location

        candidates = list(caller.contents)
        if location:
            candidates += location.contents + [location]

        return caller.search(self.target_str, candidates=candidates)

    def func(self):
        caller = self.caller

        if not self.target_str:
            caller.msg("Edit what? Usage: @objedit <object>")
            return

        obj = self._find_target()
        if not obj:
            return

        if self.typeclass_spec:
            new_cls = self._resolve_target_typeclass(self.typeclass_spec)
            if new_cls is None:
                return

            if type(obj) is not new_cls:
                obj.swap_typeclass(
                    new_cls, clean_attributes=False, run_start_hooks="all"
                )

        menu_class = _menu_class_for(obj)
        if menu_class is None:
            caller.msg(
                f"{obj.get_display_name(caller)} isn't an editable type "
                f"(Item/Weapon/Armor/Room/Key). Use @objedit {obj.key} = "
                f"item|weapon|armor|room|key to make it one first."
            )
            return

        caller.msg(_render_detail(obj, caller))

        try:
            menu = menu_class(caller, obj)
        except Exception as err:
            caller.msg(f"|rFailed to open the editor: {err}|n")
            from evennia.utils import logger
            logger.log_trace()
            return

        # Some versions/configurations of the building_menu contrib
        # require an explicit call to start displaying the menu rather
        # than doing so automatically on construction - same note as
        # CmdItemEdit/CmdDoorEdit in commands/command.py.
        if hasattr(menu, "open") and callable(menu.open):
            try:
                menu.open()
            except Exception as err:
                caller.msg(f"|rFailed to display the editor: {err}|n")
                from evennia.utils import logger
                logger.log_trace()
