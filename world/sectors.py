"""
Sectors

Terrain classification for rooms - a single sector per Room, picked
from a fixed set below, mirroring the classic Diku/Rom SECT_* terrain
types. As with world/room_flags.py, this project doesn't borrow any
code from that lineage, just the names/meanings.

Mirrors the shape of world/races.py: plain data + small accessor
functions, not a database model (see design doc §2.4).

Kept to display/classification data only for now - no movement-speed
modifiers, no swim/fly-requirement enforcement, no encumbrance
interaction. Same "don't invent mechanics the game doesn't use yet"
restraint as ROOM_SCHEMA in world/object_schema.py and
world/room_flags.py. Character already has can_fly (typeclasses/
characters.py, race-derived) which WATER_SWIM/WATER_NOSWIM/FLYING/
UNDERWATER would eventually gate against, once movement actually
checks sector - not wired up yet.

SECT_INSIDE is the default sector for any newly-created Room.
"""

SECT_INSIDE = "INSIDE"
SECT_CITY = "CITY"
SECT_FIELD = "FIELD"
SECT_FOREST = "FOREST"
SECT_HILLS = "HILLS"
SECT_MOUNTAIN = "MOUNTAIN"
SECT_WATER_SWIM = "WATER_SWIM"
SECT_WATER_NOSWIM = "WATER_NOSWIM"
SECT_FLYING = "FLYING"
SECT_UNDERWATER = "UNDERWATER"

DEFAULT_SECTOR = SECT_INSIDE

SECTORS = {
    SECT_INSIDE: {
        "display_name": "Inside",
        "description": "An interior space - a building, cave, or other enclosed area.",
    },
    SECT_CITY: {
        "display_name": "City",
        "description": "A paved/settled area - streets, plazas, town squares.",
    },
    SECT_FIELD: {
        "display_name": "Field",
        "description": "Open grassland or farmland.",
    },
    SECT_FOREST: {
        "display_name": "Forest",
        "description": "Wooded terrain.",
    },
    SECT_HILLS: {
        "display_name": "Hills",
        "description": "Rolling, uneven high ground.",
    },
    SECT_MOUNTAIN: {
        "display_name": "Mountain",
        "description": "Steep, rugged high terrain.",
    },
    SECT_WATER_SWIM: {
        "display_name": "Water (Swim)",
        "description": "Open water shallow/calm enough to cross without a boat.",
    },
    SECT_WATER_NOSWIM: {
        "display_name": "Water (No Swim)",
        "description": "Open water that requires a boat or other means to cross.",
    },
    SECT_FLYING: {
        "display_name": "Flying",
        "description": "Open air - only reachable by a flying character.",
    },
    SECT_UNDERWATER: {
        "display_name": "Underwater",
        "description": "Submerged terrain below the water's surface.",
    },
}

# Preserves the declaration order above for anything that needs a
# stable display order (e.g. a future @redit sector picker).
ALL_SECTORS = list(SECTORS.keys())


def get_sector_data(sector_id):
    """Return the sector dict for a given id, falling back to the default sector."""
    return SECTORS.get(sector_id, SECTORS[DEFAULT_SECTOR])


def sector_display_name(sector_id):
    return get_sector_data(sector_id)["display_name"]


def is_valid_sector(sector_id):
    return sector_id in SECTORS
