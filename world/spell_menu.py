"""
Spell crafting menu (the "altar")

EvMenu node functions driving the `craft spell` command (see
commands/command.py:CmdCraftSpell). Lets a player build up a
SpellRecipe (world/spell_recipe.py) from Magick words they've
actually learned, then either:

  - "Save Recipe" - stash a working draft (Character.db.
    spell_recipe_draft) so `craft spell` can pick it back up later,
    without naming/rolling/persisting it yet.
  - "Name & Create Spell" - name the finished spell, attempt the
    creation roll (Character.perform_spell_check(), same pool the
    design doc uses for casting later: Intelligence + Arcana +
    primary skill), and on success permanently learn it into
    Character.known_spells (world/spell_rules.build_spell_record()).
    On failure the in-progress recipe is left alone so the player can
    try again without losing their work.

Casting (`cast "name"`, ritual mode) is a later stage.

Design principle carried over from the study/vocabulary system: menus
are generated from the character's own knowledge, not hard-coded. A
word category the character has no known words in simply doesn't
appear as an option; if they later study a word in a new category, it
shows up automatically next time they open the altar.

Caveat: like world/building_menus.py, this was written directly
against Evennia's documented EvMenu usage pattern (node functions
returning (text, options), auto-numbered options when "key" is
omitted, and (nodename, kwargs) tuples in "goto" for passing state
between nodes). An earlier version of this menu used "exec" option
callbacks for side effects before a "goto" - live testing showed
selections silently doing nothing (no server-side traceback either),
so that's been replaced throughout with the same "goto" tuple ->
small apply-node -> node_main(caller, "") pattern world/oedit_menu.py
already used successfully. If anything about option handling still
looks off, check evennia/utils/evmenu.py in your own install.
"""

from world.dice import ResultTier
from world.skills import SKILL_CATEGORIES
from world.magick_words import get_word_data
from world.spell_recipe import SpellRecipe, DELIVERY_TYPES
from world.spell_rules import (
    build_spell_record,
    calculate_complexity,
    calculate_creation_difficulty,
    calculate_mana_cost,
    get_known_words_for_category,
    validate_recipe,
)

MAGICK_SKILLS = SKILL_CATEGORIES["Magick Skills"]


# ==========================================================================
# Shared state / rendering helpers
# ==========================================================================

def _recipe(caller):
    """
    Get-or-create the recipe currently under construction.

    Held on .ndb (in-memory, cleared on logout/reload) rather than
    persisted mid-edit - a half-built spell isn't meaningful game
    state. If a saved draft exists (from a previous "Save Recipe"),
    resume from that instead of starting blank.
    """
    recipe = caller.ndb.spell_recipe

    if recipe is not None:
        return recipe

    draft = caller.attributes.get("spell_recipe_draft", default=None)

    if draft:
        try:
            recipe = SpellRecipe.from_dict(draft)
        except (ValueError, TypeError):
            recipe = SpellRecipe()
    else:
        recipe = SpellRecipe()

    caller.ndb.spell_recipe = recipe
    return recipe


def _format_word_list(word_ids):
    if not word_ids:
        return "    (none)"

    lines = []

    for word_id in word_ids:
        data = get_word_data(word_id)

        if not data:
            continue

        lines.append(f"    - {data['word']} ({data['category']})")

    return "\n".join(lines) if lines else "    (none)"


def _render_recipe_box(recipe):
    lines = [
        "|y" + "=" * 60 + "|n",
        f"|w{'CREATE MAGICK':^60}|n",
        "|y" + "=" * 60 + "|n",
        f" Primary Skill: {recipe.primary_skill or '|r(not set)|n'}",
        f" Delivery:      {recipe.delivery or '|r(not set)|n'}",
        "",
        " Components:",
        _format_word_list(recipe.components),
        "",
        " Modifiers:",
        _format_word_list(recipe.modifiers),
        "|y" + "=" * 60 + "|n",
    ]
    return "\n".join(lines)


def _known_word_categories(caller):
    """
    Distinct word categories the character has at least one known
    word in, in first-seen order. Not hard-coded to "concept"/
    "effect" so a future word category shows up automatically.
    """
    caller.ensure_data_integrity()

    categories = []

    for word_id in caller.known_magick_words:
        data = get_word_data(word_id)

        if not data:
            continue

        category = data.get("category")

        if category and category not in categories:
            categories.append(category)

    return categories


