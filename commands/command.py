"""
Commands

Commands describe the input the account can do to the game.

"""

from evennia.commands.command import Command as BaseCommand
from evennia.utils.evmenu import EvMenu

from world.skills import SKILL_CATEGORIES, canonical_skill_name
from world.dice import ResultTier
from world.building_menus import (
    ExitBuildingMenu, ItemBuildingMenu, WeaponBuildingMenu, ArmorBuildingMenu,
)
from typeclasses.exits import LockableExit, VALID_ATTRIBUTES
from typeclasses.items import Item, Weapon, Armor, Altar
from world.skills import ALL_SKILLS
from world import body_parts as body_parts_registry
from world import immortal_data
from world import magick_words as magick_words_registry
from world.languages import canonical_language_name, garble_text

# from evennia import default_cmds


class Command(BaseCommand):
    """
    Base command (you may see this if a child command had no help text defined)

    Note that the class's `__doc__` string is used by Evennia to create the
    automatic help entry for the command, so make sure to document consistently
    here. Without setting one, the parent's docstring will show (like now).

    """

    # Each Command class implements the following methods, called in this order
    # (only func() is actually required):
    #
    #     - at_pre_cmd(): If this returns anything truthy, execution is aborted.
    #     - parse(): Should perform any extra parsing needed on self.args
    #         and store the result on self.
    #     - func(): Performs the actual work.
    #     - at_post_cmd(): Extra actions, often things done after
    #         every command, like prompts.
    #
    pass


# -------------------------------------------------------------
#
# The default commands inherit from
#
#   evennia.commands.default.muxcommand.MuxCommand.
#
# If you want to make sweeping changes to default commands you can
# uncomment this copy of the MuxCommand parent and add
#
#   COMMAND_DEFAULT_CLASS = "commands.command.MuxCommand"
#
# to your settings file. Be warned that the default commands expect
# the functionality implemented in the parse() method, so be
# careful with what you change.
#
# -------------------------------------------------------------

# from evennia.utils import utils
#
#
# class MuxCommand(Command):
#     """
#     This sets up the basis for a MUX command. The idea
#     is that most other Mux-related commands should just
#     inherit from this and don't have to implement much
#     parsing of their own unless they do something particularly
#     advanced.
#
#     Note that the class's __doc__ string (this text) is
#     used by Evennia to create the automatic help entry for
#     the command, so make sure to document consistently here.
#     """
#     def has_perm(self, srcobj):
#         """
#         This is called by the cmdhandler to determine
#         if srcobj is allowed to execute this command.
#         We just show it here for completeness - we
#         are satisfied using the default check in Command.
#         """
#         return super().has_perm(srcobj)
#
#     def at_pre_cmd(self):
#         """
#         This hook is called before self.parse() on all commands
#         """
#         pass
#
#     def at_post_cmd(self):
#         """
#         This hook is called after the command has finished executing
#         (after self.func()).
#         """
#         pass
#
#     def parse(self):
#         """
#         This method is called by the cmdhandler once the command name
#         has been identified. It creates a new set of member variables
#         that can be later accessed from self.func() (see below)
#
#         The following variables are available for our use when entering this
#         method (from the command definition, and assigned on the fly by the
#         cmdhandler):
#            self.key - the name of this command ('look')
#            self.aliases - the aliases of this cmd ('l')
#            self.permissions - permission string for this command
#            self.help_category - overall category of command
#
#            self.caller - the object calling this command
#            self.cmdstring - the actual command name used to call this
#                             (this allows you to know which alias was used,
#                              for example)
#            self.args - the raw input; everything following self.cmdstring.
#            self.cmdset - the cmdset from which this command was picked. Not
#                          often used (useful for commands like 'help' or to
#                          list all available commands etc)
#            self.obj - the object on which this command was defined. It is often
#                          the same as self.caller.
#
#         A MUX command has the following possible syntax:
#
#           name[ with several words][/switch[/switch..]] arg1[,arg2,...] [[=|,] arg[,..]]
#
#         The 'name[ with several words]' part is already dealt with by the
#         cmdhandler at this point, and stored in self.cmdname (we don't use
#         it here). The rest of the command is stored in self.args, which can
#         start with the switch indicator /.
#
#         This parser breaks self.args into its constituents and stores them in the
#         following variables:
#           self.switches = [list of /switches (without the /)]
#           self.raw = This is the raw argument input, including switches
#           self.args = This is re-defined to be everything *except* the switches
#           self.lhs = Everything to the left of = (lhs:'left-hand side'). If
#                      no = is found, this is identical to self.args.
#           self.rhs: Everything to the right of = (rhs:'right-hand side').
#                     If no '=' is found, this is None.
#           self.lhslist - [self.lhs split into a list by comma]
#           self.rhslist - [list of self.rhs split into a list by comma]
#           self.arglist = [list of space-separated args (stripped, including '=' if it exists)]
#
#           All args and list members are stripped of excess whitespace around the
#           strings, but case is preserved.
#         """
#         raw = self.args
#         args = raw.strip()
#
#         # split out switches
#         switches = []
#         if args and len(args) > 1 and args[0] == "/":
#             # we have a switch, or a set of switches. These end with a space.
#             switches = args[1:].split(None, 1)
#             if len(switches) > 1:
#                 switches, args = switches
#                 switches = switches.split('/')
#             else:
#                 args = ""
#                 switches = switches[0].split('/')
#         arglist = [arg.strip() for arg in args.split()]
#
#         # check for arg1, arg2, ... = argA, argB, ... constructs
#         lhs, rhs = args, None
#         lhslist, rhslist = [arg.strip() for arg in args.split(',')], []
#         if args and '=' in args:
#             lhs, rhs = [arg.strip() for arg in args.split('=', 1)]
#             lhslist = [arg.strip() for arg in lhs.split(',')]
#             rhslist = [arg.strip() for arg in rhs.split(',')]
#
#         # save to object properties:
#         self.raw = raw
#         self.switches = switches
#         self.args = args.strip()
#         self.arglist = arglist
#         self.lhs = lhs
#         self.lhslist = lhslist
#         self.rhs = rhs
#         self.rhslist = rhslist
#
#         # if the class has the account_caller property set on itself, we make
#         # sure that self.caller is always the account if possible. We also create
#         # a special property "character" for the puppeted object, if any. This
#         # is convenient for commands defined on the Account only.
#         if hasattr(self, "account_caller") and self.account_caller:
#             if utils.inherits_from(self.caller, "evennia.objects.objects.DefaultObject"):
#                 # caller is an Object/Character
#                 self.character = self.caller
#                 self.caller = self.caller.account
#             elif utils.inherits_from(self.caller, "evennia.accounts.accounts.DefaultAccount"):
#                 # caller was already an Account
#                 self.character = self.caller.get_puppet(self.session)
#             else:
#                 self.character = None



