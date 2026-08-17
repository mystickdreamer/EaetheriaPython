"""
Room flags

Flat registry of boolean flags a builder can toggle on a Room via
`@redit` (see world/building_menus.RoomBuildingMenu and
Room.toggle_flag() in typeclasses/rooms.py). Named/scoped after the
classic Diku/Rom ROOM_* flag set - this project doesn't borrow any
code from that lineage, just the names/meanings, since they're a
well-understood baseline for what a room flag even is.

Mirrors the shape of world/races.py: plain data + small accessor
functions, not a database model (see design doc §2.4).

This registry defines what a flag IS (id, display name, description),
not what it DOES. Actually enforcing a flag's meaning - NOMOB blocking
NPC spawns, PEACEFUL blocking combat, NOMAGIC blocking spellcasting,
TUNNEL capping occupancy - is left to whatever system reads
Room.has_flag() once that system exists (NPCs/combat/magick are all
"Not started" per the design doc's current-state table). Same
"don't invent mechanics the game doesn't use yet" restraint as
ROOM_SCHEMA in world/object_schema.py.

DARK is the one exception worth flagging: Character.vision (typeclasses/
characters.py) already exists (VISION_NORMAL/LOWLIGHT/DARKVISION,
race-derived), so a DARK room could plausibly gate what `look` shows
today without waiting on a new system. Left unenforced for now anyway,
to keep this pass to "the flag exists and is toggleable" - wiring it
into return_appearance is a small, separate follow-up once you want it.

ROOM_WORLDMAP is deliberately not included yet - flagged as an open
question, not forgotten.
"""

FLAG_DARK = "DARK"
FLAG_NOMOB = "NOMOB"
FLAG_INDOORS = "INDOORS"
FLAG_PEACEFUL = "PEACEFUL"
FLAG_NOMAGIC = "NOMAGIC"
FLAG_TUNNEL = "TUNNEL"
FLAG_GODROOM = "GODROOM"
FLAG_HOUSE = "HOUSE"
FLAG_ATRIUM = "ATRIUM"

ROOM_FLAGS = {
    FLAG_DARK: {
        "display_name": "Dark",
        "description": (
            "Room is dark - characters without darkvision/a light source "
            "can't see its contents/exits on look. (Not yet enforced - "
            "see module docstring.)"
        ),
    },
    FLAG_NOMOB: {
        "display_name": "No Mob",
        "description": "NPCs cannot be spawned into or wander into this room.",
    },
    FLAG_INDOORS: {
        "display_name": "Indoors",
        "description": (
            "Room is sheltered - weather/outdoor effects (once "
            "implemented) don't apply here."
        ),
    },
    FLAG_PEACEFUL: {
        "display_name": "Peaceful",
        "description": "Combat and other hostile actions can't be initiated here.",
    },
    FLAG_NOMAGIC: {
        "display_name": "No Magic",
        "description": "Spellcasting/magick use is suppressed in this room.",
    },
    FLAG_TUNNEL: {
        "display_name": "Tunnel",
        "description": "Only one character may occupy this room at a time.",
    },
    FLAG_GODROOM: {
        "display_name": "God Room",
        "description": "Restricted to Immortal (Builder+) characters.",
    },
    FLAG_HOUSE: {
        "display_name": "House",
        "description": "Part of a player house/instance rather than the shared world.",
    },
    FLAG_ATRIUM: {
        "display_name": "Atrium",
        "description": "Entryway room for a house - the point new occupants attach to.",
    },
}

# Preserves the declaration order above for anything that needs a
# stable display order (e.g. Room.flags_command in typeclasses/rooms.py).
ALL_ROOM_FLAGS = list(ROOM_FLAGS.keys())


def get_flag_info(flag_id):
    """Return the {display_name, description} dict for a flag id, or None if unknown."""
    return ROOM_FLAGS.get(flag_id)


def flag_display_name(flag_id):
    """Human-readable name for a flag id, falling back to the raw id if unknown."""
    info = ROOM_FLAGS.get(flag_id)
    return info["display_name"] if info else flag_id


def is_valid_flag(flag_id):
    return flag_id in ROOM_FLAGS