# ==========================================================================
# Main node
# ==========================================================================

def node_main(caller, raw_string, **kwargs):
    recipe = _recipe(caller)

    text = (
        _render_recipe_box(recipe)
        + "\n\nBuild your spell from Magick words you've learned "
        "(see 'study' and 'magick words')."
    )

    options = (
        {"desc": "Choose Primary Skill", "goto": "node_choose_skill"},
        {"desc": "Choose Delivery", "goto": "node_choose_delivery"},
        {
            "desc": "Add Magick Word",
            "goto": ("node_add_word_menu", {"mode": "component"}),
        },
        {
            "desc": "Add Modifier",
            "goto": ("node_add_word_menu", {"mode": "modifier"}),
        },
        {"desc": "Remove Component", "goto": "node_remove_component"},
        {"desc": "Remove Modifier", "goto": "node_remove_modifier"},
        {"desc": "Review Spell", "goto": "node_review"},
        {
            "key": ("f", "finish"),
            "desc": "Name & Create Spell",
            "goto": "node_name_spell",
        },
        {
            "key": ("s", "save"),
            "desc": "Save Recipe (draft)",
            "goto": "node_save",
        },
        {
            "key": ("q", "quit", "cancel"),
            "desc": "Cancel",
            "goto": "node_cancel",
        },
    )

    return text, options


# ==========================================================================
# Primary skill
# ==========================================================================

def node_choose_skill(caller, raw_string, **kwargs):
    text = (
        "|wChoose your spell's PRIMARY Magick skill.|n\n"
        "This is fixed for the spell's lifetime and determines your "
        "casting dice pool. Secondary Magick skills can still be woven "
        "in through the words you add, but only the primary skill adds "
        "dice to the roll."
    )

    known_skills = [
        skill for skill in MAGICK_SKILLS if caller.get_skill(skill) > 0
    ]

    if not known_skills:
        caller.msg("|rYou have no ranks in any Magick skill yet.|n")
        return node_main(caller, "")

    options = [
        {
            "desc": f"{skill} (rank {caller.get_skill(skill)})",
            "goto": ("node_apply_skill", {"skill": skill}),
        }
        for skill in known_skills
    ]
    options.append(
        {"key": ("q", "back"), "desc": "Back without changing", "goto": "node_main"}
    )

    return text, options


def node_apply_skill(caller, raw_string="", **kwargs):
    """
    Applies the choice made in node_choose_skill, then falls through
    to node_main. Not reached via an "exec" option callback - that
    convention turned out not to reliably fire in practice (see the
    "F. Finish & Name Spell" flow's naming node for the same "goto"-
    carries-the-kwargs pattern, and world/oedit_menu.py's node_edit_
    field for the precedent this follows).
    """
    skill = kwargs.get("skill")
    if skill:
        _recipe(caller).primary_skill = skill
    return node_main(caller, "")


# ==========================================================================
# Delivery / target
# ==========================================================================

def node_choose_delivery(caller, raw_string, **kwargs):
    text = (
        "|wChoose the spell's Delivery/Target type.|n\n"
        "Self only affects you. Touch requires melee range. Projectile "
        "can be thrown to melee/pole/missile range. Object targets a "
        "held or nearby item. Room affects everyone and everything in "
        "the room you're standing in - the way to create wards, light, "
        "illusions, or other non-combat effects."
    )

    options = [
        {
            "desc": delivery,
            "goto": ("node_apply_delivery", {"delivery": delivery}),
        }
        for delivery in DELIVERY_TYPES
    ]
    options.append(
        {"key": ("q", "back"), "desc": "Back without changing", "goto": "node_main"}
    )

    return text, options


def node_apply_delivery(caller, raw_string="", **kwargs):
    delivery = kwargs.get("delivery")
    if delivery:
        _recipe(caller).delivery = delivery
    return node_main(caller, "")


# ==========================================================================
# Adding words / modifiers
# ==========================================================================