def format_equipment_lines(caller):
    """
    Shared renderer for the worn/wielded-items table - used by both
    `equipment` (standalone) and `sheet` (embedded), so the two never
    drift out of sync with each other.
    """
    lines = []
    equipment = caller.equipment
    for slot_id in caller.equip_slots:
        label = body_parts_registry.slot_display_name(slot_id) + ":"
        item = equipment.get(slot_id)
        if item:
            item_str = f"|w{item.get_display_name(caller)}|n"
        else:
            item_str = "|x(empty)|n"
        lines.append(f"  {label:<14} {item_str}")
    return lines


def format_body_lines(caller):
    """
    Shared renderer for the body-parts/damage table - used by both
    `body` (standalone) and `sheet` (embedded).
    """
    lines = []
    damage = caller.body_part_damage
    body_parts = caller.body_parts

    rows = []
    for part_id in body_parts:
        part_data = body_parts_registry.get_body_part_data(part_id) or {}
        label = part_data.get("display_name", part_id)
        slots = part_data.get("equip_slots", [])
        slot_str = ", ".join(body_parts_registry.slot_display_name(s) for s in slots) or "-"
        rows.append((label, slot_str, part_id))

    label_width = max((len(label) for label, _, _ in rows), default=0)
    slot_width = max((len(slot_str) for _, slot_str, _ in rows), default=0)

    for label, slot_str, part_id in rows:
        dmg = damage.get(part_id, 0)
        disabled = caller.is_body_part_disabled(part_id)
        if disabled:
            status = "|rDISABLED|n"
        elif dmg:
            status = f"|r{dmg} dmg|n"
        else:
            status = "|ghealthy|n"

        lines.append(
            f"  {label:<{label_width}} |x(slots: {slot_str:<{slot_width}})|n  {status}"
        )
    return lines


class CmdSheet(Command):
    """
    View your character's full stats and information.

    Usage:
      sheet
    """

    key = "sheet"
    aliases = ["score", "sh"]
    help_category = "General"

    def func(self):
        """
        Render and display the character sheet.
        """
        caller = self.caller

        # Defensive self-heal: catches characters created before some of
        # these fields existed on the typeclass (at_object_creation only
        # ever runs once, so old objects wouldn't otherwise pick them up).
        if caller.ensure_data_integrity():
            caller.msg("|x(sheet: found and repaired missing character data)|n")

        sheet = []
        sheet.append("|y" + "=" * 78 + "|n")
        sheet.append(f"|w{'CHARACTER SHEET':^78}|n")
        sheet.append("|y" + "=" * 78 + "|n")

        # ----- Identity -----
        race_label = caller.race_data.get("display_name", caller.race)
        display_name = caller.name.capitalize() if caller.name else caller.name
        name_str = f" Name: |w{display_name:<20}|n"
        sex_str = f"Sex: |w{str(caller.sex):<12}|n"
        race_str = f"Race: |w{race_label}|n"
        sheet.append(f"{name_str}{sex_str}{race_str}")

        size_str = f" Size: |w{caller.size_category:<15}|n"
        vision_str = f"Vision: |w{caller.vision:<12}|n"
        sheet.append(f"{size_str}{vision_str}")

        if caller.languages:
            sheet.append(f" Languages: |w{', '.join(caller.languages)}|n")

        sheet.append("|y" + "-" * 78 + "|n")

        # ----- Vitals -----
        sheet.append(
            f" HP: |w{caller.hp}/{caller.max_hp}|n   "
            f"Mana: |w{caller.mana}/{caller.max_mana}|n   "
            f"Stamina: |w{caller.stamina}/{caller.max_stamina}|n"
        )
        sheet.append(
            f" Combat Speed: |w{caller.combat_speed}|n   "
            f"Weight: |w{caller.weight}/{caller.max_weight}|n"
        )
        # xp itself stays a float (see EXPLORATION_XP_REWARD in
        # typeclasses/characters.py) so tiny fractional rewards can
        # accumulate - the sheet just displays the whole-number part.
        # int() truncates rather than rounds, so this never shows a
        # whole point the character can't actually spend yet (e.g.
        # 5.99 displays as 5, not 6).
        sheet.append(f" XP: |w{int(caller.xp)}|n")
        sheet.append("|y" + "-" * 78 + "|n")

        # ----- Attributes (base + any active modifier total) -----
        sheet.append(f"|c{'PHYSICAL':^26}{'MENTAL':^26}{'SOCIAL':^26}|n")

        def fmt_attr(label, attr_name):
            base = getattr(caller, attr_name)
            mod = caller.get_modifier_total(attr_name)
            val = f"{base}+{mod}" if mod else f"{base}"
            return f"  {label:<12} |w{val:<5}|n"

        def format_row(p_attr, p_label, m_attr, m_label, s_attr, s_label):
            return (
                fmt_attr(p_label, p_attr)
                + fmt_attr(m_label, m_attr)
                + fmt_attr(s_label, s_attr)
            )

        sheet.append(format_row("might", "Might", "intelligence", "Intelligence", "charisma", "Charisma"))
        sheet.append(format_row("agility", "Agility", "cunning", "Cunning", "influence", "Influence"))
        sheet.append(format_row("endurance", "Endurance", "willpower", "Willpower", "appearance", "Appearance"))

        sheet.append("|y" + "-" * 78 + "|n")

        # ----- Skills (grouped by category, all skills shown) -----
        skills = caller.attributes.get("skills", default={})
        sheet.append("|c" + f"{'SKILLS':^78}" + "|n")
        for category, category_skills in SKILL_CATEGORIES.items():
            sheet.append(f" |y{category}:|n")
            skill_line = "   "
            for i, name in enumerate(category_skills):
                rank = skills.get(name, 0)
                total = caller.get_skill_total(name)
                val = f"{rank}+{total - rank}" if total != rank else f"{rank}"
                skill_line += f"{name:<14}|w{val:<5}|n"
                if (i + 1) % 3 == 0:
                    sheet.append(skill_line)
                    skill_line = "   "
            if skill_line.strip():
                sheet.append(skill_line)
        sheet.append("|y" + "-" * 78 + "|n")

        # ----- Perks -----
        perks = caller.perks
        if perks:
            perk_str = ", ".join(
                f"{pid} (rank {rank})" if rank > 1 else pid
                for pid, rank in perks.items()
            )
            sheet.append(f" |gPerks:|n {perk_str}")

        # ----- Backgrounds -----
        backgrounds = caller.backgrounds
        if backgrounds:
            sheet.append(f" |gBackgrounds:|n {', '.join(backgrounds.keys())}")

        # ----- Conditions -----
        conditions = caller.conditions
        if conditions:
            cond_str = ", ".join(
                f"{name} ({value})" if value != 1 else name
                for name, value in conditions.items()
            )
            sheet.append(f" |rConditions:|n {cond_str}")

        if perks or backgrounds or conditions:
            sheet.append("|y" + "-" * 78 + "|n")

        # ----- Active modifiers (debug/transparency view) -----
        active_modifiers = caller.active_modifiers
        if active_modifiers:
            sheet.append(" |mActive Modifiers:|n")
            for stat_name, sources in active_modifiers.items():
                total = sum(sources.values())
                source_str = ", ".join(f"{sid}: {val:+d}" for sid, val in sources.items())
                sheet.append(f"   {stat_name:<14} |w{total:+d}|n  ({source_str})")
            sheet.append("|y" + "-" * 78 + "|n")

        # ----- Equipment -----.
        sheet.append("Type EQUIPMENT or EQ to see your equipment." + "|n")
        #sheet.append("|c" + f"{'EQUIPMENT':^78}" + "|n")
        #sheet.extend(format_equipment_lines(caller))
        #sheet.append("|y" + "-" * 78 + "|n")

        # ----- Body -----
        sheet.append("Type BODY to see your body part status." + "|n")
        #sheet.append("|c" + f"{'BODY':^78}" + "|n")
        #sheet.extend(format_body_lines(caller))
        #sheet.append("|y" + "=" * 78 + "|n")

        # ----- Immortal reminder (staff only) -----
        if immortal_data.is_immortal(caller.highest_staff_permission()):
            sheet.append("Type IMM to view immortal information." + "|n")

        caller.msg("\n".join(sheet))


