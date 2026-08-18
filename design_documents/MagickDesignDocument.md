EAETHERIA MAGICK SYSTEM
========================

OVERVIEW
--------
Eaetheria uses a skill-based, language-driven Magick system.

Characters do not memorize spells in the traditional D&D sense.
Instead, characters:

    1. Learn the language of Magick.
    2. Discover Magick words throughout the world.
    3. Develop their Magick skills.
    4. Combine words and Magick skills at an altar.
    5. Create and name their own spells.
    6. Store those spells permanently on their character.
    7. Cast those spells using their Magick skills.

The goal is for players to discover and construct their own magic
rather than simply receiving predetermined spell lists.


============================================================
MAGICK SKILLS
============================================================

There are nine Magick skills:

    Abjuration
    Arcana
    Charm
    Conjuration
    Divination
    Evocation
    Illusion
    Necromancy
    Transmutation

Arcana is the general understanding of Magick.

The other eight skills represent specialized approaches to Magick.

Characters are NOT restricted to a single Magick skill and there
are no traditional mage classes.

A character may develop any combination of Magick skills.


============================================================
MAGICK WORDS
============================================================

Magick is an ancient language.

Characters discover individual Magick words throughout the world.

A Magick word should have:

    - Internal identifier
    - Displayed Magick word
    - Phonetic pronunciation
    - Player-readable meaning
    - Associated Magick skill
    - Minimum skill requirement
    - Complexity value
    - Description/lore

Example:

    Word:
        IGNASH

    Pronunciation:
        ig-NASH

    Meaning:
        Fire

    Magick Skill:
        Evocation

    Minimum Skill:
        Evocation 2

    Complexity:
        1


The Magick word should look strange and ancient, but the player
should still be able to understand what it means.

Example:

    IGNASH (ig-NASH) — Fire

This allows Magick to feel like an actual language rather than
a collection of arbitrary keywords.


============================================================
LEARNING MAGICK WORDS
============================================================

Players learn Magick words through exploration and study.

Potential sources include:

    - Magical objects
    - Ancient inscriptions
    - Books
    - Scrolls
    - NPC teachers
    - Quests
    - Magical locations
    - Magical creatures
    - Ritual sites
    - Other discoveries

The player will be taught the STUDY skill during Mud School.

The player may then use:

    study <object>

to attempt to discover Magick words associated with that object.

A Magick word has a minimum required Magick skill.

Example:

    IGNASH
    Evocation requirement: 3

If the character has:

    Evocation 2

they cannot learn the word.

The player should receive a message explaining that they can sense
Magick within the object but do not yet understand it.

If the character meets the required skill level, the appropriate
learning check can be made.

The important distinction is:

    Skill requirement = Can the character understand this word?

    Learning roll = Does the character successfully learn it?


Characters do NOT automatically know every word available to their
skill level.

Two characters can have:

    Evocation 5

but know completely different Magick words.

This makes exploration and discovery an important part of magical
progression.


============================================================
KNOWN MAGICK WORDS
============================================================

Characters should have persistent character data containing their
known Magick words.

Example:

    known_magick_words

        IGNASH
        VAEL
        KORUM
        AETH

The player should eventually have a command to view their known
Magick vocabulary.

Example:

    magick words

or another appropriate command.


============================================================
SPELL CREATION
============================================================

Spells are created at magical altars.

The player does NOT select from a predetermined spell list.

Instead, the player constructs a spell from the Magick words they
have learned.

The player begins spell creation by choosing the PRIMARY MAGICK
SKILL.

Example:

    Choose the primary Magick skill:

    1. Abjuration
    2. Arcana
    3. Charm
    4. Conjuration
    5. Divination
    6. Evocation
    7. Illusion
    8. Necromancy
    9. Transmutation

The first skill selected becomes the spell's:

    PRIMARY SKILL

The Primary Skill determines the skill used when casting the spell.

It does NOT change later.

