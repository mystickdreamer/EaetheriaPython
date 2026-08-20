"""
oedit - rewritten object editor (Item / Weapon / Armor / Altar / Key)

Replaces the item-editing half of the old @objedit, which was built on
Evennia's `evennia.contrib.base_systems.building_menu` contrib (see
world/building_menus.py: _ObjEditMenu and its Item/Weapon/Armor/Altar/
Key subclasses - left in place but unused by any command as of this
rewrite; RoomBuildingMenu/ExitBuildingMenu there are unrelated and
still power @redit/doedit). That implementation was never smoke-tested
against a live install, had a real bug (`q` getting swallowed by the
contrib's keys_go_back), a leftover debug print, and - worst - handled
"1. Type" by closing the whole menu and instantiating a brand new
BuildingMenu subclass for the new typeclass.

This is a fresh EvMenu (evennia.utils.evmenu), same pattern as
world/spell_menu.py: plain node functions, an in-memory draft that
nothing commits until "S", and typeclass switching that just updates
the draft and re-renders - no reopening.

Caveat, same as spell_menu.py and building_menus.py before it: written
against Evennia's documented EvMenu contract without a live install to
confirm against. Test with `evennia reload` + `oedit #<dbref>`.

--------------------------------------------------------------------
Draft shape
--------------------------------------------------------------------

Evennia typeclassed objects are DB rows - there's no cheap in-memory
copy of one to edit against. So the "draft" is a plain dict instead,
stashed on caller.ndb for the duration of the session:

    caller.ndb.oedit_obj = <the real object being edited>
    caller.ndb.oedit_draft = {
        "typeclass": "weapon",       # a key into world.object_schema.OBJEDIT_TYPES
        "values": {field_name: value, ...},
    }

Every node reads/writes draft["values"] only. Field values are parsed/
coerced by _coerce() below at entry time (so the draft only ever holds
clean values, e.g. a real bool for a BOOLEAN field) - see _coerce()'s
docstring for why this doesn't reuse typeclasses.items.Item's own
validated properties.

"S" (node_confirm_save) diffs draft["values"] against the object's
current field values, shows the diff, and on "y" applies it: swaps
typeclass first if it changed (via swap_typeclass(), same call
Object.editor_type's setter in typeclasses/objects.py already uses),
then writes every field in the draft onto the object.

"Q" (node_confirm_quit) does the same diff just to decide whether
there's anything to lose; a clean draft closes immediately.

--------------------------------------------------------------------
A note on raw_string
--------------------------------------------------------------------

EvMenu calls every node as node(caller, raw_string, **kwargs), where
raw_string is whatever text the user typed that led here - even on a
numbered-menu-option arrival (raw_string would be "3", "s", etc, NOT
""). So nodes below never use "is raw_string empty?" to decide "did I
just arrive here, or is the user answering a free-text prompt?" -
that's unreliable. Instead, free-text nodes (node_edit_field,
node_edit_bonuses, node_edit_magick_words, node_choose_typeclass) take
an explicit `apply` kwarg that's only ever set to True by their own
"_default" catch-all option - never by a numbered menu option - so it
reliably distinguishes "show the prompt" from "parse what they typed".
Save/Quit avoid the ambiguity entirely by using single-purpose action
nodes (node_do_save, node_do_quit_discard) that don't branch on
raw_string at all.
"""

from world.object_schema import (
    OBJECT_SCHEMAS,
    OBJEDIT_TYPES,
    ITEM_SCHEMA,
    KEY_SCHEMA,
    FieldType,
    get_schema,
)


# ==========================================================================
# Small helpers
# ==========================================================================

_INVALID = object()  # sentinel: user's input didn't parse for this field