class CmdBody(Command):
    """
    View your character's body parts and any hit-location damage.

    Usage:
      body
    """

    key = "body"
    aliases = ["parts"]
    help_category = "General"

    def func(self):
        caller = self.caller

        lines = []
        lines.append("|y" + "=" * 78 + "|n")
        lines.append(f"|w{'BODY':^78}|n")
        lines.append("|y" + "=" * 78 + "|n")

        lines.extend(format_body_lines(caller))

        lines.append("|y" + "-" * 78 + "|n")
        lines.append(" |xType 'equipment' (or 'eq') to see what you're wearing.|n")
        lines.append("|y" + "=" * 78 + "|n")

        caller.msg("\n".join(lines))


class CmdEquipment(Command):
    """
    View what you're wearing/wielding in each of your equip slots.

    Usage:
      equipment
      eq
    """

    key = "equipment"
    aliases = ["eq"]
    help_category = "General"

    def func(self):
        caller = self.caller

        lines = []
        lines.append("|y" + "=" * 78 + "|n")
        lines.append(f"|w{'EQUIPMENT':^78}|n")
        lines.append("|y" + "=" * 78 + "|n")

        lines.extend(format_equipment_lines(caller))

        lines.append("|y" + "-" * 78 + "|n")
        lines.append(" |xType 'body' to see your body parts.|n")
        lines.append("|y" + "=" * 78 + "|n")

        caller.msg("\n".join(lines))


class CmdImm(Command):
    """
    View and edit your immortal/staff information.

    Usage:
      imm
      imm bamfin <message>
      imm bamfout <message>
      imm bamfin reset
      imm bamfout reset

    Shows your current permission tier, the staff commands that tier
    unlocks, and your bamf-in/bamf-out flavor messages - shown
    automatically to a room whenever you use Evennia's teleport
    command (@tel/teleport) instead of the default arrive/leave text.

    Bamf messages accept {name} as a placeholder for your own display
    name, e.g.:

      imm bamfin *poof* {name} appears in a puff of orange smoke!

    Builder permission or higher is required to use this command at
    all - if you can't see 'imm' in your command list, you don't have
    it.
    """

    key = "imm"
    locks = "cmd:perm(Builder)"
    help_category = "Immortal"

    def func(self):
        caller = self.caller
        args = self.args.strip() if self.args else ""

        if not args:
            self._display(caller)
            return

        parts = args.split(None, 1)
        verb = parts[0].lower()
        rest = parts[1].strip() if len(parts) > 1 else ""

        if verb == "bamfin":
            self._set_bamf(caller, "in", rest)
        elif verb == "bamfout":
            self._set_bamf(caller, "out", rest)
        else:
            caller.msg(
                "Usage: imm | imm bamfin <message> | imm bamfout <message> "
                "| imm bamfin reset | imm bamfout reset"
            )

    def _set_bamf(self, caller, direction, rest):
        default = (
            immortal_data.DEFAULT_BAMF_IN if direction == "in"
            else immortal_data.DEFAULT_BAMF_OUT
        )
        label = "bamf-in" if direction == "in" else "bamf-out"

        if not rest:
            caller.msg(
                f"Set what? Usage: imm bamf{direction} <message>, or "
                f"imm bamf{direction} reset to restore the default."
            )
            return

        if rest.lower() == "reset":
            value = default
        else:
            value = rest

        if direction == "in":
            caller.bamf_in = value
        else:
            caller.bamf_out = value

        caller.msg(f"Your {label} message is now: {value}")

    def _display(self, caller):
        # Defensive self-heal, same pattern as CmdSheet - catches
        # characters created before bamf_in/bamf_out existed.
        if caller.ensure_data_integrity():
            caller.msg("|x(imm: found and repaired missing character data)|n")

        tier = caller.highest_staff_permission()

        lines = []
        lines.append("|y" + "=" * 78 + "|n")
        lines.append(f"|w{'IMMORTAL INFORMATION':^78}|n")
        lines.append("|y" + "=" * 78 + "|n")

        if not tier:
            lines.append(
                " You don't currently hold a recognized staff permission tier."
            )
            lines.append("|y" + "=" * 78 + "|n")
            caller.msg("\n".join(lines))
            return

        tier_info = immortal_data.get_tier_info(tier)
        lines.append(f" Permission tier: |w{tier}|n")
        if tier_info.get("description"):
            lines.append(f" {tier_info['description']}")

        lines.append("|y" + "-" * 78 + "|n")

        commands = immortal_data.commands_available_at(tier)
        lines.append("|c" + f"{'COMMANDS AVAILABLE':^78}" + "|n")
        if commands:
            lines.append(" " + ", ".join(commands))
        else:
            lines.append(" (none registered for this tier yet)")

        lines.append("|y" + "-" * 78 + "|n")

        lines.append("|c" + f"{'BAMF MESSAGES':^78}" + "|n")
        lines.append(f" Bamf-in:  |w{caller.bamf_in}|n")
        lines.append(f" Bamf-out: |w{caller.bamf_out}|n")
        lines.append(
            " |x(edit with 'imm bamfin <message>' / 'imm bamfout <message>', "
            "'reset' to restore defaults; {name} is a placeholder)|n"
        )

        lines.append("|y" + "=" * 78 + "|n")
        caller.msg("\n".join(lines))


