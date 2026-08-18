"""
Room

Rooms are simple containers that has no location of their own.
"""

from evennia.objects.objects import DefaultRoom

from .objects import ObjectParent
from world import room_flags as room_flags_registry
from world.magick_words import canonical_word_id as canonical_magick_word_id
from world.sectors import DEFAULT_SECTOR, is_valid_sector, sector_display_name


class Room(ObjectParent, DefaultRoom):
    """
    Rooms are like any Object, except their location is None
    (which is default). They also use basetype_setup() to
    add locks so they cannot be puppeted or picked up.
    (to change that, use at_object_creation instead)

    See mygame/typeclasses/objects.py for a list of
    properties and methods available on all Objects.
    """

    def at_object_creation(self):
        super().at_object_creation()

        # ===== Flags (id -> True; see world/room_flags.py) =====
        # Dict-of-True rather than a list/set, same shape as
        # Character.db.perks/backgrounds in typeclasses/characters.py -
        # O(1) has_flag() lookups, and room to attach per-flag data
        # later if a flag ever needs one.
        self.db.room_flags = {}

        # ===== Sector (single value; see world/sectors.py) =====
        self.db.sector = DEFAULT_SECTOR

        # ===== Magick =====
        # Ambient Magick words this location itself teaches via
        # 'study here'/'study room' - for ancient inscriptions,
        # ritual sites, magical locations etc. that aren't a discrete
        # object a player could pick up. Same shape/gate as
        # typeclasses.items.Item's is_magick/magick_words - see
        # CmdStudy in commands/command.py.
        self.db.is_magick_location = False
        self.db.magick_words = []

    def ensure_data_integrity(self):
        """
        Self-healing check, same pattern/contract as
        Character.ensure_data_integrity() in typeclasses/characters.py:
        fills in fields this typeclass expects but a given Room
        doesn't have yet (created before these fields existed).
        Existing values are never touched. Returns True if anything
        was healed. Called from CmdRoomEdit when opening an existing
        room (commands/object_builder.py) - Room has no per-room
        status command of its own to trigger it from otherwise.
        """
        healed = False

        if not self.attributes.has("room_flags"):
            self.attributes.add("room_flags", {})
            healed = True

        if not self.attributes.has("sector"):
            self.attributes.add("sector", DEFAULT_SECTOR)
            healed = True

        if not self.attributes.has("is_magick_location"):
            self.attributes.add("is_magick_location", False)
            healed = True

        if not self.attributes.has("magick_words"):
            self.attributes.add("magick_words", [])
            healed = True

        return healed

    # ==================================================================
    # Flags (see world/room_flags.py)
    #
    # Validated read/write surface, same convention as
    # typeclasses.items.Item's properties: raw storage stays on .db,
    # each accessor validates/normalizes and silently no-ops on an
    # unrecognized flag id rather than corrupting .db or raising into
    # a menu/command.
    # ==================================================================
    @property
    def flags(self):
        """Currently-set flag ids, as a sorted list."""
        return sorted((self.db.room_flags or {}).keys())

    def has_flag(self, flag_id):
        return bool((self.db.room_flags or {}).get(str(flag_id).strip().upper()))

    def add_flag(self, flag_id):
        """Set a flag. Returns False (no-op) if flag_id isn't recognized."""
        flag_id = str(flag_id).strip().upper()
        if not room_flags_registry.is_valid_flag(flag_id):
            return False
        flags = dict(self.db.room_flags or {})
        flags[flag_id] = True
        self.db.room_flags = flags
        return True

    def remove_flag(self, flag_id):
        """Clear a flag. Returns False (no-op) if it wasn't set."""
        flag_id = str(flag_id).strip().upper()
        flags = dict(self.db.room_flags or {})
        if flag_id not in flags:
            return False
        del flags[flag_id]
        self.db.room_flags = flags
        return True

    def toggle_flag(self, flag_id):
        """
        Flip a flag on/off. Returns the new state (True/False), or
        None if flag_id isn't recognized.
        """
        flag_id = str(flag_id).strip().upper()
        if not room_flags_registry.is_valid_flag(flag_id):
            return None
        if self.has_flag(flag_id):
            self.remove_flag(flag_id)
            return False
        self.add_flag(flag_id)
        return True

    @property
    def flags_command(self):
        """
        Menu-facing view of room_flags: on/off state of every known
        flag plus the syntax used to toggle one. world.building_menus.
        RoomBuildingMenu's "flags" choice binds to this via attr= -
        same live-rerender-on-attr pattern as Item.stat_bonuses_command
        in typeclasses/items.py.
        """
        lines = []
        for flag_id, info in room_flags_registry.ROOM_FLAGS.items():
            state = "|gON |n" if self.has_flag(flag_id) else "|xoff|n"
            lines.append(f"  [{state}] {flag_id:<10} {info['display_name']}")
        body = "\n".join(lines)
        return (
            f"Current flags:\n{body}\n\n"
            "Type a flag name to toggle it (e.g. 'PEACEFUL')."
        )

    @flags_command.setter
    def flags_command(self, value):
        # Unrecognized name: toggle_flag() returns None and this is a
        # silent no-op, same convention as every other validated
        # setter in this codebase.
        self.toggle_flag(str(value).strip())

    # ==================================================================
    # Sector (see world/sectors.py)
    # ==================================================================
    @property
    def sector(self):
        return self.db.sector or DEFAULT_SECTOR

    @sector.setter
    def sector(self, value):
        text = str(value).strip().upper()
        if is_valid_sector(text):
            self.db.sector = text
        # unrecognized sector id: leave unchanged, same silent-ignore
        # convention as the validated setters in typeclasses/items.py

    @property
    def sector_display(self):
        """Human-readable sector name - read-only, for detail dumps."""
        return sector_display_name(self.sector)

    # ==================================================================
    # Magick (ambient words - see world/magick_words.py and CmdStudy
    # in commands/command.py). Mirrors typeclasses.items.Item's
    # is_magick/magick_words + magick_words_command exactly - same
    # gate, same menu-facing edit syntax - just scoped to a Room
    # instead of an Item.
    # ==================================================================
    @property
    def is_magick_location(self):
        return bool(self.db.is_magick_location)

    @is_magick_location.setter
    def is_magick_location(self, value):
        self.db.is_magick_location = bool(value)

    @property
    def magick_words(self):
        return list(self.db.magick_words or [])

    def add_magick_word(self, word_id):
        canonical = canonical_magick_word_id(word_id)
        if canonical is None:
            return False
        words = list(self.db.magick_words or [])
        if canonical not in words:
            words.append(canonical)
            self.db.magick_words = words
        return True

    def remove_magick_word(self, word_id):
        canonical = canonical_magick_word_id(word_id)
        if canonical is None:
            return
        words = list(self.db.magick_words or [])
        if canonical in words:
            words.remove(canonical)
            self.db.magick_words = words

    @property
    def magick_words_command(self):
        """
        Menu-facing view/editor for magick_words, identical in shape
        to Item.magick_words_command - RoomBuildingMenu's "magick
        words" choice binds to this via attr=.
        """
        words = self.db.magick_words or []
        body = "  (none set)" if not words else "\n".join(f"  {w}" for w in words)
        return (
            f"Magick words this location teaches via 'study here':\n{body}\n\n"
            "Type a word id to add it (e.g. 'IGNASH'), or 'remove <word "
            "id>' to delete one. Must be a recognized id from "
            "world/magick_words.py. Remember to also toggle 'is magick "
            "location' on, or 'study here' will treat this room as "
            "non-magical regardless of this list."
        )

    @magick_words_command.setter
    def magick_words_command(self, value):
        text = str(value).strip()
        if not text:
            return
        parts = text.split()
        if parts[0].lower() == "remove" and len(parts) >= 2:
            self.remove_magick_word(parts[1])
            return
        self.add_magick_word(parts[0])
