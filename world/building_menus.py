"""
Building menus (OasisOLC-style editing)

Menu-driven editors for builders, in the spirit of tbaMUD's OasisOLC -
pick a numbered/lettered choice instead of typing a string of @set
commands. This is NOT a port of OasisOLC's C code (Evennia's object
model - persistent Python typeclasses in a database - has nothing in
common with tbaMUD's vnum/flat-file world), it's a fresh menu built on
Evennia's own `building_menu` contrib, which exists for exactly this
purpose.

Caveat: this file was written directly against Evennia's documented
building_menu usage pattern (subclass BuildingMenu, override
init(self, obj), call self.add_choice(name, key, attr=...)), which is
the one pattern confirmed in Evennia's docs. It has NOT been
smoke-tested against a live Evennia install (no network access in the
sandbox this was written in), unlike the rest of this project's code.
Test it with `evennia reload` + `doedit <exit>` before relying on it,
and check evennia/contrib/base_systems/building_menu/README.md in
your own install if anything about add_choice's behavior looks off.

To keep this reliable despite that gap, all the actual validation
(parsing "yes"/"no" into a bool, clamping pick_successes to a
non-negative int, checking pick_skill against the real skill list)
lives in ordinary Python properties on LockableExit itself (see
typeclasses/exits.py) - code that *was* unit-tested. This menu just
points attr= at those properties, the same way Evennia's own
building_menu examples point attr="key" at DefaultObject.key.
"""

from evennia.contrib.base_systems import building_menu


# ==========================================================================
# @objedit menus (Item/Weapon/Armor/Key) - numbered choices + type switch
#
# _ObjEditMenu is the shared base for everything @objedit covers except
# Room (Room is intentionally excluded from @objedit - see
# commands/object_builder.py - and mobs have no typeclass here yet).
#
# Every _ObjEditMenu subclass gets, in this fixed order:
#     1.  Type            change typeclass mid-session (see close() below
#                          and Object.editor_type in typeclasses/objects.py)
#     2+  ...subclass fields, numbered by init_fields()...
#     s   save & quit
#     q   quit
#
# All keys are matched case-insensitively, same as every other Evennia
# command - nothing special needed for that part.
#
# Caveat on the "1. Type" -> live menu reshaping: this contrib's
# documented pattern (subclass BuildingMenu, add_choice(name, key=,
# attr=)) has no confirmed-safe way *we've verified* to swap which menu
# class is driving an already-open session. Rather than guess at
# unverified submenu-switching internals - which is exactly what broke
# @objedit last time (a whole menu class, ObjectBuildingMenu, was
# referenced but never actually written) - close() below takes the
# safe route: if the typeclass changed while the menu was open, it
# closes normally and then opens a fresh instance of the correct menu
# class for the new type. One extra render, zero guessing.
#
# This still rests on one assumption we could not verify offline (no
# live Evennia install / network access in the sandbox this was
# written in): that BuildingMenu stores the bound object as self.obj.
# That's the standard/documented pattern and is very likely right, but
# smoke-test the "1. Type" -> save flow with `evennia reload` +
# `@objedit <name>` before relying on it, same caveat as the rest of
# this file.
# ==========================================================================

class _ObjEditMenu(building_menu.BuildingMenu):
    """
    Shared base for the Item/Weapon/Armor/Key menus opened by
    @objedit. See the module-level comment above for the overall
    design (numbered choices, "1. Type", s/q to close).

    Bug note (found live, not just from the "not smoke-tested"
    caveat above): this class used to set `keys_go_back = ["q"]` on
    top of also binding a "quit" choice to key="q" via
    add_choice_quit. That doesn't work - the contrib's CmdNoMatch
    checks `raw_string in self.menu.keys_go_back` BEFORE it checks
    for a matching choice key, so "q" was always swallowed by the
    go-back branch and the actual quit choice (on_enter=menu_quit,
    which removes BuildingMenuCmdSet) was unreachable. At the top of
    the menu (no keys, no parents) the go-back branch just calls
    self.menu.display() again - which is exactly the "closing"
    message appears, but the cmdset is never actually removed, and
    'q' just redisplays the menu" symptom. "s" (save & quit) was
    unaffected since it isn't in keys_go_back.

    Fix: leave keys_go_back at the contrib's own default (["@"]),
    which no choice here uses, so "q" reaches the real quit choice
    instead of being intercepted.
    """

    def init(self, obj):
        self._opened_as = type(obj)
        self.add_choice("type", key="1", attr="editor_type")
        self.init_fields(obj)
        self.add_choice_quit("save & quit", key="s", aliases=["save"])
        self.add_choice_quit("quit", key="q", aliases=["quit", "exit"])

    def init_fields(self, obj):
        """Subclasses add their own numbered choices here, starting at 2."""
        raise NotImplementedError

    def close(self):
        obj = self.obj
        changed = type(obj) is not self._opened_as
        super().close()

        if not changed:
            return

        # Local import: avoids a module-load-time circular import with
        # commands/object_builder.py, which also imports from this
        # module.
        new_menu_class = menu_class_for(obj)

        if new_menu_class is None:
            return

        self.caller.msg(
            f"|gType changed to {type(obj).__name__}|n - "
            f"reopening the editor."
        )

        menu = new_menu_class(self.caller, obj)

        if hasattr(menu, "open") and callable(menu.open):
            menu.open()


