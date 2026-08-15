"""
Dice Pool System

Mirrors Godot's `DiceRoller` autoload as closely as possible from the
call sites visible in EntityStats.perform_skill_check(): an exploding
d10 pool, a success threshold (die value needed to count as a hit), a
required-successes target, and a result tier.

I don't have DiceRoller.gd itself, only how EntityStats calls it, so
DEFAULT_SUCCESS_THRESHOLD and the exact tier cutoffs below are
reasonable guesses, not a verified 1:1 port. Adjust them to match your
actual DiceRoller if the numbers differ.
"""

import random
from dataclasses import dataclass, field


DIE_SIDES = 10
DEFAULT_SUCCESS_THRESHOLD = 8   # die result >= this counts as a success
EXPLODE_ON = 10                 # die result that triggers a reroll+add
BOTCH_ON_ONES = True            # zero successes + at least one natural 1 = botch
MAX_EXPLOSIONS_PER_DIE = 10     # safety cap against runaway loops


class ResultTier:
    """
    Ordered so `result.tier >= ResultTier.SUCCESS` works the same way
    the Godot call sites use `DiceRoller.ResultTier.SUCCESS`.
    """
    BOTCH = 0
    FAILURE = 1
    SUCCESS = 2
    CRITICAL = 3

    NAMES = {BOTCH: "BOTCH", FAILURE: "FAILURE", SUCCESS: "SUCCESS", CRITICAL: "CRITICAL"}


@dataclass
class DiceRollResult:
    """Structured result of a dice pool roll."""
    pool_size: int
    required_successes: int = 0
    threshold: int = DEFAULT_SUCCESS_THRESHOLD
    rolls: list = field(default_factory=list)
    successes: int = 0
    ones: int = 0
    exploded_count: int = 0
    tier: int = ResultTier.FAILURE
    margin: int = 0

    def __str__(self):
        tier_name = ResultTier.NAMES.get(self.tier, "?")
        return (
            f"Rolled {self.pool_size}d10 {self.rolls} -> "
            f"{self.successes} successes (need {self.required_successes}, "
            f"threshold {self.threshold}+) [{tier_name}]"
        )


def _roll_die():
    return random.randint(1, DIE_SIDES)


def roll_pool(pool_size, required_successes=1, threshold=DEFAULT_SUCCESS_THRESHOLD,
              bonus_dice=0, exploding=True):
    """
    Roll an exploding d10 dice pool.

    Args:
        pool_size (int): base dice count, usually attribute total + skill total.
        required_successes (int): successes needed to pass (SUCCESS tier).
        threshold (int): die value that counts as a success (default 8).
        bonus_dice (int): extra dice (race bonuses, gear, situational, etc.)
        exploding (bool): whether hitting EXPLODE_ON rerolls and adds a die.

    Returns:
        DiceRollResult
    """
    total_dice = max(0, int(pool_size) + int(bonus_dice))
    result = DiceRollResult(
        pool_size=total_dice,
        required_successes=required_successes,
        threshold=threshold,
    )

    if total_dice == 0:
        result.tier = ResultTier.BOTCH if BOTCH_ON_ONES else ResultTier.FAILURE
        return result

    to_roll = total_dice
    while to_roll > 0:
        die = _roll_die()
        result.rolls.append(die)
        to_roll -= 1

        if die == 1:
            result.ones += 1
        if die >= threshold:
            result.successes += 1
        if exploding and die == EXPLODE_ON and result.exploded_count < MAX_EXPLOSIONS_PER_DIE:
            result.exploded_count += 1
            to_roll += 1

    result.margin = result.successes - required_successes

    if BOTCH_ON_ONES and result.successes == 0 and result.ones > 0:
        result.tier = ResultTier.BOTCH
    elif result.successes >= required_successes:
        # Doubling the target (with at least 1 required) counts as a
        # critical. Tune this to match your real crit rule.
        if required_successes > 0 and result.successes >= required_successes * 2:
            result.tier = ResultTier.CRITICAL
        else:
            result.tier = ResultTier.SUCCESS
    else:
        result.tier = ResultTier.FAILURE

    return result


def resolve_contest(pool_a, pool_b, threshold=DEFAULT_SUCCESS_THRESHOLD,
                     bonus_dice_a=0, bonus_dice_b=0):
    """
    Opposed roll between two dice pools (e.g. Perception vs Stealth).
    Returns (result_a, result_b, winner) where winner is "a", "b", or "tie".
    """
    result_a = roll_pool(pool_a, required_successes=0, threshold=threshold, bonus_dice=bonus_dice_a)
    result_b = roll_pool(pool_b, required_successes=0, threshold=threshold, bonus_dice=bonus_dice_b)

    if result_a.successes > result_b.successes:
        winner = "a"
    elif result_b.successes > result_a.successes:
        winner = "b"
    else:
        winner = "tie"

    return result_a, result_b, winner