def _common_and_typeclass_fields(tc_slug):
    """
    Split the fields relevant to `tc_slug` (an OBJEDIT_TYPES key) into
    (common_fields, typeclass_fields), matching the "GENERAL" /
    "TYPECLASS: X" menu sections.

    Key isn't an Item subclass (see KEY_SCHEMA's own comment in
    world/object_schema.py) so it gets no common-fields section, just
    its own small schema. Every other type shares ITEM_SCHEMA as the
    common section, plus whatever fields that type's own schema adds
    locally (WEAPON_SCHEMA.fields is just weapon_type/stamina_cost,
    not the inherited ones get_fields() would also return - that's
    exactly the split we want here).
    """

    if tc_slug == "key":
        return [], KEY_SCHEMA.get_fields()

    schema = OBJECT_SCHEMAS[tc_slug]
    common = ITEM_SCHEMA.get_fields()
    typeclass_fields = [] if tc_slug == "item" else schema.fields
    return common, typeclass_fields


def _all_fields_for(tc_slug):
    common, typeclass_fields = _common_and_typeclass_fields(tc_slug)
    return common + typeclass_fields


def _tc_slug_for(obj):
    schema = get_schema(obj)
    return schema.name if schema else "item"


def _find_field(draft, field_name):
    for field in _all_fields_for(draft["typeclass"]):
        if field.name == field_name:
            return field
    return None


def _build_draft(obj):
    """Seed a fresh draft dict from the real object's current values."""

    tc_slug = _tc_slug_for(obj)
    values = {}

    for field in _all_fields_for(tc_slug):
        if field.field_type == FieldType.STAT_BONUSES:
            values[field.name] = dict(field.get_value(obj) or {})
        elif field.name == "magick_words":
            values[field.name] = list(field.get_value(obj) or [])
        else:
            values[field.name] = field.get_value(obj)

    return {"typeclass": tc_slug, "values": values}


def _draft_value(draft, field):
    if field.name not in draft["values"]:
        # Field wasn't relevant when the draft was built (e.g. the
        # typeclass was just switched to something that exposes it
        # for the first time) - seed it from the schema default.
        draft["values"][field.name] = field.default
    return draft["values"][field.name]


def _coerce(field, raw_text):
    """
    Parse `raw_text` against `field`'s type. Returns the parsed value,
    or _INVALID if it doesn't parse.

    This intentionally does NOT call the object's own validated
    property setters (typeclasses/items.py's _bool_property/
    _int_property/etc.) - those write straight to a live object's
    .db, and the whole point of the draft is that nothing touches the
    real object until Save. So the coercion rules are re-implemented
    here, matching those setters' behavior (case-insensitive
    true/false words, non-negative numbers, case-insensitive choice
    matching) closely enough that a value that would have been
    accepted there is accepted here too.
    """

    text = raw_text.strip()

    if field.field_type == FieldType.TEXT:
        return text

    if field.field_type == FieldType.BOOLEAN:
        low = text.lower()
        if low in ("true", "yes", "y", "on", "1"):
            return True
        if low in ("false", "no", "n", "off", "0"):
            return False
        return _INVALID

    if field.field_type == FieldType.INTEGER:
        try:
            return max(0, int(text))
        except ValueError:
            return _INVALID

    if field.field_type == FieldType.FLOAT:
        try:
            return max(0.0, float(text))
        except ValueError:
            return _INVALID

    if field.field_type == FieldType.CHOICE:
        if text.lower() in ("none", "-", "clear", ""):
            return None
        for choice in field.choices:
            if text.lower() == str(choice).lower():
                return choice
        return _INVALID

    # STAT_BONUSES and the magick_words list have their own dedicated
    # nodes below and never go through generic _coerce().
    return _INVALID


def _display_value(draft, field):
    value = _draft_value(draft, field)
    if field.field_type == FieldType.STAT_BONUSES:
        if not value:
            return "(none set)"
        return ", ".join(f"{k} {v:+d}" for k, v in sorted(value.items()))
    if field.name == "magick_words":
        return ", ".join(value) if value else "(none set)"
    if value is None or value == "":
        return "(not set)"
    return str(value)


def _real_value(obj, field):
    """Current value on the real object, for the save-time diff."""
    if field.field_type == FieldType.STAT_BONUSES:
        return dict(field.get_value(obj) or {})
    if field.name == "magick_words":
        return list(field.get_value(obj) or [])
    return field.get_value(obj)