class CmdHolylight(Command):
    """
    Toggle holylight.

    Usage:
      holylight
      holylight on
      holylight off

    Off, you see the game exactly like a player does - no dbrefs on
    rooms, exits, items, or characters. On, every name gets its
    "(#dbref)" shown, the way it needs to for building/debugging.

    With no argument, toggles your current state. Off by default even
    for Builder+ characters - holylight is a deliberate switch, not
    something tied automatically to permission level, so staff can
    walk the game world as a player would without losing builder
    access.

    Builder permission or higher is required to use this command at
    all - if you can't see 'holylight' in your command list, you
    don't have it.
    """

    key = "holylight"
    locks = "cmd:perm(Builder)"
    help_category = "Immortal"

    def func(self):
        caller = self.caller

        # Defensive self-heal, same pattern as CmdImm/CmdSheet - catches
        # characters created before the holylight field existed.
        if caller.ensure_data_integrity():
            caller.msg("|x(holylight: found and repaired missing character data)|n")

        arg = self.args.strip().lower() if self.args else ""

        if arg in ("on", "off"):
            new_state = arg == "on"
        elif arg:
            caller.msg("Usage: holylight | holylight on | holylight off")
            return
        else:
            new_state = not caller.holylight

        caller.holylight = new_state

        if new_state:
            caller.msg("|wHolylight ON|n - you now see dbrefs on everything.")
        else:
            caller.msg("|xHolylight off|n - you see the game like a player again.")


class CmdRoll(Command):
    """
    Roll an attribute + skill check via the exploding d10 dice pool.

    Usage:
      roll <attribute>/<skill> [= <required successes>] [+ <bonus dice>]

    Examples:
      roll agility/stealth
      roll agility/stealth = 2
      roll intelligence/arcana = 2 + 1
    """

    key = "roll"
    aliases = ["check"]
    help_category = "General"

    VALID_ATTRIBUTES = (
        "might", "agility", "endurance",
        "intelligence", "cunning", "willpower",
        "charisma", "influence", "appearance",
    )

    def func(self):
        caller = self.caller
        args = self.args.strip()

        if not args:
            caller.msg("Usage: roll <attribute>/<skill> [= <required successes>] [+ <bonus dice>]")
            return

        extra_bonus_dice = 0
        if "+" in args:
            args, bonus_str = args.rsplit("+", 1)
            args = args.strip()
            bonus_str = bonus_str.strip()
            if not bonus_str.isdigit():
                caller.msg("Bonus dice must be a whole number.")
                return
            extra_bonus_dice = int(bonus_str)

        required_successes = 1
        if "=" in args:
            args, req_str = args.split("=", 1)
            args = args.strip()
            req_str = req_str.strip()
            if not req_str.isdigit():
                caller.msg("Required successes must be a whole number.")
                return
            required_successes = int(req_str)

        if "/" not in args:
            caller.msg("Usage: roll <attribute>/<skill> [= <required successes>] [+ <bonus dice>]")
            return

        attribute_name, skill_name = (part.strip() for part in args.split("/", 1))
        attribute_name = attribute_name.lower()

        if attribute_name not in self.VALID_ATTRIBUTES:
            caller.msg(
                f"'{attribute_name}' isn't a valid attribute. "
                f"Choose from: {', '.join(self.VALID_ATTRIBUTES)}"
            )
            return

        canonical = canonical_skill_name(skill_name)
        if canonical is None:
            caller.msg(
                f"'{skill_name}' isn't a recognized skill. "
                f"Use |wskills|n to see the full list."
            )
            return

        caller.perform_skill_check(
            attribute_name, canonical, required_successes,
            extra_bonus_dice=extra_bonus_dice,
        )


class CmdSkills(Command):
    """
    List every skill, grouped by category, with your current ranks.

    Usage:
      skills
    """

    key = "skills"
    aliases = ["skilllist"]
    help_category = "General"

    def func(self):
        caller = self.caller
        current = caller.attributes.get("skills", default={})

        lines = []
        lines.append("|y" + "=" * 78 + "|n")
        lines.append(f"|w{'SKILLS':^78}|n")
        lines.append("|y" + "=" * 78 + "|n")

        for category, category_skills in SKILL_CATEGORIES.items():
            lines.append(f"|c{category}|n")
            line = "  "
            for i, name in enumerate(category_skills):
                rank = current.get(name, 0)
                line += f"{name:<16}|w{rank:<3}|n"
                if (i + 1) % 3 == 0:
                    lines.append(line)
                    line = "  "
            if line.strip():
                lines.append(line)
            lines.append("")

        caller.msg("\n".join(lines).rstrip())


class CmdSay(Command):
    """
    Speak out loud in the language you're currently speaking.

    Usage:
      say <message>

    Listeners who know the language you're speaking (see 'speak' to
    change it, 'sheet' to see which ones you know) hear you clearly.
    Everyone else hears your words garbled into nonsense - the same
    garbled shape every time for a given word in a given language, so
    a language you hear often enough can start to feel familiar even
    before you actually learn it (see world/languages.py).

    This overrides Evennia's default `say` (same key, so it replaces
    rather than stacks - see CharacterCmdSet.at_cmdset_creation() in
    commands/default_cmdsets.py) specifically to add that garbling;
    aliases (' and ") match Evennia's original for the same typing
    shortcut.
    """

    key = "say"
    aliases = ["'", '"']
    help_category = "General"

    def func(self):
        caller = self.caller
        message = self.args.strip() if self.args else ""

        if not message:
            caller.msg("Say what?")
            return

        if not caller.location:
            caller.msg("You have no location to speak into.")
            return

        caller.ensure_data_integrity()

        language = caller.speaking_language
        canonical = canonical_language_name(language) or language

        caller.msg(f'You say, in {canonical}, "{message}"')

        for listener in caller.location.contents:
            if listener is caller:
                continue

            knows_it = (
                hasattr(listener, "knows_language")
                and listener.knows_language(canonical)
            )
            heard = message if knows_it else garble_text(message, canonical)

            listener.msg(
                f'{caller.get_display_name(listener)} says, in {canonical}, "{heard}"'
            )


class CmdSpeak(Command):
    """
    Switch which language 'say' speaks in.

    Usage:
      speak <language>
      speak

    With no argument, shows the language you're currently speaking
    and the full list of languages you know. You can only switch to a
    language you actually know - see world/races.py for which
    languages each race starts with.
    """

    key = "speak"
    help_category = "General"

    def func(self):
        caller = self.caller
        caller.ensure_data_integrity()

        arg = self.args.strip() if self.args else ""

        if not arg:
            caller.msg(
                f"You are currently speaking |w{caller.speaking_language}|n.\n"
                f"Languages known: |w{', '.join(caller.languages) or 'none'}|n"
            )
            return

        canonical = canonical_language_name(arg)
        if canonical is None:
            caller.msg(f"'{arg}' isn't a recognized language.")
            return

        if not caller.knows_language(canonical):
            caller.msg(f"You don't know {canonical}.")
            return

        caller.speaking_language = canonical
        caller.msg(f"You are now speaking |w{canonical}|n.")