class ExitBuildingMenu(building_menu.BuildingMenu):
    """
    Building menu bound to a LockableExit instance. Opened via the
    `doedit <exit>` command (see commands/command.py: CmdDoorEdit).

    Choices:
        l - locked          toggle whether the door currently blocks traversal
        p - pickable         toggle whether `pick` is allowed on this door at all
        s - pick successes   how many successes a pick attempt needs
        a - pick attribute   which attribute is rolled when picking
        k - pick skill       which skill is rolled when picking
        m - locked message   text shown to someone who tries to traverse while locked
        i - key id           the tag a matching Key item must have to lock/unlock this door

    Type @ from inside any choice to return to this main menu (the
    contrib's default go-back key - left un-overridden here, since
    "q" is already spoken for by the auto-added "quit the menu"
    choice below; see the module-level note on _ObjEditMenu.close()
    for why those two can't share a key).
    """

    def init(self, exit_obj):
        self.add_choice(
            "locked",
            key="l",
            attr="locked",
        )
        self.add_choice(
            "pickable",
            key="p",
            attr="pickable",
        )
        self.add_choice(
            "pick successes",
            key="s",
            attr="pick_successes",
        )
        self.add_choice(
            "pick attribute",
            key="a",
            attr="pick_attribute",
        )
        self.add_choice(
            "pick skill",
            key="k",
            attr="pick_skill",
        )
        self.add_choice(
            "locked message",
            key="m",
            attr="err_traverse",
        )
        self.add_choice(
            "key id",
            key="i",
            attr="key_id",
        )


# ==========================================================================
# Item / Weapon / Armor - OasisOLC-style editor
#
# One command (`itemedit`, see commands/command.py: CmdItemEdit) picks
# which of these three menu classes to open based on the target's
# actual typeclass - that's what gives the "menu changes depending on
# typeclass" behavior asked for, rather than one menu trying to show
# every field for every kind of item. All three bind to the validated
# properties on typeclasses.items.Item (see the "Validated properties"
# block there), never to .db directly, for the same reason
# ExitBuildingMenu above binds to LockableExit's properties.
#
# ItemBuildingMenu covers every field the base Item typeclass has,
# which is also everything a plain MISC/FOOD/POTION/MATERIAL item
# uses. WeaponBuildingMenu and ArmorBuildingMenu each add a `combat`
# section on top of that for the fields that matter once the item is
# equipment (weapon_type/stamina_cost for weapons; equip_stat/
# equip_skill emphasized for armor) - both are already present on the
# base Item and simply get their own labeled entry point here so a
# builder editing a weapon isn't hunting through misc/light/tool
# sections to find them.
# ==========================================================================

