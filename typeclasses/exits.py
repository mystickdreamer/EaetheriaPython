"""
Exits

Exits are connectors between Rooms. An exit always has a destination property
set and has a single command defined on itself with the same name as its key,
for allowing Characters to traverse the exit to its destination.

"""

from evennia.objects.objects import DefaultExit

from .objects import ObjectParent
from world.skills import canonical_skill_name


class Exit(ObjectParent, DefaultExit):
    """
    Exits are connectors between rooms. Exits are normal Objects except
    they defines the `destination` property and overrides some hooks
    and methods to represent the exits.

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects child classes like this.

    """

    pass


# Sensible fallbacks if a LockableExit is ever created without going
# through at_object_creation (e.g. copy-pasted in-game).
DEFAULT_PICK_SUCCESSES = 3
DEFAULT_PICK_ATTRIBUTE = "agility"
DEFAULT_PICK_SKILL = "Thievery"

VALID_ATTRIBUTES = (
    "might", "agility", "endurance",
    "intelligence", "cunning", "willpower",
    "charisma", "influence", "appearance",
)

_TRUTHY_STRINGS = ("true", "yes", "y", "on", "1", "locked", "closed")
_FALSY_STRINGS = ("false", "no", "n", "off", "0", "unlocked", "open")


def _coerce_bool(value, current):
    """
    Best-effort parse of a bool from whatever a menu/builder typed in
    (True/False, yes/no, on/off, 1/0, or an actual bool). Falls back
    to leaving the value unchanged if it can't be parsed, rather than
    silently corrupting state.
    """
    if isinstance(value, bool):
        return value
    text = str(value).strip().lower()
    if text in _TRUTHY_STRINGS:
        return True
    if text in _FALSY_STRINGS:
        return False
    return current


class LockableExit(Exit):
    """
    An Exit that can be locked/unlocked and, while locked, attempted
    against with a dice pool check (see commands.command.CmdPick).

    Raw storage lives on .db (locked, pick_successes, pick_attribute,
    pick_skill, pickable, err_traverse) exactly as before. On top of
    that, this class exposes validated Python *properties* of the
    same names minus the db. prefix (self.locked, self.pick_successes,
    etc.) that parse/clamp/validate on write. These properties are
    what world/building_menus.ExitBuildingMenu binds to via attr=,
    the same way Evennia's own building-menu examples bind to plain
    properties like `key` - so a builder typing "no" into the locked
    field, or "12" into pick_successes, can't corrupt .db with a raw
    unparsed string.

    Key .db fields:
        locked (bool)             - whether the exit currently blocks traversal
        pick_successes (int)      - successes required on a pick attempt to open it
        pick_attribute (str)      - attribute rolled for picking (e.g. "agility")
        pick_skill (str)          - skill rolled for picking (e.g. "Thievery")
        err_traverse (str)        - shown to a character who tries to traverse while locked
        pickable (bool)           - whether `pick` is allowed on this exit at all
                                     (set False for a door that only opens via a
                                     lever/key, never by lockpicking)

    The traverse lock is set to `traverse:door_unlocked()` (see
    server/conf/lockfuncs.py), which simply checks `db.locked`.
    """

    def at_object_creation(self):
        super().at_object_creation()
        self.db.locked = True
        self.db.pick_successes = DEFAULT_PICK_SUCCESSES
        self.db.pick_attribute = DEFAULT_PICK_ATTRIBUTE
        self.db.pick_skill = DEFAULT_PICK_SKILL
        self.db.pickable = True
        self.db.key_id = ""
        # Evennia's own traverse-command checks the "traverse" lock and,
        # on failure, displays db.err_traverse (falling back to a generic
        # message if unset) - so this is the actual denial message, no
        # at_traverse override needed.
        self.db.err_traverse = "The door is locked."
        self.locks.add("traverse:door_unlocked()")

    # ------------------------------------------------------------
    # Validated properties (menu-safe read/write surface)
    # ------------------------------------------------------------
    @property
    def locked(self):
        return bool(self.db.locked)

    @locked.setter
    def locked(self, value):
        self.db.locked = _coerce_bool(value, self.db.locked)

    @property
    def pickable(self):
        return bool(self.db.pickable)

    @pickable.setter
    def pickable(self, value):
        self.db.pickable = _coerce_bool(value, self.db.pickable)

    @property
    def pick_successes(self):
        return self.db.pick_successes

    @pick_successes.setter
    def pick_successes(self, value):
        try:
            parsed = int(str(value).strip())
        except (TypeError, ValueError):
            return  # leave unchanged on bad input rather than crash
        self.db.pick_successes = max(0, parsed)

    @property
    def pick_attribute(self):
        return self.db.pick_attribute

    @pick_attribute.setter
    def pick_attribute(self, value):
        text = str(value).strip().lower()
        if text in VALID_ATTRIBUTES:
            self.db.pick_attribute = text
        # invalid attribute name: leave unchanged

    @property
    def pick_skill(self):
        return self.db.pick_skill

    @pick_skill.setter
    def pick_skill(self, value):
        canonical = canonical_skill_name(str(value).strip())
        if canonical is not None:
            self.db.pick_skill = canonical
        # unrecognized skill name: leave unchanged

    @property
    def err_traverse(self):
        return self.db.err_traverse

    @err_traverse.setter
    def err_traverse(self, value):
        self.db.err_traverse = str(value)

    @property
    def key_id(self):
        return self.db.key_id

    @key_id.setter
    def key_id(self, value):
        self.db.key_id = str(value).strip()

    # ------------------------------------------------------------
    # State
    # ------------------------------------------------------------
    def is_locked(self):
        return self.locked

    def lock(self):
        """Lock the door/exit, blocking traversal until unlocked."""
        self.locked = True

    def unlock(self):
        """Unlock the door/exit, allowing traversal."""
        self.locked = False

    def toggle(self):
        """Flip the current locked state. Returns the new state (bool)."""
        self.locked = not self.locked
        return self.locked

    def key_matches(self, key_obj):
        """Whether the given Key object can unlock this exit."""
        matches = getattr(key_obj, "matches", None)
        if callable(matches):
            return matches(self)
        # Fallback for anything that has a plain key_id but not the
        # full Key.matches() helper.
        my_id = (self.key_id or "").strip()
        their_id = (getattr(key_obj, "key_id", "") or "").strip()
        return bool(my_id) and my_id == their_id

    # ------------------------------------------------------------
    # Pick difficulty configuration
    # ------------------------------------------------------------
    def set_pick_difficulty(self, successes, attribute=None, skill=None):
        """
        Configure how hard this exit is to pick.

        Args:
            successes (int): required successes on the dice check.
            attribute (str, optional): attribute to roll (defaults unchanged if omitted).
            skill (str, optional): skill to roll (defaults unchanged if omitted).
        """
        self.pick_successes = successes
        if attribute is not None:
            self.pick_attribute = attribute
        if skill is not None:
            self.pick_skill = skill