MEMORIZE_REQUIRED_SUCCESSES = 3  # balance number - easy to retune


def _render_memorized_locations(caller):
    """
    Shared "MEMORIZED LOCATIONS" box used by both `memorize` (no-arg
    form) and `locations`, so there's a single place to change the
    display instead of two copies drifting apart.
    """
    locations = caller.memorized_locations
    capacity = caller.get_memorized_location_capacity()

    lines = [
        "|y" + "=" * 60 + "|n",
        f"|w{'MEMORIZED LOCATIONS':^60}|n",
        "|y" + "=" * 60 + "|n",
    ]

    if locations:
        for index, name in enumerate(locations, start=1):
            lines.append(f" {index}. {name}")
    else:
        lines.append(" You have no memorized locations.")

    lines.append("|y" + "-" * 60 + "|n")
    lines.append(
        f" {len(locations)} / {capacity} memorized location(s)"
    )
    lines.append("|y" + "=" * 60 + "|n")

    return "\n".join(lines)


class CmdMemorize(Command):
    """
    Memorize the current location as a permanent teleport destination.

    Usage:
    memorize
    memorize <location name>

    With no argument, displays your current memorized locations and 
    explains how to memorize the current room.

    Memorizing a location requires an Intelligence/Arcana skill check 
    with 3 required successes.
    """

    key = "memorize"
    help_category = "Magick"

    def func(self):
        caller = self.caller
        name = self.args.strip() if self.args else ""

        if not name:
            caller.msg(_render_memorized_locations(caller))
            caller.msg(
                "\nTo memorize this location, use: |wmemorize <name>|n"
            )
            return
        
        if caller.location is None:
            caller.msg("You aren't currently in a location that can be memorized.")
            return
        
        caller.ensure_data_integrity()

        capacity = caller.get_memorized_location_capacity()
        locations = caller.memorized_locations

        if len(locations) >= capacity:
            caller.msg(
                f"You cannot memorize another location. "
                f"You have reached your Intelligence-based limit of "
                f"{capacity} memorized location(s)."
            )
            return
        

        if caller.has_memorized_location(name):
            caller.msg(
                f"You already have a memorized location named |w{name}|n. "
                f"Forget it first if you want to use that name again."
            )
            return

        result = caller.perform_skill_check(
            "intelligence",
            "Arcana",
            MEMORIZE_REQUIRED_SUCCESSES,
        )

        if result.tier < ResultTier.SUCCESS:
            caller.msg(
                f"|rYou fail to memorize this location as "
                f"'{name}'.|n"
            )
            return

        room_id = caller.location.id

        if caller.memorize_location(name, room_id):
            caller.msg(
                f"|gYou successfully memorize this location as "
                f"'{name}'.|n"
            )
        else:
            #This should only happen if the charter's data changed
            #between the capacity/name checks and the save.
            caller.msg(
                "|rYou were unable to save that memorized location.|n"
            )


class CmdLocations(Command):
    """
    Display your permanent memorized teleport locations.

    Usage:
        locations
    """

    key = "locations"
    help_category = "Magick"

    def func(self):
        caller = self.caller
        caller.ensure_data_integrity()
        caller.msg(_render_memorized_locations(caller))


class CmdForget(Command):
    """
    Forget a permanent memorized teleport location/

    Usage:
        forget <location name>
    """

    key = "forget"
    help_category = "Magick"

    def func(self):
        caller = self.caller
        name = self.args.strip() if self.args else ""

        if not name:
            caller.msg("Usage: forget <location name>")
            return

        caller.ensure_data_integrity()

        if not caller.has_memorized_location(name):
            caller.msg(
                f"You don't have a memorized location named |w{name}|n."
            )
            return
        caller.forget_memorized_location(name)

        caller.msg(
            f"|gYou forget the memorized location '{name}'.|n"
        )


# Balance numbers, tunable - the design doc is explicit that word
# complexity values are examples to be balanced later. Reusing a
# word's own `complexity` as its learning roll's required successes
# keeps this to a single number per word instead of a second parallel
# "how hard is this to learn" value that could drift out of sync.
STUDY_ATTRIBUTE = "intelligence"

# Recognized as "study the room itself" rather than a search term.
STUDY_ROOM_KEYWORDS = ("here", "room")


def _study_source_words(obj, caller):
    """
    Return the list of Magick word ids `obj` can teach via 'study',
    and a short label describing it for messages. Three kinds of
    source, each gated the same way (a bool flag + a magick_words
    list), so CmdStudy.func() doesn't need to care which one it got:

      - a Character (PC or, once mobs have their own typeclass, an
        NPC) willing to teach - gated on teaches_magick_words,
        offering what THEY know (known_magick_words)
      - a Room studied via 'study here'/'study room' - gated on
        is_magick_location, offering its own magick_words list
      - anything else (an Item, typically) - gated on is_magick,
        offering its own magick_words list
    """
    if hasattr(obj, "known_magick_words"):
        label = obj.get_display_name(caller)
        if not obj.attributes.get("teaches_magick_words", default=False):
            return [], label
        return obj.known_magick_words, label

    if hasattr(obj, "is_magick_location"):
        if not obj.is_magick_location:
            return [], "here"
        return obj.magick_words, "here"

    label = obj.get_display_name(caller)
    if not obj.attributes.get("is_magick", default=False):
        return [], label
    return obj.attributes.get("magick_words", default=[]), label