If the player wants to create the same concept using a different
primary skill, they must START OVER and construct the spell again.


============================================================
SPELL CONSTRUCTION
============================================================

The general conceptual structure of a spell is:

    PRIMARY MAGICK SKILL
            ↓
    DELIVERY / TARGET
            ↓
    CONCEPT
            ↓
    WHAT IT AFFECTS
            ↓
    OPTIONAL MODIFIERS


The exact order of some components may eventually be flexible, but
the spell should conceptually be constructed from these pieces.


============================================================
DELIVERY / TARGET
============================================================

Delivery and range are NOT separate systems.

The delivery/target component determines how the spell reaches its
target.

Initial target/delivery types include:

    Self
    Touch
    Projectile
    Object
    Room

SELF
----
The caster is the target.

Example:

    Transmutation
    → Self
    → Stone
    → Body
    → Transform


TOUCH
-----
The spell targets another entity through physical contact.

Touch spells require the caster to be in MELEE range.

Example:

    Necromancy
    → Touch
    → Life
    → Heal


PROJECTILE
----------
The spell is launched at a target.

Projectile spells may be used at:

    Melee range
    Pole range
    Missile range

Example:

    Evocation
    → Projectile
    → Fire
    → Damage


OBJECT
------
The spell targets an object rather than a creature.

Example:

    Transmutation
    → Object
    → Metal
    → Transform


ROOM
----
The room/location itself is the target.

Room-targeted spells are especially important for non-combat magic.

Examples:

    Divination
    → Room
    → Magic
    → Reveal

    Abjuration
    → Room
    → Ward
    → Magic

    Evocation
    → Room
    → Light
    → Illuminate


============================================================
COMBINING MAGICK SKILLS
============================================================

A spell may contain multiple Magick skills.

However:

    ONLY THE PRIMARY MAGICK SKILL contributes its skill rating
    to the casting dice pool.

Secondary Magick skills NEVER provide additional dice.

Secondary skills are components of the spell and contribute to the
spell's complexity.

Example:

    Abjuration
    → Shield
    → Evocation
    → Fire

This is a Fire Ward.

The Primary Skill is:

    Abjuration

Therefore the casting roll uses:

    Intelligence
    + Arcana
    + Abjuration
    + Equipment bonuses

Evocation does NOT add its skill rating to the roll.

The Evocation component simply makes the spell more complex and
allows Fire to be incorporated into the Abjuration spell.


============================================================
CROSS-SCHOOL MAGICK
============================================================

Magick words can be used across different Magick skills when the
combination makes sense.

The meaning of a word can change depending on how it is used.

For example, the concept FIRE might be used as:

    Evocation → Fire → Damage

    Abjuration → Shield → Evocation → Fire

    Conjuration → Summon → Fire

    Transmutation → Object → Fire → Transform

The same Magick word can therefore participate in many different
types of magic.

This is an important part of the language-based system.


============================================================
SPELL EXAMPLES
============================================================

FIRE ATTACK
-----------

    Evocation
    → Projectile
    → Fire
    → Damage

Primary Skill:

    Evocation


FIRE WARD
---------

    Abjuration
    → Shield
    → Evocation
    → Fire

Primary Skill:

    Abjuration


HEALING TOUCH
-------------

    Necromancy
    → Touch
    → Life
    → Heal

Primary Skill:

    Necromancy


SELF TRANSFORMATION
-------------------

    Transmutation
    → Self
    → Stone
    → Body
    → Transform

Primary Skill:

    Transmutation


ROOM DIVINATION
---------------

    Divination
    → Room
    → Magic
    → Reveal

Primary Skill:

    Divination


ROOM WARD
---------

    Abjuration
    → Room
    → Ward
    → Magic

Primary Skill:

    Abjuration


TEMPORARY MAGICAL ANCHOR
------------------------

    Conjuration
    → Room
    → Space
    → Anchor

This could eventually create a temporary magical teleportation
point in the room.