def _diff(caller):
    """
    (typeclass_changed, changes) where changes is a list of
    (field, old_value, new_value) for every field whose draft value
    differs from the real object's current value. Used by both Save
    and Quit.
    """

    obj = caller.ndb.oedit_obj
    draft = caller.ndb.oedit_draft

    typeclass_changed = draft["typeclass"] != _tc_slug_for(obj)

    changes = []
    for field in _all_fields_for(draft["typeclass"]):
        old = field.default if typeclass_changed else _real_value(obj, field)
        new = _draft_value(draft, field)
        if old != new:
            changes.append((field, old, new))

    return typeclass_changed, changes


# ==========================================================================
# Entry point
# ==========================================================================

def start_oedit(caller, obj):
    """Called by commands/object_builder.py's CmdOEdit."""

    from evennia.utils.evmenu import EvMenu

    caller.ndb.oedit_obj = obj
    caller.ndb.oedit_draft = _build_draft(obj)

    EvMenu(
        caller,
        "world.oedit_menu",
        startnode="node_main",
        cmd_on_exit=_cleanup,
    )


def _cleanup(caller, menu):
    caller.ndb.oedit_obj = None
    caller.ndb.oedit_draft = None


# ==========================================================================
# Main menu
# ==========================================================================

def node_main(caller, raw_string="", **kwargs):
    obj = caller.ndb.oedit_obj
    draft = caller.ndb.oedit_draft
    common, typeclass_fields = _common_and_typeclass_fields(draft["typeclass"])
    tc_label = OBJECT_SCHEMAS[draft["typeclass"]].label

    lines = [
        "=" * 60,
        "OBJECT EDITOR".center(60),
        "=" * 60,
        "",
        f"Object:    {obj.key} ({obj.dbref})",
        f"Typeclass: {tc_label}",
    ]

    options = [
        {"key": "1", "desc": "Typeclass", "goto": ("node_choose_typeclass", {})},
    ]

    idx = 2

    if common:
        lines.append("")
        lines.append("------------------- GENERAL " + "-" * 31)
        for field in common:
            lines.append(f" {idx}. {field.label}: {_display_value(draft, field)}")
            options.append(_field_option(str(idx), field))
            idx += 1

    if typeclass_fields:
        lines.append("")
        lines.append(f"---------------- TYPECLASS: {tc_label.upper()} " + "-" * 10)
        for field in typeclass_fields:
            lines.append(f" {idx}. {field.label}: {_display_value(draft, field)}")
            options.append(_field_option(str(idx), field))
            idx += 1

    lines.append("")
    lines.append("-" * 60)
    lines.append(" S. Save")
    lines.append(" Q. Quit")
    lines.append("=" * 60)

    options.append({"key": "s", "desc": "Save", "goto": ("node_confirm_save", {})})
    options.append({"key": "q", "desc": "Quit", "goto": ("node_confirm_quit", {})})

    return "\n".join(lines), options


def _field_option(key, field):
    if field.field_type == FieldType.STAT_BONUSES:
        goto = ("node_edit_bonuses", {})
    elif field.name == "magick_words":
        goto = ("node_edit_magick_words", {})
    else:
        goto = ("node_edit_field", {"field_name": field.name})
    return {"key": key, "desc": field.label, "goto": goto}


# ==========================================================================
# Generic single-value field editor (TEXT / INTEGER / FLOAT / BOOLEAN / CHOICE)
# ==========================================================================

def node_edit_field(caller, raw_string="", **kwargs):
    draft = caller.ndb.oedit_draft
    field_name = kwargs.get("field_name")
    field = _find_field(draft, field_name)

    if field is None:
        # Stale option from before a typeclass switch dropped this
        # field - just bounce back to the main menu.
        return node_main(caller, "")

    if not kwargs.get("apply"):
        return _field_prompt(field, field_name)

    value = _coerce(field, raw_string)
    if value is _INVALID:
        text, options = _field_prompt(field, field_name)
        text = f"|rDidn't understand '{raw_string.strip()}' for {field.label}.|n\n\n" + text
        return text, options

    draft["values"][field_name] = value
    return node_main(caller, "")