class CmdStudy(Command):
    """
    Attempt to learn a Magick word from a magical source.

    Usage:
      study <object>
      study <character>
      study here

    Three kinds of source:

      - An object (see itemedit's "is magick"/"magick words" fields) -
        study checks your inventory and the room for a name match.
      - A willing teacher - another character (a future NPC, or a
        player who's been granted the ability) who has
        teaches_magick_words switched on. Studying them offers up
        whatever Magick words THEY already know that you don't.
      - The room itself ('study here'/'study room') - for ambient
        magic, ancient inscriptions, and ritual sites that aren't a
        discrete object (see @redit's "is magick location"/"magick
        words" fields).

    For the first unknown word found at that source:

      - If your rank in the word's associated Magick skill is below
        that word's minimum requirement, you sense Magick but don't
        yet understand it. No roll is made, and nothing is learned -
        raise the skill and try again.
      - Otherwise, you attempt a learning roll: Intelligence + the
        word's Magick skill, against a number of required successes
        equal to the word's complexity. Success permanently adds the
        word to your known Magick vocabulary (see 'magick words').
        Failure teaches you nothing this time, but you're free to
        study the same source again.

    Meeting a word's skill requirement means you're ABLE to learn it -
    it does not teach it to you automatically. Two characters at the
    same skill rank can know entirely different words.
    """

    key = "study"
    help_category = "Magick"

    def func(self):
        caller = self.caller
        name = self.args.strip() if self.args else ""

        if not name:
            caller.msg(
                "Usage: study <object> | study <character> | study here"
            )
            return

        caller.ensure_data_integrity()

        if name.lower() in STUDY_ROOM_KEYWORDS:
            if caller.location is None:
                caller.msg("You have nowhere to study.")
                return
            obj = caller.location
        else:
            candidates = list(caller.contents)
            if caller.location:
                candidates += list(caller.location.contents)

            obj = caller.search(name, candidates=candidates)
            if not obj:
                return  # caller.search already sent a not-found message

            if obj is caller:
                caller.msg("You can't study yourself.")
                return

        word_ids, source_label = _study_source_words(obj, caller)

        unknown_word_id = next(
            (word_id for word_id in word_ids if not caller.knows_magick_word(word_id)),
            None,
        )

        if unknown_word_id is None:
            if word_ids:
                caller.msg(f"You've already learned everything {source_label} has to teach you.")
            elif hasattr(obj, "known_magick_words"):
                caller.msg(f"{source_label} has nothing to teach you right now.")
            elif hasattr(obj, "is_magick_location"):
                caller.msg("You study your surroundings, but sense nothing here worth learning.")
            else:
                caller.msg(f"You find nothing magical about {source_label}.")
            return

        word_data = magick_words_registry.get_word_data(unknown_word_id)

        if not caller.understands_magick_word(unknown_word_id):
            caller.msg(
                f"You sense Magick within {source_label}, but you "
                f"don't yet understand it. (Requires {word_data['skill']} "
                f"{word_data['min_skill']}.)"
            )
            return

        result = caller.perform_skill_check(
            STUDY_ATTRIBUTE,
            word_data["skill"],
            word_data["complexity"],
        )

        if result.tier < ResultTier.SUCCESS:
            caller.msg(
                f"|rYou study {source_label} intently, but the "
                f"meaning slips away from you. (Try again.)|n"
            )
            return

        caller.learn_magick_word(unknown_word_id)
        caller.msg(
            f"|gSomething clicks into place. You have learned the Magick word "
            f"{word_data['word']} ({word_data['pronunciation']}) - {word_data['meaning']}.|n"
        )


class CmdMagickWords(Command):
    """
    List the Magick words you've learned.

    Usage:
      magick words
    """

    key = "magick words"
    aliases = ["vocabulary"]
    help_category = "Magick"

    def func(self):
        caller = self.caller
        caller.ensure_data_integrity()

        known = caller.known_magick_words

        lines = [
            "|y" + "=" * 60 + "|n",
            f"|w{'KNOWN MAGICK WORDS':^60}|n",
            "|y" + "=" * 60 + "|n",
        ]

        if not known:
            lines.append(" You don't know any Magick words yet.")
        else:
            for word_id in known:
                word_data = magick_words_registry.get_word_data(word_id)
                if word_data is None:
                    continue  # stale/removed word id - skip rather than crash
                lines.append(
                    f" {word_data['word']} ({word_data['pronunciation']}) - "
                    f"{word_data['meaning']}  |c[{word_data['skill']}]|n"
                )

        lines.append("|y" + "=" * 60 + "|n")
        caller.msg("\n".join(lines))


class CmdCraftSpell(Command):
    """
    Open the spell-crafting altar to construct a new Magick spell.

    Usage:
      craft spell

    Walks you through choosing a primary Magick skill, a
    delivery/target type, and building the spell up from Magick words
    you've actually learned (see 'study' and 'magick words'). Only
    words and skills you already know appear in the menu - if you
    haven't learned it, it isn't offered.

    Requires an Altar (see @objedit) present in the room - you can't
    craft a spell without one to work at.

    This spell is under construction while you're in the menu. Saving
    stores it as a draft; naming the finished spell, the creation
    roll, and permanently learning it are handled by a later stage of
    this system.
    """

    key = "craft spell"
    aliases = ["craft magick", "altar"]
    help_category = "Magick"

    def func(self):
        caller = self.caller

        location = caller.location
        has_altar = location is not None and any(
            isinstance(obj, Altar) for obj in location.contents
        )
        if not has_altar:
            caller.msg("You need to be at an altar to craft Magick.")
            return

        caller.ensure_data_integrity()

        EvMenu(
            caller,
            "world.spell_menu",
            startnode="node_main",
            cmd_on_exit=None,
        )


class CmdPick(Command):
    """
    Attempt to pick a locked door/exit.

    Usage:
      pick <exit>

    Rolls the exit's configured attribute/skill (pick_attribute /
    pick_skill, default Agility/Thievery) against its pick_successes
    difficulty. On a SUCCESS or CRITICAL, the exit unlocks. Builders
    set the difficulty per-exit with, e.g.:

      @set north/pick_successes = 4
      @set north/pick_attribute = agility
      @set north/pick_skill = Thievery

    An exit with pickable = False (@set north/pickable = False) can
    never be picked open - useful for a door that only opens via a
    lever or key.
    """

    key = "pick"
    help_category = "General"

    def func(self):
        caller = self.caller

        if not self.args or not self.args.strip():
            caller.msg("Pick what? Usage: pick <exit>")
            return

        target_name = self.args.strip()
        exit_obj = caller.search(
            target_name,
            candidates=caller.location.exits if caller.location else [],
        )
        if not exit_obj:
            return  # caller.search already sent a not-found message

        if not exit_obj.attributes.has("locked"):
            caller.msg(f"{exit_obj.get_display_name(caller)} isn't something you can pick.")
            return

        if not exit_obj.db.locked:
            caller.msg(f"{exit_obj.get_display_name(caller)} is already unlocked.")
            return

        if not exit_obj.attributes.get("pickable", default=True):
            caller.msg(f"{exit_obj.get_display_name(caller)} can't be picked open.")
            return

        pick_successes = exit_obj.attributes.get("pick_successes", default=3)
        pick_attribute = exit_obj.attributes.get("pick_attribute", default="agility")
        pick_skill = exit_obj.attributes.get("pick_skill", default="Thievery")

        result = caller.perform_skill_check(
            pick_attribute, pick_skill, pick_successes, announce=False
        )

        label = f"{pick_attribute.capitalize()} / {pick_skill}"
        caller.msg(f"|c[Picking {exit_obj.get_display_name(caller)} - {label}]|n {result}")

        if result.tier >= ResultTier.SUCCESS:
            exit_obj.db.locked = False
            caller.msg(f"|gThe lock clicks open.|n")
            if caller.location:
                caller.location.msg_contents(
                    f"{caller.get_display_name(None)} picks {exit_obj.get_display_name(None)} open.",
                    exclude=caller,
                )
        else:
            caller.msg("|rYou fail to pick the lock.|n")


