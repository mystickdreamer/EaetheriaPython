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

    Type q from inside any choice to return to this main menu (instead
    of the contrib's default @).
    """

    keys_go_back = ["q"]

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

class ItemBuildingMenu(building_menu.BuildingMenu):
    """
    Building menu bound to a plain Item (or MISC/FOOD/POTION/MATERIAL
    item using the base typeclass directly). Opened via `itemedit
    <item>`.

    Choices:
        n  - item id            internal id string
        u  - unidentified name  name shown before identification
        d  - identified         whether the true name/desc show yet
        w  - weight
        k  - stackable          whether copies merge in inventory
        m  - size matters       restrict equip to same size_category
        z  - size category      TINY/SMALL/MEDIUM/LARGE/HUGE/GARGANTUAN
        c  - knowledge difficulty
        a  - arcana difficulty
        t  - item type          WEAPON/ARMOR/FOOD/POTION/MATERIAL/MISC
        s  - wear slot          which body slot this equips to (or none)
        g  - equip stat         might/agility/endurance bonus while worn
        j  - equip skill        skill this item is used with
        y  - is magick
        e  - is enchantable
        l  - enchanting mana limit
        f  - is thief tools
        b  - thief tools bonus dice
        r  - light radius (tiles)
        v  - light energy
        o  - bonuses             stat/skill bonuses granted while worn

    Type q from inside any choice to return to this main menu (instead
    of the contrib's default @).
    """

    keys_go_back = ["q"]

    def init(self, item):
        self.add_choice("item id", key="n", attr="item_id")
        self.add_choice("unidentified name", key="u", attr="unidentified_name")
        self.add_choice("identified", key="d", attr="identified")
        self.add_choice("weight", key="w", attr="weight")
        self.add_choice("stackable", key="k", attr="stackable")
        self.add_choice("size matters", key="m", attr="size_matters")
        self.add_choice("size category", key="z", attr="size_category")
        self.add_choice("knowledge difficulty", key="c", attr="knowledge_difficulty")
        self.add_choice("arcana difficulty", key="a", attr="arcana_difficulty")
        self.add_choice("item type", key="t", attr="item_type")
        self.add_choice("wear slot", key="s", attr="wear_slot")
        self.add_choice("equip stat", key="g", attr="equip_stat")
        self.add_choice("equip skill", key="j", attr="equip_skill")
        self.add_choice("is magick", key="y", attr="is_magick")
        self.add_choice("is enchantable", key="e", attr="is_enchantable")
        self.add_choice("enchanting mana limit", key="l", attr="enchanting_mana_limit")
        self.add_choice("is thief tools", key="f", attr="is_thief_tools")
        self.add_choice("thief tools bonus dice", key="b", attr="thief_tools_bonus_dice")
        self.add_choice("light radius (tiles)", key="r", attr="light_radius_tiles")
        self.add_choice("light energy", key="v", attr="light_energy")
        # Entering this choice shows Item.stat_bonuses_command's getter
        # (a formatted summary of the dict) and re-renders it fresh
        # after every edit, since attr= choices always redisplay via
        # the live property rather than a snapshot. Typing "OneHand 2"
        # or "remove OneHand" goes through that property's setter,
        # which mutates the dict through add_stat_bonus()/
        # remove_stat_bonus() - see typeclasses/items.py.
        self.add_choice("bonuses", key="o", attr="stat_bonuses_command")


class WeaponBuildingMenu(ItemBuildingMenu):
    """
    ItemBuildingMenu plus a dedicated combat section for the fields
    that matter on a weapon. Opened via `itemedit <item>` when the
    target is a Weapon (or Weapon subclass).

    Adds:
        x  - weapon type       AXE/BOW/CHAINED/CROSSBOW/BLUNT/SLASHING/
                                PIERCING/UNARMED/NONE
        p  - stamina cost      0 falls back to caller's default
    """

    def init(self, item):
        super().init(item)
        self.add_choice("weapon type", key="x", attr="weapon_type")
        self.add_choice("stamina cost", key="p", attr="stamina_cost")


class ArmorBuildingMenu(ItemBuildingMenu):
    """
    ItemBuildingMenu with no additional fields - Armor uses the same
    attributes as the base Item, just different at_object_creation
    defaults (item_type=ARMOR, wear_slot=torso). Kept as its own class
    (rather than reusing ItemBuildingMenu directly) so `itemedit` can
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
    Building menu bound to a Room instance.

    Choices:
        n  - name          the room's key/display name
        d  - description    what `look` shows for the room

    Kept intentionally small: Eaetheria has no room-specific game
    mechanics defined yet (lighting, safe zones, terrain, weather,
    ...) - same reasoning as the "no armor-specific fields yet" note
    on ArmorBuildingMenu above and on ROOM_SCHEMA in
    world/object_schema.py. Add choices here (and matching fields to
    ROOM_SCHEMA) once those mechanics actually exist, rather than
    inventing placeholders now.

    Type q from inside any choice to return to this main menu (instead
    of the contrib's default @).
    """

    keys_go_back = ["q"]

    def init(self, room):
        self.add_choice("name", key="n", attr="key")
        self.add_choice("description", key="d", attr="db.desc")


# ==========================================================================
# Key - OasisOLC-style editor
#
# Key (typeclasses.items.Key) is NOT an Item subclass - it's its own
# plain-Object typeclass with a single validated field (key_id).
# Opened via `@objedit <key>` the same way Room is; there's no
# dedicated `keyedit` command since one field doesn't need its own
# top-level command.
# ==========================================================================

class KeyBuildingMenu(building_menu.BuildingMenu):
    """
    Building menu bound to a Key instance.

    Choices:
        i - key id   the tag a LockableExit's key_id must match for
                      this key to unlock it (see typeclasses/exits.py)

    Type q from inside any choice to return to this main menu (instead
    of the contrib's default @).
    """

    keys_go_back = ["q"]

    def init(self, key_obj):
        self.add_choice("key id", key="i", attr="key_id")