The anchor would be temporary world state and could have:

    room_id
    creator
    expiration time

When the timer expires, the magical anchor disappears.


============================================================
SPELL CREATION MENU
============================================================

The spell creation interface should include:

    Add Modifier
    Remove Modifier
    Start Over
    Finish
    Cancel

START OVER
----------

Completely abandons the current spell construction.

The player returns to the Primary Magick Skill selection.

This allows the player to create the same general concept using a
different Primary Skill.

Example:

    Abjuration → Shield → Evocation → Fire

can be abandoned.

The player can START OVER and create:

    Evocation → Fire → Shield

These are different spells because they have different Primary
Skills.


FINISH
------

Finishes spell construction and proceeds to the spell creation roll.

CANCEL
------

Abandons the spell without saving anything.


============================================================
PLAYER-NAMED SPELLS
============================================================

The player names every spell they create.

The game should NOT automatically call a spell:

    Fireball
    Flame Shield
    Lightning Bolt

Instead, the player chooses the name.

Example:

    Name your spell:

    Flaming Death

The game should warn:

    You have named this spell "Flaming Death".

    You will need to type this name when casting the spell.

    Are you sure?

The player must confirm.

Spell names should be case-insensitive when casting, but the player
must otherwise provide the correct name.

Example:

    cast flaming death

would work for:

    Flaming Death

But:

    cast fireball

would not work unless the player actually named the spell Fireball.


============================================================
SPELL PERSISTENCE
============================================================

Created spells must be stored in persistent character data.

Each spell should store at least:

    name
    primary_skill
    secondary_skills
    words/components
    delivery/target
    complexity
    creation difficulty
    casting difficulty
    mana cost
    any additional spell-specific data


The player should NOT merely store the finished spell's name.

The actual recipe must be stored so the game knows exactly how the
spell works.


============================================================
SPELL LIST COMMAND
============================================================

Players should have a command to see their created spells.

Example:

    spells

Possible output:

    KNOWN SPELLS
    --------------------------------

    1. Flaming Death
       Primary Skill: Evocation
       Difficulty: 5
       Mana: 12

    2. Gentle Touch
       Primary Skill: Necromancy
       Difficulty: 2
       Mana: 4

    3. Mage's Ward
       Primary Skill: Abjuration
       Difficulty: 4
       Mana: 8

The player should also eventually be able to inspect a specific
spell.

Example:

    spells flaming death

which could display:

    FLAMING DEATH
    --------------------------------

    Primary Skill:
        Evocation

    Components:
        Projectile
        Fire
        Damage

    Complexity:
        5

    Casting Difficulty:
        4

    Mana Cost:
        12


============================================================
SPELL COMPLEXITY
============================================================

Every Magick word/component has a complexity value.

Adding components increases the overall complexity of a spell.

Complexity represents how complicated the magical construction is.

Simple spell:

    Fire
    → Projectile

More complex spell:

    Fire
    → Projectile
    → Area
    → Damage

Even more complex:

    Abjuration
    → Shield
    → Evocation
    → Fire
    → Area
    → Duration


Different words may have different complexity values.

For example:

    Fire        1
    Shield      1
    Projectile  1
    Area        2
    Teleport    5

These values are examples only and should be balanced later.


============================================================
SPELL CREATION ROLL
============================================================

Complexity affects the roll required to CREATE the spell.

The spell creation dice pool is:

    Intelligence
    + Arcana
    + Primary Magick Skill
    + Equipment bonuses

Secondary Magick skills do NOT add dice.

Complexity determines the difficulty/target of the creation roll.

The more complicated the spell, the more difficult it is to create.

Example:

    Simple spell:
        Complexity 2
        Low creation difficulty

    Complex spell:
        Complexity 7
        High creation difficulty

The player must successfully create the spell before it becomes
part of their known spells.


============================================================
SPELL CASTING
============================================================

Once a spell has been successfully created, complexity does NOT
make the normal casting roll more difficult.