class CmdUnlock(Command):
    """
    Unlock a door/exit using a matching key from your inventory.

    Usage:
      unlock <exit>

    Searches everything you're carrying for a Key whose key_id
    matches the exit's key_id. Unlike picking, this always succeeds
    if you have the right key - no roll involved - and the key isn't
    consumed, so it works again next time.
    """

    key = "unlock"
    help_category = "General"

    def func(self):
        caller = self.caller

        if not self.args or not self.args.strip():
            caller.msg("Unlock what? Usage: unlock <exit>")
            return

        exit_obj = caller.search(
            self.args.strip(),
            candidates=caller.location.exits if caller.location else [],
        )
        if not exit_obj:
            return

        if not hasattr(exit_obj, "key_matches"):
            caller.msg(f"{exit_obj.get_display_name(caller)} isn't something you can unlock.")
            return

        if not exit_obj.locked:
            caller.msg(f"{exit_obj.get_display_name(caller)} is already unlocked.")
            return

        matching_key = next(
            (item for item in caller.contents if exit_obj.key_matches(item)),
            None,
        )
        if matching_key is None:
            caller.msg("You don't have a key that fits.")
            return

        exit_obj.locked = False
        caller.msg(
            f"|gYou unlock {exit_obj.get_display_name(caller)} with "
            f"{matching_key.get_display_name(caller)}.|n"
        )
        if caller.location:
            caller.location.msg_contents(
                f"{caller.get_display_name(None)} unlocks {exit_obj.get_display_name(None)}.",
                exclude=caller,
            )


class CmdLock(Command):
    """
    Lock a door/exit using a matching key from your inventory.

    Usage:
      lock <exit>

    Same key-matching rule as unlock - requires a Key in your
    inventory whose key_id matches the exit's key_id.
    """

    key = "lock"
    help_category = "General"

    def func(self):
        caller = self.caller

        if not self.args or not self.args.strip():
            caller.msg("Lock what? Usage: lock <exit>")
            return

        exit_obj = caller.search(
            self.args.strip(),
            candidates=caller.location.exits if caller.location else [],
        )
        if not exit_obj:
            return

        if not hasattr(exit_obj, "key_matches"):
            caller.msg(f"{exit_obj.get_display_name(caller)} isn't something you can lock.")
            return

        if exit_obj.locked:
            caller.msg(f"{exit_obj.get_display_name(caller)} is already locked.")
            return

        matching_key = next(
            (item for item in caller.contents if exit_obj.key_matches(item)),
            None,
        )
        if matching_key is None:
            caller.msg("You don't have a key that fits.")
            return

        exit_obj.locked = True
        caller.msg(f"|gYou lock {exit_obj.get_display_name(caller)}.|n")


class CmdDoorEdit(Command):
    """
    Open a menu-driven editor for a locked door/exit (OasisOLC-style).

    Usage:
      doedit <exit>

    Lets you toggle locked/pickable and set pick_successes,
    pick_attribute, pick_skill, and the locked-traversal message
    through a numbered menu instead of a string of @set commands.

    Valid attributes: """ + ", ".join(VALID_ATTRIBUTES) + """
    Valid skills: """ + ", ".join(ALL_SKILLS) + """
    """

    key = "doedit"
    aliases = ["oasisdoor"]
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller

        if not self.args or not self.args.strip():
            caller.msg("Edit what? Usage: doedit <exit>")
            return

        exit_obj = caller.search(
            self.args.strip(),
            candidates=caller.location.exits if caller.location else [],
        )
        if not exit_obj:
            return

        if not isinstance(exit_obj, LockableExit):
            caller.msg(
                f"{exit_obj.get_display_name(caller)} isn't a LockableExit "
                f"(use @typeclass {exit_obj.key} = typeclasses.exits.LockableExit first)."
            )
            return

        try:
            menu = ExitBuildingMenu(caller, exit_obj)
        except Exception as err:
            caller.msg(f"|rFailed to open the door editor: {err}|n")
            from evennia.utils import logger
            logger.log_trace()
            return

        # Some versions/configurations of the building_menu contrib
        # require an explicit call to start displaying the menu rather
        # than doing so automatically on construction. Harmless no-op
        # if this build already opens on __init__.
        if hasattr(menu, "open") and callable(menu.open):
            try:
                menu.open()
            except Exception as err:
                caller.msg(f"|rFailed to display the door editor: {err}|n")
                from evennia.utils import logger
                logger.log_trace()


class CmdItemEdit(Command):
    """
    Open a menu-driven editor for an item (OasisOLC-style).

    Usage:
      itemedit <item>

    Lets you set an item's attributes - identity, physical properties,
    equipment slot/stats, magick, tool, and light fields - through a
    numbered menu instead of a string of 'set' commands. Which fields
    show up depends on the item's typeclass: a Weapon gets an extra
    combat section (weapon type, stamina cost) a plain Item doesn't,
    for example.

    See 'help item attributes' for what every field means and what
    values it accepts.
    """

    key = "itemedit"
    aliases = ["oasisitem"]
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    def func(self):
        caller = self.caller

        if not self.args or not self.args.strip():
            caller.msg("Edit what? Usage: itemedit <item>")
            return

        item = caller.search(
            self.args.strip(),
            candidates=caller.contents + (caller.location.contents if caller.location else []),
        )
        if not item:
            return

        if not isinstance(item, Item):
            caller.msg(
                f"{item.get_display_name(caller)} isn't an Item "
                f"(use @typeclass {item.key} = typeclasses.items.Item, "
                f"or one of its subclasses, first)."
            )
            return

        # Dispatch on typeclass - this is what makes the menu's
        # available fields change depending on what kind of item it
        # is, rather than one menu trying to cover every field for
        # every item type.
        if isinstance(item, Weapon):
            menu_class = WeaponBuildingMenu
        elif isinstance(item, Armor):
            menu_class = ArmorBuildingMenu
        else:
            menu_class = ItemBuildingMenu

        try:
            menu = menu_class(caller, item)
        except Exception as err:
            caller.msg(f"|rFailed to open the item editor: {err}|n")
            from evennia.utils import logger
            logger.log_trace()
            return

        # See the matching comment in CmdDoorEdit: some versions of the
        # building_menu contrib need an explicit open() call.
        if hasattr(menu, "open") and callable(menu.open):
            try:
                menu.open()
            except Exception as err:
                caller.msg(f"|rFailed to open the item editor: {err}|n")
                from evennia.utils import logger
                logger.log_trace()


