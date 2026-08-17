"""
Immortal / staff tier data

Flat registry describing what each Evennia permission tier means for
this game and what staff-facing commands become available at each
level. Mirrors the shape of world/races.py and world/perks.py: plain
data plus small accessor functions, not a database model, since this
doesn't need runtime mutability.

Evennia's default PERMISSION_HIERARCHY (unset in server/conf/settings.py,
so the Evennia default applies) is, low to high:

    Guest < Player < Helper < Builder < Admin < Developer

"Immortal" isn't an Evennia permission string of its own - it's used
here (and by CmdImm in commands/command.py) as shorthand for "Builder
or higher", matching every other staff-only command already in the
codebase (@objedit, @olist, @redit, itemedit, doedit all lock at
perm(Builder)).

NOTE on bamf messages: DEFAULT_BAMF_IN/DEFAULT_BAMF_OUT are used both as
the character's starting values (typeclasses/characters.py) and as
the fallback when a player resets with 'imm bamfin reset' /
'imm bamfout reset'. Actual display happens automatically whenever
Evennia's default teleport command (@tel/teleport) moves a Character
- see Character.announce_move_from()/announce_move_to() in
typeclasses/characters.py, which hook move_type="teleport".
"""

# Ordered low -> high. Must match Evennia's default PERMISSION_HIERARCHY
# (server/conf/settings.py doesn't override it, so this is it).
PERMISSION_ORDER = ["Guest", "Player", "Helper", "Builder", "Admin", "Developer"]

# The minimum tier CmdImm (and every other staff-only command in this
# codebase) locks at.
IMMORTAL_MIN_PERM = "Builder"

DEFAULT_BAMF_IN = "{name} arrives in a swirl of light."
DEFAULT_BAMF_OUT = "{name} vanishes in a swirl of light."

# What each tier unlocks, on top of everything the tier below it has.
# `commands` only lists commands newly available *at* that tier - use
# commands_available_at() below to get the cumulative list a character
# actually has access to.
TIER_INFO = {
    "Builder": {
        "description": (
            "World-building access: create and edit rooms, items, and exits."
        ),
        "commands": ["@objedit", "@olist", "@redit", "itemedit", "doedit"],
    },
    "Admin": {
        "description": (
            "Player and world administration, on top of full Builder access."
        ),
        "commands": [],
    },
    "Developer": {
        "description": (
            "Full server access (in-game equivalent of superuser), on top "
            "of full Admin access."
        ),
        "commands": [],
    },
}


def get_tier_info(perm_name):
    """Raw per-tier data (description + commands newly unlocked there)."""
    return TIER_INFO.get(perm_name, {"description": "", "commands": []})


def commands_available_at(perm_name):
    """
    Cumulative list of staff commands available at and below the given
    tier - e.g. a Developer sees everything an Admin and a Builder can
    use too, not just Developer-only commands. Returns [] for a tier
    below Builder or not recognized.
    """
    if perm_name not in PERMISSION_ORDER:
        return []
    idx = PERMISSION_ORDER.index(perm_name)
    commands = []
    seen = set()
    for tier in PERMISSION_ORDER[: idx + 1]:
        for cmd in TIER_INFO.get(tier, {}).get("commands", []):
            if cmd not in seen:
                seen.add(cmd)
                commands.append(cmd)
    return commands


def highest_permission(permission_strings):
    """
    Given an iterable of permission strings (e.g. from
    `character.permissions.all()` / `account.permissions.all()`),
    return the highest one found in PERMISSION_ORDER, or None if none
    of them match a known tier.
    """
    best = None
    best_idx = -1
    for perm in permission_strings:
        if not perm:
            continue
        # Evennia permission checks are case-insensitive; normalize to
        # the canonical capitalized form used in PERMISSION_ORDER.
        normalized = perm.strip().capitalize()
        if normalized in PERMISSION_ORDER:
            idx = PERMISSION_ORDER.index(normalized)
            if idx > best_idx:
                best_idx = idx
                best = normalized
    return best


def is_immortal(perm_name):
    """True if the given tier is Builder or higher."""
    if perm_name not in PERMISSION_ORDER:
        return False
    return PERMISSION_ORDER.index(perm_name) >= PERMISSION_ORDER.index(IMMORTAL_MIN_PERM)