class ItemBuildingMenu(_ObjEditMenu):
    """
    Building menu bound to a plain Item (or MISC/FOOD/POTION/MATERIAL
    item using the base typeclass directly). Opened via `@objedit
    <name>` (create) or `@objedit #<dbref>` (edit an existing Item).

    Choices:
        1  - type                change typeclass (Item/Weapon/Armor/Key)
        2  - item id              internal id string
        3  - unidentified name    name shown before identification
        4  - identified           whether the true name/desc show yet
        5  - weight
        6  - stackable            whether copies merge in inventory
        7  - size matters         restrict equip to same size_category
        8  - size category        TINY/SMALL/MEDIUM/LARGE/HUGE/GARGANTUAN
        9  - knowledge difficulty
        10 - arcana difficulty
        11 - item type            WEAPON/ARMOR/FOOD/POTION/MATERIAL/MISC
        12 - wear slot            which body slot this equips to (or none)
        13 - equip stat           might/agility/endurance bonus while worn
        14 - equip skill          skill this item is used with
        15 - is magick
        16 - is enchantable
        17 - enchanting mana limit
        18 - magick words         word ids (world/magick_words.py) this
                                   object teaches via 'study' - only
                                   meaningful when is magick is set
        19 - is thief tools
        20 - thief tools bonus dice
        21 - light radius (tiles)
        22 - light energy
        23 - bonuses              stat/skill bonuses granted while worn
        s  - save & quit
        q  - quit

    All keys are case-insensitive, per normal Evennia command matching.
    """

    def init_fields(self, item):
        self.add_choice("item id", key="2", attr="item_id")
        self.add_choice("unidentified name", key="3", attr="unidentified_name")
        self.add_choice("identified", key="4", attr="identified")
        self.add_choice("weight", key="5", attr="weight")
        self.add_choice("stackable", key="6", attr="stackable")
        self.add_choice("size matters", key="7", attr="size_matters")
        self.add_choice("size category", key="8", attr="size_category")
        self.add_choice("knowledge difficulty", key="9", attr="knowledge_difficulty")
        self.add_choice("arcana difficulty", key="10", attr="arcana_difficulty")
        self.add_choice("item type", key="11", attr="item_type")
        self.add_choice("wear slot", key="12", attr="wear_slot")
        self.add_choice("equip stat", key="13", attr="equip_stat")
        self.add_choice("equip skill", key="14", attr="equip_skill")
        self.add_choice("is magick", key="15", attr="is_magick")
        self.add_choice("is enchantable", key="16", attr="is_enchantable")
        self.add_choice("enchanting mana limit", key="17", attr="enchanting_mana_limit")
        self.add_choice("magick words", key="18", attr="magick_words_command")
        self.add_choice("is thief tools", key="19", attr="is_thief_tools")
        self.add_choice("thief tools bonus dice", key="20", attr="thief_tools_bonus_dice")
        self.add_choice("light radius (tiles)", key="21", attr="light_radius_tiles")
        self.add_choice("light energy", key="22", attr="light_energy")
        # Entering this choice shows Item.stat_bonuses_command's getter
        # (a formatted summary of the dict) and re-renders it fresh
        # after every edit, since attr= choices always redisplay via
        # the live property rather than a snapshot. Typing "OneHand 2"
        # or "remove OneHand" goes through that property's setter,
        # which mutates the dict through add_stat_bonus()/
        # remove_stat_bonus() - see typeclasses/items.py.
        self.add_choice("bonuses", key="23", attr="stat_bonuses_command")


class AltarBuildingMenu(ItemBuildingMenu):
    """
    ItemBuildingMenu with no additional fields - Altar uses the same
    attributes as the base Item, just different at_object_creation
    defaults (non-equippable, non-stackable). Kept as its own class
    (rather than reusing ItemBuildingMenu directly) for the same
    reason as ArmorBuildingMenu: @objedit dispatches on typeclass, and
    a header/title reading "Altar" is easy to add here later.
    """


class WeaponBuildingMenu(ItemBuildingMenu):
    """
    ItemBuildingMenu plus a dedicated combat section for the fields
    that matter on a weapon. Opened via @objedit when the target is a
    Weapon (or Weapon subclass) - either directly, or after switching
    an object's type to Weapon from choice 1.

    Adds:
        24 - weapon type   AXE/BOW/CHAINED/CROSSBOW/BLUNT/SLASHING/
                            PIERCING/UNARMED/NONE
        25 - stamina cost  0 falls back to caller's default
    """

    def init_fields(self, item):
        super().init_fields(item)
        self.add_choice("weapon type", key="24", attr="weapon_type")
        self.add_choice("stamina cost", key="25", attr="stamina_cost")


class ArmorBuildingMenu(ItemBuildingMenu):
    """
    ItemBuildingMenu with no additional fields - Armor uses the same
    attributes as the base Item, just different at_object_creation
    defaults (item_type=ARMOR, wear_slot=torso). Kept as its own class
    (rather than reusing ItemBuildingMenu directly) so @objedit can
    dispatch on typeclass and so a header/title reading "Armor" is
    easy to add here later without touching ItemBuildingMenu.
    """