The normal casting roll is simply:

    Intelligence
    + Arcana
    + Primary Magick Skill
    + Equipment bonuses

The spell's established casting difficulty determines how many
successes are required.

Complexity is therefore primarily relevant during spell creation
and to the spell's mana cost.


============================================================
MANA COST
============================================================

Spell complexity affects the amount of mana required to cast a spell.

More complicated spells cost more mana.

Example:

    Simple spell:
        Complexity 2
        Mana cost 4

    Medium spell:
        Complexity 5
        Mana cost 10

    Very complex spell:
        Complexity 10
        Mana cost 25

The exact formula should be determined during balancing.

The important design rule is:

    Complexity increases mana cost.

A skilled mage can therefore reliably cast a complex spell without
necessarily having a harder casting roll, but the mage cannot cast
that spell indefinitely because it consumes substantial mana.


============================================================
COMBAT RANGE
============================================================

Combat has three distances:

    MELEE
    POLE
    MISSILE

Spell delivery determines which ranges can be used.

TOUCH:

    Melee only.

PROJECTILE:

    Melee
    Pole
    Missile

SELF:

    Caster only.

ROOM:

    Current room.

OBJECT:

    Selected object.

Additional delivery types can be added later if needed.


============================================================
COMBAT SPELL EXAMPLES
============================================================

Touch spell:

    Necromancy
    → Touch
    → Life
    → Heal

Can only be cast while in melee range.

Projectile spell:

    Evocation
    → Projectile
    → Fire
    → Damage

Can be cast at:

    Melee
    Pole
    Missile


============================================================
NON-COMBAT / ROOM MAGIC
============================================================

Not all spells are intended for combat.

Room-targeted spells allow Magick to affect the environment.

Examples:

    Divination
    → Room
    → Magic
    → Reveal

    Abjuration
    → Room
    → Ward
    → Magic

    Illusion
    → Room
    → Appearance
    → Change

Room spells may create persistent or temporary effects attached to
the room.

Possible room effects include:

    magical light
    magical darkness
    wards
    alarms
    anti-magic effects
    illusions
    magical traps
    teleportation anchors
    portals
    environmental transformations


============================================================
RITUAL CASTING
============================================================

Some spells may be designated as RITUAL spells.

A ritual is different from normal casting.

Normal casting:

    cast "spell name"

Ritual casting:

    cast "spell name" ritual

A ritual allows the caster to continue attempting the spell over
multiple combat rounds/rounds of time.

Each round, the caster makes another Magick roll.

The caster continues making rolls until:

    1. They reach the required number of successes, OR
    2. They BOTCH.

A ritual therefore represents gradually building and maintaining a
complex magical effect.

Example:

    cast "Greater Ward" ritual

Round 1:
    Roll Magick
    2 successes

Round 2:
    Roll Magick
    1 success

Round 3:
    Roll Magick
    2 successes

Total:
    5 successes

If the spell required 5 successes, the ritual completes.

If the caster botches at any point, the ritual fails.

The exact treatment of mana during ritual casting should be decided
separately.

Potential options include:

    - Mana consumed each round
    - Mana consumed when the ritual completes
    - A small ongoing mana cost each round
    - Mana reserved for the duration of the ritual

The system should support one of these without changing the basic
ritual mechanic.


============================================================
RITUALS AND COMPLEX MAGIC
============================================================

Ritual casting is particularly appropriate for magic that would be
too complicated or powerful for ordinary combat casting.

Examples:

    powerful wards
    portals
    summoning
    large-area transformations
    powerful divination
    teleportation networks
    magical anchors
    major environmental effects
    large magical barriers

A ritual does NOT give the player additional dice.

The casting pool remains:

    Intelligence
    + Arcana
    + Primary Magick Skill
    + Equipment bonuses

The ritual simply allows the caster to accumulate successes across
multiple rounds.