def node_add_word_menu(caller, raw_string, **kwargs):
    mode = kwargs.get("mode", "component")
    label = "Modifier" if mode == "modifier" else "Magick Word"

    categories = _known_word_categories(caller)

    if not categories:
        caller.msg(
            "|rYou don't know any Magick words yet - 'study' something "
            "magical to learn some.|n"
        )
        return node_main(caller, "")

    text = f"|wAdd {label}|n - choose a category of known words."

    options = [
        {
            "desc": category.title(),
            "goto": ("node_add_word_pick", {"mode": mode, "category": category}),
        }
        for category in categories
    ]
    options.append({"key": ("q", "back"), "desc": "Back", "goto": "node_main"})

    return text, options


def node_add_word_pick(caller, raw_string, **kwargs):
    mode = kwargs.get("mode", "component")
    category = kwargs.get("category", "")

    words = get_known_words_for_category(caller, category)

    if not words:
        caller.msg(f"You don't know any {category} words.")
        return node_main(caller, "")

    text = f"|wChoose a {category} word to add.|n"

    options = []

    for word_id in words:
        data = get_word_data(word_id)
        options.append(
            {
                "desc": f"{data['word']} - {data['meaning']} |c[{data['skill']}]|n",
                "goto": ("node_apply_add_word", {"word_id": word_id, "mode": mode}),
            }
        )

    options.append({"key": ("q", "back"), "desc": "Back", "goto": "node_main"})

    return text, options


def node_apply_add_word(caller, raw_string="", **kwargs):
    word_id = kwargs.get("word_id")
    mode = kwargs.get("mode", "component")

    recipe = _recipe(caller)

    try:
        if mode == "modifier":
            recipe.add_modifier(word_id)
        else:
            recipe.add_component(word_id)
    except ValueError as err:
        caller.msg(str(err))

    return node_main(caller, "")


# ==========================================================================
# Removing words / modifiers
# ==========================================================================

def _node_remove(caller, list_name):
    recipe = _recipe(caller)
    word_ids = getattr(recipe, list_name)

    if not word_ids:
        caller.msg(f"There are no {list_name} to remove.")
        return node_main(caller, "")

    singular = list_name[:-1]
    text = f"|wRemove which {singular}?|n"

    options = []

    for word_id in word_ids:
        data = get_word_data(word_id)
        label = data["word"] if data else word_id
        options.append(
            {
                "desc": label,
                "goto": (
                    "node_apply_remove_word",
                    {"word_id": word_id, "list_name": list_name},
                ),
            }
        )

    options.append({"key": ("q", "back"), "desc": "Back", "goto": "node_main"})

    return text, options


def node_apply_remove_word(caller, raw_string="", **kwargs):
    word_id = kwargs.get("word_id")
    list_name = kwargs.get("list_name")

    recipe = _recipe(caller)

    if list_name == "modifiers":
        recipe.remove_modifier(word_id)
    else:
        recipe.remove_component(word_id)

    return node_main(caller, "")


def node_remove_component(caller, raw_string, **kwargs):
    return _node_remove(caller, "components")


def node_remove_modifier(caller, raw_string, **kwargs):
    return _node_remove(caller, "modifiers")


# ==========================================================================
# Review
# ==========================================================================

def node_review(caller, raw_string, **kwargs):
    recipe = _recipe(caller)
    result = validate_recipe(recipe, caller)

    lines = [_render_recipe_box(recipe), ""]

    lines.append(f" Complexity:          {calculate_complexity(recipe)}")
    lines.append(
        f" Creation difficulty: {calculate_creation_difficulty(recipe)} successes"
    )
    lines.append(f" Est. mana cost:      {calculate_mana_cost(recipe)}")
    lines.append("")

    if result.valid:
        lines.append("|gThis recipe is currently valid.|n")
    else:
        lines.append("|rThis recipe is not yet valid:|n")
        for error in result.errors:
            lines.append(f"  |r- {error}|n")

    for warning in result.warnings:
        lines.append(f"  |y- {warning}|n")

    text = "\n".join(lines)
    options = {"key": ("q", "back", ""), "desc": "Back", "goto": "node_main"}

    return text, options


# ==========================================================================
# Naming / creation roll / persistence
# ==========================================================================