class CmdWear(Command):
    """
    Wear/wield an item you're carrying. The slot is always whichever
    one the item itself is built for - you don't choose it.

    Usage:
      wear <item>

    Available slots come from your race's body parts (see 'body') -
    e.g. head, torso, back, arms, left_wrist, right_wrist, left_ring,
    legs, feet, wielded, offhand, floaty, and for races that have
    them, tail and wings. If an item won't wear, it either isn't
    equippable or a builder hasn't set its slot yet (itemedit <item>,
    or @set <item>/wear_slot = <slot>) - it's not something you pick
    at wear-time.

    Builders/staff only:
      wear <item> = <slot>
        Force a slot at wear-time, bypassing the item's own
        wear_slot. Useful for testing an item before its slot is
        configured. Regular characters can't do this.
    """

    key = "wear"
    aliases = ["wield"]
    help_category = "General"

    def func(self):
        caller = self.caller

        if not self.args or not self.args.strip():
            caller.msg("Wear what? Usage: wear <item>")
            return

        is_builder = caller.locks.check_lockstring(caller, "dummy:perm(Builder)")

        if "=" in self.args:
            item_name, slot_override = (part.strip() for part in self.args.split("=", 1))
            if not is_builder:
                caller.msg(
                    "You can't choose a slot - what you wear goes wherever "
                    "the item itself is made for."
                )
                return
        else:
            item_name, slot_override = self.args.strip(), None

        item = caller.search(item_name, candidates=caller.contents)
        if not item:
            return  # caller.search already sent a not-found message

        slot_id = slot_override or item.attributes.get("wear_slot", default=None)
        if not slot_id:
            if is_builder:
                available = ", ".join(
                    body_parts_registry.slot_display_name(s) for s in caller.equip_slots
                )
                caller.msg(
                    f"{item.get_display_name(caller)} has no wear_slot set. As a "
                    f"builder you can force one with 'wear {item.key} = <slot>' "
                    f"(available: {available}), but the real fix is setting the "
                    f"item's own slot (itemedit {item.key}, or @set "
                    f"{item.key}/wear_slot = <slot>)."
                )
            else:
                caller.msg(f"{item.get_display_name(caller)} can't be worn.")
            return

        can_equip, reason = caller.can_equip_item(item, slot_id)
        if not can_equip:
            caller.msg(reason)
            return

        if caller.equip(item, slot_id):
            caller.msg(
                f"|gYou wear {item.get_display_name(caller)} on your "
                f"{body_parts_registry.slot_display_name(slot_id)}.|n"
            )
            if caller.location:
                caller.location.msg_contents(
                    f"{caller.get_display_name(None)} wears {item.get_display_name(None)}.",
                    exclude=caller,
                )
        else:
            caller.msg(f"You can't wear {item.get_display_name(caller)} there.")


class CmdRemove(Command):
    """
    Take off/unwield something you're wearing.

    Usage:
      remove <slot or item>

    Accepts either a slot name (e.g. 'remove chest') or the item's
    name (e.g. 'remove leather jerkin').
    """

    key = "remove"
    aliases = ["unwear", "unwield"]
    help_category = "General"

    def func(self):
        caller = self.caller

        if not self.args or not self.args.strip():
            caller.msg("Remove what? Usage: remove <slot or item>")
            return

        query = self.args.strip()
        equipment = caller.equipment

        slot_id = query if query in equipment else None
        if slot_id is None:
            query_lower = query.lower()
            for candidate_slot, item in equipment.items():
                if query_lower in item.get_display_name(caller).lower() or query_lower == item.key.lower():
                    slot_id = candidate_slot
                    break

        if slot_id is None:
            caller.msg(f"You aren't wearing anything matching '{query}'.")
            return

        item = caller.unequip(slot_id)
        if item is None:
            caller.msg(f"You aren't wearing anything on your {body_parts_registry.slot_display_name(slot_id)}.")
            return

        caller.msg(
            f"|gYou remove {item.get_display_name(caller)} from your "
            f"{body_parts_registry.slot_display_name(slot_id)}.|n"
        )
        if caller.location:
            caller.location.msg_contents(
                f"{caller.get_display_name(None)} removes {item.get_display_name(None)}.",
                exclude=caller,
            )


# ========================================================================================
# TEST COMMANDS
# ========================================================================================
class CmdTestMagickVocabulary(Command):
    """
    Temporary diagnostic command for testing Magick vocabulary access.
    """

    key = "test magick vocabulary"
    help_category = "Magick"

    def func(self):
        from world.spell_rules import known_words_by_category

        caller = self.caller
        caller.ensure_data_integrity()

        caller.msg("|y=== KNOWN MAGICK VOCABULARY TEST ===|n")

        for category in ("concept", "effect", "modifier"):
            words = known_words_by_category(
                caller,
                category,
            )

            caller.msg(
                f"|w{category.title()}:|n {words}"
            )

class CmdTestSkill(Command):
    """
    Development command for directly setting skill ranks.

    Usage:
        testskill <skill> <rank>
        testskill <skill>

    Examples:
        testskill Evocation 5
        testskill Arcana 3
        testskill Evocation
    """

    key = "testskill"
    aliases = ["test skill"]
    locks = "cmd:perm(Admin)"
    help_category = "Admin"

    def func(self):
        caller = self.caller

        if not self.args:
            caller.msg(
                "|rUsage: testskill <skill> <rank>|n"
            )
            caller.msg(
                "Example: testskill Evocation 5"
            )
            return

        parts = self.args.split()

        # --------------------------------------------------------------
        # Display current rank
        # --------------------------------------------------------------
        if len(parts) == 1:
            skill_name = parts[0]

            try:
                current = caller.get_skill(skill_name)
            except Exception:
                caller.msg(
                    f"|rUnknown skill: {skill_name}|n"
                )
                return

            caller.msg(
                f"|w{skill_name}:|n {current}"
            )
            return

        # --------------------------------------------------------------
        # Set rank
        # --------------------------------------------------------------
        skill_name = " ".join(parts[:-1])
        rank_text = parts[-1]

        try:
            rank = int(rank_text)
        except ValueError:
            caller.msg(
                "|rSkill rank must be a whole number.|n"
            )
            return

        if rank < 0:
            caller.msg(
                "|rSkill rank cannot be negative.|n"
            )
            return

        try:
            caller.set_skill(skill_name, rank)
        except ValueError:
            caller.msg(
                f"|rUnknown skill: {skill_name}|n"
            )
            return

        canonical = skill_name

        # Get the canonical name back from the character system.
        from world.skills import canonical_skill_name

        canonical = canonical_skill_name(skill_name)

        caller.msg(
            f"|gSet {canonical} skill to {rank}.|n"
        )