============================================================
PERMANENT TELEPORTATION LOCATIONS
============================================================

Characters may permanently memorize locations.

Memorized locations are stored in persistent character data.

Each location contains:

    player-defined name
    room_id

The player sees only the name.

The room ID remains hidden.

Example:

    memorized_locations

        Home
            room_id: 123

        Mud School
            room_id: 45

The player can use:

    memorize <location name>

to attempt to memorize the current room.

The memorization check uses:

    Intelligence
    + Arcana
    + relevant racial bonuses
    + equipment bonuses

The character must achieve the required number of successes.

The current design target is:

    3 successes

If the player fails to achieve the required successes, the location
is not memorized.

The player can list their memorized locations and forget locations.

The room ID is never displayed to the player.


============================================================
TEMPORARY MAGICAL LOCATIONS
============================================================

Permanent memorized locations are stored on the character.

Temporary magical points are different.

A future spell may create a temporary magical point in a room.

The temporary point may be represented by a magical object/world
entity containing:

    room_id
    creator
    expiration time

When the timer expires, the temporary point is removed.

This allows future teleport/portal spells to use both:

    Permanent memorized locations

and:

    Temporary magical points


============================================================
FUTURE TELEPORTATION
============================================================

Teleportation should eventually be implemented as a spell rather
than a special hard-coded character ability.

A teleport spell may require concepts such as:

    Conjuration
    Transmutation
    Space
    Destination

The exact recipe will be determined when teleportation is designed.

The teleport spell should ultimately resolve a destination to a
room_id.

Permanent destination:

    Character's memorized location
        ↓
    room_id

Temporary destination:

    Magical anchor
        ↓
    room_id

The player never needs to know or enter the room ID.


============================================================
CORE DESIGN PRINCIPLES
============================================================

1. No traditional spell memorization.

2. No traditional D&D spell slots.

3. Players learn the language of Magick.

4. Magick words are discovered through exploration, study, teaching,
   quests, objects, books, and magical locations.

5. Magick words have minimum skill requirements.

6. Knowing a Magick skill does not automatically teach the player
   all words associated with that skill.

7. Players create spells at magical altars.

8. The player chooses the Primary Magick Skill first.

9. The first Magick Skill selected becomes the Primary Skill.

10. The Primary Skill determines the Magick dice pool.

11. Secondary Magick Skills may be incorporated into spells.

12. Secondary Magick Skills never add dice to the casting roll.

13. Secondary skills contribute to spell complexity.

14. Players can START OVER during spell creation to choose a
    different Primary Skill.

15. Players can REMOVE modifiers during spell creation.

16. Players can FINISH or CANCEL spell creation.

17. Players name their own spells.

18. The player must use the spell's chosen name when casting it.

19. Created spells are stored persistently on the character.

20. Players have a command to list their created spells.

21. Players can inspect individual spells.

22. Spell complexity increases spell creation difficulty.

23. Spell complexity increases mana cost.

24. Once created, complexity does not make the normal casting roll
    harder.

25. Normal casting uses:

        Intelligence
        + Arcana
        + Primary Magick Skill
        + Equipment bonuses

26. Combat has three ranges:

        Melee
        Pole
        Missile

27. Touch spells require melee range.

28. Projectile spells work at melee, pole, and missile range.

29. Self is a valid target.

30. Object is a valid target.

31. Room is a valid target.

32. Room-targeted spells support non-combat/environmental magic.

33. Room effects can potentially persist for a duration.

34. Ritual casting is available for appropriate spells.

35. Ritual casting uses:

        cast "spell name" ritual

36. Rituals make a Magick roll every round.

37. Ritual successes accumulate between rounds.

38. The ritual continues until the required successes are reached.

39. A botch immediately ends/fails the ritual.

40. Rituals do not receive extra dice merely because they are rituals.

41. The system should remain flexible enough to support future
    teleportation, portals, magical anchors, wards, environmental
    effects, summons, transformations, and other complex Magick.