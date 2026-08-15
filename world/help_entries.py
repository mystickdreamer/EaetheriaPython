"""
File-based help entries. These complements command-based help and help entries
added in the database using the `sethelp` command in-game.

Control where Evennia reads these entries with `settings.FILE_HELP_ENTRY_MODULES`,
which is a list of python-paths to modules to read.

A module like this should hold a global `HELP_ENTRY_DICTS` list, containing
dicts that each represent a help entry. If no `HELP_ENTRY_DICTS` variable is
given, all top-level variables that are dicts in the module are read as help
entries.

Each dict is on the form
::

    {'key': <str>,
     'text': <str>}``     # the actual help text. Can contain # subtopic sections
     'category': <str>,   # optional, otherwise settings.DEFAULT_HELP_CATEGORY
     'aliases': <list>,   # optional
     'locks': <str>       # optional, 'view' controls seeing in help index, 'read'
                          #           if the entry can be read. If 'view' is unset,
                          #           'read' is used for the index. If unset, everyone
                          #           can read/view the entry.

"""

HELP_ENTRY_DICTS = [
    {
        "key": "item attributes",
        "aliases": ["itemattrs", "set item", "item set"],
        "category": "Building",
        "locks": "read:perm(Builder)",
        "text": """
            |wItem Attributes|n

            Every Item (and its subtypes Weapon/Armor) stores its data as
            Attributes on |c.db|n. You can set any of these by hand with
            the core |wset|n command:

                set <item>/<attribute> = <value>

            e.g. |wset sword/weight = 4.5|n or
            |wset sword/wear_slot = wielded|n

            Or use the menu-driven editor instead of typing these by hand:

                itemedit <item>

            This opens a numbered menu (OasisOLC-style) built from the
            same validated fields listed below. Which choices appear
            depends on the item's typeclass - a Weapon gets an extra
            "weapon type"/"stamina cost" section a plain Item doesn't,
            for example. See |whelp itemedit|n for the command itself.

            There's also a generalized pair of commands that work the
            same way across items *and* rooms:

                @olist [<category>] [<search>]   - browse a table
                @olist #<dbref>                    - full field dump
                @objedit <object>                  - open the editor
                @objedit <object> = item|weapon|armor|room

            The `=` form on |wobjedit|n sets an object's typeclass
            first (so you can turn a freshly-created plain Object into
            an Item/Weapon/Armor/Room, then edit it, in one command)
            before opening the same menu |witemedit|n would. See
            |whelp objedit|n and |whelp olist|n for details.

            Below is the full list, grouped the same way
            typeclasses/items.py groups them at creation. "Options" lists
            the only values that setter will actually accept where the
            item enforces validation (wear_slot, item_type, weapon_type,
            equip_stat, equip_skill via itemedit/set_wear_slot); plain
            |wset|n on other fields does no validation, so typos won't be
            caught until something reads the field.

            # subtopics

            ## Identity

            - |citem_id|n (str) - internal id string, free text
            - |cunidentified_name|n (str) - name shown while unidentified
            - |cidentified|n (bool) - True/False; if False and
              unidentified_name is set, that name is shown instead of the
              real one until the item is identified

            ## Physical

            - |cweight|n (float)
            - |cstackable|n (bool) - whether copies merge in inventory
            - |csize_matters|n (bool) - if True, only a wielder of the
              same size_category can equip this item (unless their race
              ignores_size_restrictions)
            - |csize_category|n (str) - one of: TINY, SMALL, MEDIUM,
              LARGE, HUGE, GARGANTUAN

            ## Identification

            - |cknowledge_difficulty|n (int) - successes needed to
              identify via Knowledge
            - |carcana_difficulty|n (int) - successes needed to identify
              via Arcana (magick items)

            ## Classification

            - |citem_type|n (str) - one of: WEAPON, ARMOR, FOOD, POTION,
              MATERIAL, MISC

            ## Equipment

            - |cwear_slot|n (str or None) - which body-part slot this
              equips to; None means "not equippable". Valid slots come
              from world/body_parts.py (see |whelp body|n in-game for the
              current list on a given race) - things like head, torso,
              back, arms, left_wrist, right_wrist, left_ring, waist, legs,
              feet, wielded, offhand, floaty, and race-specific slots like
              tail/wings/horns/shell. This is the field that decides where
              an item goes when worn - see |whelp wear|n; players no
              longer pick the slot themselves.
            - |cweapon_type|n (str) - one of: NONE, AXE, BOW, CHAINED,
              CROSSBOW, BLUNT, SLASHING, PIERCING, UNARMED
            - |cstamina_cost|n (int) - 0/unset falls back to a default
              attack cost
            - |cequip_stat|n (str or None) - one of: might, agility,
              endurance
            - |cequip_skill|n (str or None) - one of: Archery, DualWield,
              GreatWeapon, MartialArts, OneHand, ThrownWeapon, LightArmor,
              MediumArmor, HeavyArmor
            - |cstat_bonuses|n (dict) - {attribute_or_skill_name: flat int
              bonus while worn}; |wset <item>/stat_bonuses = {"agility": 1}|n
              replaces the *whole* dict, so use itemedit's "bonuses"
              choice instead to add/remove one entry at a time: enter
              e.g. |wOneHand 2|n to add or update that bonus, or
              |wremove OneHand|n to delete it. Names match a skill or
              an attribute (might/agility/endurance) case-insensitively.

            ## Magick

            - |cis_magick|n (bool)
            - |cis_enchantable|n (bool)
            - |cenchanting_mana_limit|n (int)

            ## Tool info

            - |cis_thief_tools|n (bool)
            - |cthief_tools_bonus_dice|n (int)

            ## Light source

            - |clight_radius_tiles|n (float) - 0 = doesn't emit light
            - |clight_energy|n (float)
            - |clight_color|n (tuple of 3 floats, 0.0-1.0 each - R, G, B)

        """,
    },
    {
        "key": "evennia",
        "aliases": ["ev"],
        "category": "General",
        "locks": "read:perm(Developer)",
        "text": """
            Evennia is a MU-game server and framework written in Python. You can read more
            on https://www.evennia.com.

            # subtopics

            ## Installation

            You'll find installation instructions on https://www.evennia.com.

            ## Community

            There are many ways to get help and communicate with other devs!

            ### Discussions

            The Discussions forum is found at https://github.com/evennia/evennia/discussions.

            ### Discord

            There is also a discord channel for chatting - connect using the
            following link: https://discord.gg/AJJpcRUhtF

        """,
    },
]