def node_name_spell(caller, raw_string, **kwargs):
    """
    Free-text name entry, using the "_default" catch-all pattern (see
    world/oedit_menu.py for the same convention): the first visit
    (no "apply" kwarg) just shows the prompt, the "_default" option
    re-enters this same node with apply=True so raw_string is treated
    as the typed name.
    """
    recipe = _recipe(caller)
    result = validate_recipe(recipe, caller)

    if not result.valid:
        lines = ["|rThis recipe isn't ready to name/create yet:|n"]
        for error in result.errors:
            lines.append(f"  - {error}")
        caller.msg("\n".join(lines))
        return node_main(caller, "")

    if not kwargs.get("apply"):
        text = "|wName your spell|n (or '@' to cancel):"
        options = (
            {"key": "@", "desc": "Cancel", "goto": "node_main"},
            {"key": "_default", "goto": ("node_name_spell", {"apply": True})},
        )
        return text, options

    name = raw_string.strip()

    if not name:
        caller.msg("|rA spell needs a name.|n")
        return node_name_spell(caller, "", apply=False)

    if caller.knows_spell(name):
        caller.msg(
            f"|rYou already know a spell called '{name}'. Choose a "
            "different name.|n"
        )
        return node_name_spell(caller, "", apply=False)

    return node_confirm_creation(caller, "", name=name)


def node_confirm_creation(caller, raw_string, **kwargs):
    recipe = _recipe(caller)
    name = kwargs.get("name", "")

    required = calculate_creation_difficulty(recipe)
    mana_cost = calculate_mana_cost(recipe)

    text = (
        f"|wCreate '{name}'?|n\n\n"
        f" Primary skill:  {recipe.primary_skill}\n"
        f" Complexity:     {calculate_complexity(recipe)}\n"
        f" Roll needed:    Intelligence + Arcana + {recipe.primary_skill} "
        f"vs. {required} successes\n"
        f" Mana cost (once learned): {mana_cost}\n\n"
        "Attempting the roll does not consume the draft on failure - "
        "you can try again."
    )

    options = (
        {
            "key": ("y", "yes"),
            "desc": "Attempt the creation roll",
            "goto": ("node_creation_roll", {"name": name}),
        },
        {"key": ("n", "no", "@"), "desc": "Back", "goto": "node_main"},
    )

    return text, options


def node_creation_roll(caller, raw_string, **kwargs):
    recipe = _recipe(caller)
    name = kwargs.get("name", "")

    result = validate_recipe(recipe, caller)

    if not result.valid:
        # State changed since confirmation (word forgotten somehow,
        # etc.) - bounce out rather than roll against a bad recipe.
        caller.msg("|rThis recipe is no longer valid - check Review Spell.|n")
        return node_main(caller, "")

    required = calculate_creation_difficulty(recipe)

    roll = caller.perform_spell_check(recipe.primary_skill, required)

    if roll.tier < ResultTier.SUCCESS:
        caller.msg(
            f"|rThe working falls apart before it takes shape. "
            f"'{name}' is not yet created - your recipe is still here "
            "if you want to try again.|n"
        )
        return node_main(caller, "")

    record = build_spell_record(recipe, name)
    caller.learn_spell(record)

    caller.attributes.remove("spell_recipe_draft")
    caller.ndb.spell_recipe = None

    caller.msg(
        f"|gSuccess! You have created and learned the spell "
        f"'{record['name']}'.|n\n"
        f"Casting difficulty: {record['casting_difficulty']} successes  "
        f"Mana cost: {record['mana_cost']}"
    )
    return None, None


# ==========================================================================
# Save / cancel (end nodes)
# ==========================================================================

def node_save(caller, raw_string, **kwargs):
    recipe = _recipe(caller)
    result = validate_recipe(recipe, caller)

    if not result.valid:
        lines = ["|rThis recipe isn't ready to save yet:|n"]
        for error in result.errors:
            lines.append(f"  - {error}")
        caller.msg("\n".join(lines))
        return node_main(caller, "")

    caller.attributes.add("spell_recipe_draft", recipe.to_dict())
    caller.msg(
        "|gDraft recipe saved.|n Naming the spell, the creation roll, and "
        "permanently learning it aren't wired up yet - for now your draft "
        "is held in progress, and 'craft spell' will pick it back up next "
        "time you open the altar."
    )
    return None, None


def node_cancel(caller, raw_string, **kwargs):
    caller.ndb.spell_recipe = None
    caller.msg("You step back from the altar, your working recipe discarded.")
    return None, None