# ==========================================================================
# Room - OasisOLC-style editor
#
# Opened via `@objedit <room>` (see commands/object_builder.py:
# CmdObjEdit), the generalized sibling of `itemedit` that dispatches
# across every typeclass world/object_schema.py knows a schema for,
# not just Item/Weapon/Armor.
# ==========================================================================

class RoomBuildingMenu(building_menu.BuildingMenu):
    """
    Building menu bound to a Room instance. Opened via `@redit <name>`
    (create) or `@redit #<dbref>` (edit an existing Room) - see
    CmdRoomEdit in commands/object_builder.py.

    Choices:
        1 - name          the room's key/display name
        2 - description   what `look` shows for the room
        3 - sector        terrain classification (see world/sectors.py)
        4 - flags         toggle ROOM_* flags (see world/room_flags.py)
        5 - is magick location   whether 'study here' works at all
        6 - magick words         word ids this location teaches via
                                  'study here' (see world/magick_words.py)
        s - save & quit
        q - quit

    No "Type" choice here, unlike the @objedit menus: Room is
    ObjectParent+DefaultRoom, not typeclasses.objects.Object, so it
    doesn't inherit Object.editor_type - and per the original design,
    rooms (and eventually mobs) are intentionally excluded from
    typeclass-switching anyway.

    sector/flags are classification/metadata only for now - nothing
    in the engine yet reads them to change behavior (see the module
    docstrings on world/sectors.py and world/room_flags.py). Kept
    otherwise small for the same reason as the "no armor-specific
    fields yet" note on ArmorBuildingMenu above: don't invent
    mechanics the game doesn't use yet.

    Go-back key inside a field edit is "@" (the contrib default,
    left un-overridden) rather than "q" - see the bug note on
    _ObjEditMenu.__doc__ above for why "q" can't do double duty as
    both go-back and the "quit" choice below.
    """

    def init(self, room):
        self.add_choice("name", key="1", attr="key")
        self.add_choice("description", key="2", attr="db.desc")
        self.add_choice("sector", key="3", attr="sector")
        self.add_choice("flags", key="4", attr="flags_command")
        self.add_choice("is magick location", key="5", attr="is_magick_location")
        self.add_choice("magick words", key="6", attr="magick_words_command")
        self.add_choice_quit("save & quit", key="s", aliases=["save"])
        self.add_choice_quit("quit", key="q", aliases=["quit", "exit"])


# ==========================================================================
# Key - OasisOLC-style editor
#
# Key (typeclasses.items.Key) is NOT an Item subclass - it's its own
# plain-Object typeclass with a single validated field (key_id).
# Opened via `@objedit <key>` the same way Room is; there's no
# dedicated `keyedit` command since one field doesn't need its own
# top-level command.
# ==========================================================================

class KeyBuildingMenu(_ObjEditMenu):
    """
    Building menu bound to a Key instance. Opened via @objedit the
    same way Item/Weapon/Armor are.

    Choices:
        1 - type      change typeclass (Item/Weapon/Armor/Key)
        2 - key id    the tag a LockableExit's key_id must match for
                      this key to unlock it (see typeclasses/exits.py)
        s - save & quit
        q - quit
    """

    def init_fields(self, key_obj):
        self.add_choice("key id", key="2", attr="key_id")


# --------------------------------------------------------------------
# Shared by _ObjEditMenu.close() (above) and commands/object_builder.py
# (CmdObjEdit, CmdOList): which menu class to open for a given object's
# current typeclass. Most-specific typeclasses must come first because
# Weapon and Armor inherit from Item. Room is intentionally absent -
# @objedit never touches Rooms (see commands/object_builder.py).
# --------------------------------------------------------------------

from typeclasses.items import Item, Weapon, Armor, Altar, Key  # noqa: E402

MENU_DISPATCH = [
    (Weapon, WeaponBuildingMenu),
    (Armor, ArmorBuildingMenu),
    (Altar, AltarBuildingMenu),
    (Item, ItemBuildingMenu),
    (Key, KeyBuildingMenu),
]


def menu_class_for(obj):
    """
    Return the @objedit menu class for obj's current typeclass, or
    None if @objedit doesn't cover that typeclass (e.g. Room).
    """

    for cls, menu_class in MENU_DISPATCH:
        if isinstance(obj, cls):
            return menu_class

    return None