def _field_prompt(field, field_name):
    text = (
        f"|c{field.label}|n\n"
        f"{field.description}\n\n"
        "Enter a new value, or '@' to cancel:"
    )
    if field.field_type == FieldType.CHOICE:
        text += f"\n\nChoices: {', '.join(str(c) for c in field.choices)}"
        text += "\n(or 'none' to clear)"
    options = [
        {"key": "@", "desc": "Cancel", "goto": ("node_main", {})},
        {"key": "_default", "goto": ("node_edit_field", {"field_name": field_name, "apply": True})},
    ]
    return text, options


# ==========================================================================
# Stat/Skill Bonuses editor
# ==========================================================================

def node_edit_bonuses(caller, raw_string="", **kwargs):
    from world.skills import ALL_SKILLS
    from typeclasses.items import EQUIP_STATS

    draft = caller.ndb.oedit_draft
    field = _find_field(draft, "stat_bonuses")
    bonuses = _draft_value(draft, field)

    if kwargs.get("apply"):
        text = raw_string.strip()
        low = text.lower()
        parts = text.split()
        if low.startswith("remove ") and len(parts) >= 2:
            name = _resolve_name(" ".join(parts[1:]), ALL_SKILLS + EQUIP_STATS)
            if name:
                bonuses.pop(name, None)
        elif len(parts) >= 2:
            *name_parts, amount_text = parts
            name = _resolve_name(" ".join(name_parts), ALL_SKILLS + EQUIP_STATS)
            try:
                amount = int(amount_text)
            except ValueError:
                name = None
            if name:
                bonuses[name] = amount
        draft["values"]["stat_bonuses"] = bonuses

    text = (
        "|cStat/Skill Bonuses|n\n"
        f"{field.description}\n\n"
        f"Current: {_display_value(draft, field)}\n\n"
        "Type '<name> <amount>' to add or update one (e.g. 'OneHand 2'), "
        "'remove <name>' to delete one, or '@' to return."
    )
    options = [
        {"key": "@", "desc": "Back", "goto": ("node_main", {})},
        {"key": "_default", "goto": ("node_edit_bonuses", {"apply": True})},
    ]
    return text, options


def _resolve_name(text, valid_names):
    text = text.strip()
    for candidate in valid_names:
        if text.lower() == str(candidate).lower():
            return candidate
    return None


# ==========================================================================
# Magick Words editor
# ==========================================================================

def node_edit_magick_words(caller, raw_string="", **kwargs):
    from world.magick_words import canonical_word_id

    draft = caller.ndb.oedit_draft
    field = _find_field(draft, "magick_words")
    words = _draft_value(draft, field)

    if kwargs.get("apply"):
        text = raw_string.strip()
        low = text.lower()
        if low.startswith("remove "):
            word_id = canonical_word_id(text[7:].strip())
            if word_id and word_id in words:
                words.remove(word_id)
        else:
            word_id = canonical_word_id(text)
            if word_id and word_id not in words:
                words.append(word_id)
        draft["values"]["magick_words"] = words

    text = (
        "|cMagick Words|n\n"
        f"{field.description}\n\n"
        f"Current: {_display_value(draft, field)}\n\n"
        "Type a word id to add it (e.g. 'IGNASH'), 'remove <word id>' "
        "to delete one, or '@' to return."
    )
    options = [
        {"key": "@", "desc": "Back", "goto": ("node_main", {})},
        {"key": "_default", "goto": ("node_edit_magick_words", {"apply": True})},
    ]
    return text, options


# ==========================================================================
# Typeclass switcher
# ==========================================================================

def node_choose_typeclass(caller, raw_string="", **kwargs):
    draft = caller.ndb.oedit_draft
    slugs = list(OBJEDIT_TYPES)

    if kwargs.get("apply"):
        text = raw_string.strip().lower()
        for i, slug in enumerate(slugs, start=1):
            if text == str(i) or text == slug:
                draft["typeclass"] = slug
                return node_main(caller, "")
        # unrecognized: fall through and re-show the picker

    lines = ["|cTypeclass|n", f"Current: {OBJECT_SCHEMAS[draft['typeclass']].label}", ""]
    for i, slug in enumerate(slugs, start=1):
        lines.append(f" {i}. {OBJECT_SCHEMAS[slug].label}")
    lines.append("")
    lines.append(
        "Select a number or name. This only changes the draft - "
        "nothing is applied until you Save. '@' to cancel."
    )
    options = [
        {"key": "@", "desc": "Cancel", "goto": ("node_main", {})},
        {"key": "_default", "goto": ("node_choose_typeclass", {"apply": True})},
    ]
    return "\n".join(lines), options


# ==========================================================================
# Save
# ==========================================================================

def node_confirm_save(caller, raw_string="", **kwargs):
    obj = caller.ndb.oedit_obj
    typeclass_changed, changes = _diff(caller)

    if not typeclass_changed and not changes:
        caller.msg("Nothing to save.")
        return node_main(caller, "")

    draft = caller.ndb.oedit_draft
    lines = ["|cSave Object|n", f"Object: {obj.key}", "", "Changes:"]
    if typeclass_changed:
        lines.append(f"  Typeclass: {_tc_slug_for(obj)} -> {draft['typeclass']}")
    for field, old, new in changes:
        lines.append(f"  {field.label}: {old} -> {new}")
    lines.append("")
    lines.append("Save these changes? (y/n)")

    options = [
        {"key": "y", "goto": ("node_do_save", {})},
        {"key": ["n", "_default"], "goto": ("node_main", {})},
    ]
    return "\n".join(lines), options


def node_do_save(caller, raw_string="", **kwargs):
    """One-shot: apply the draft and close. Never branches on raw_string."""
    obj = caller.ndb.oedit_obj
    _apply_draft(caller)
    caller.msg(f"|gSaved {obj.key} ({obj.dbref}).|n")
    return None


def _apply_draft(caller):
    obj = caller.ndb.oedit_obj
    draft = caller.ndb.oedit_draft

    if draft["typeclass"] != _tc_slug_for(obj):
        new_cls = OBJEDIT_TYPES[draft["typeclass"]]
        obj.swap_typeclass(
            f"{new_cls.__module__}.{new_cls.__name__}",
            clean_attributes=False,
            run_start_hooks="all",
        )

    for field in _all_fields_for(draft["typeclass"]):
        value = _draft_value(draft, field)
        if field.name == "key":
            obj.key = value
        elif field.name == "desc":
            obj.db.desc = value
        elif field.field_type == FieldType.STAT_BONUSES:
            obj.db.stat_bonuses = dict(value)
        elif field.name == "magick_words":
            obj.db.magick_words = list(value)
        elif hasattr(type(obj), field.name):
            # A real validated property exists (typeclasses/items.py) -
            # use it so its own parsing/clamping applies too.
            try:
                setattr(obj, field.name, value)
            except Exception:
                obj.attributes.add(field.name, value)
        else:
            obj.attributes.add(field.name, value)


# ==========================================================================
# Quit
# ==========================================================================

def node_confirm_quit(caller, raw_string="", **kwargs):
    typeclass_changed, changes = _diff(caller)

    if not typeclass_changed and not changes:
        caller.msg("Editor closed.")
        return None

    text = (
        "You have unsaved changes.\n\n"
        " 1. Save and quit\n"
        " 2. Quit without saving\n"
        " 3. Return to editor\n\n"
        "Choice:"
    )
    options = [
        {"key": "1", "goto": ("node_do_save", {})},
        {"key": "2", "goto": ("node_do_quit_discard", {})},
        {"key": ["3", "_default"], "goto": ("node_main", {})},
    ]
    return text, options


def node_do_quit_discard(caller, raw_string="", **kwargs):
    """One-shot: close without applying the draft."""
    caller.msg("Editor closed. Changes discarded.")
    return None
