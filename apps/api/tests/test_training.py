"""Training and progression rules (Plan.md §9.6). No database needed.

The property tests (Hypothesis) check the Plan's promises over many random inputs: a higher
score never gives less XP, and stats never go past their caps.
"""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from app.engines.care import MOODS, Need
from app.engines.game_data import Stat, load_game_data
from app.engines.training import (
    Implausible,
    Locked,
    Progression,
    Refused,
    TrainingOutcome,
    check_can_train,
    check_duration,
    complete,
    load_progression,
    stage_for,
    unlocked,
    xp_to_next,
)

RULES = load_progression()
GAME = load_game_data()
NADDER = next(s for s in GAME.species if s.id == "deadly_nadder")
FLIGHT = RULES.activity("flight")
WELL: dict[Need, int] = {"hunger": 30, "energy": 80, "happiness": 60}


def _train(
    score: int,
    *,
    mood: str = "curious",
    level: int = 1,
    xp: int = 0,
    stats: dict[Stat, int] | None = None,
    needs_at_start: dict[Need, int] = WELL,
    rules: Progression = RULES,
) -> TrainingOutcome:
    return complete(
        rules,
        FLIGHT,
        name="Ember",
        score=score,
        mood=mood,  # type: ignore[arg-type]
        needs_at_start=needs_at_start,
        needs=WELL,
        trust=20,
        stats=stats or {s: 30 for s in NADDER.stat_caps},
        caps=NADDER.stat_caps,
        level=level,
        xp=xp,
    )


def test_xp_follows_the_plan_formula() -> None:
    # round((20 + 0.6 x 80) x 1.0) = 68 for a curious dragon; x1.2 when excited.
    assert _train(80).xp_gained == 68
    assert _train(80, mood="excited").xp_gained == 82


def test_the_xp_curve() -> None:
    assert xp_to_next(RULES, 1) == 100
    assert xp_to_next(RULES, 4) == 800
    assert xp_to_next(RULES, RULES.max_level) is None


def test_levelling_can_skip_several_levels_and_keeps_the_rest() -> None:
    outcome = _train(100, xp=99 + 283)  # level 1 needs 100, level 2 needs 283
    assert outcome.level_ups == (2, 3)
    assert outcome.level == 3
    assert outcome.xp == outcome.xp_gained - 1


def test_stages_and_unlocks() -> None:
    assert stage_for(RULES, 4).id == "newborn"
    assert stage_for(RULES, 5).id == "young"
    assert stage_for(RULES, 30).id == "master"
    assert [a.id for a in unlocked(RULES, 1)] == ["flight", "speed"]
    assert {a.id for a in unlocked(RULES, 10)} == {
        "flight",
        "speed",
        "accuracy",
        "memory",
        "obedience",
    }


def test_reaching_a_stage_reports_new_activities() -> None:
    outcome = _train(100, level=4, xp=799)
    assert outcome.level == 5
    assert outcome.stage.id == "young"
    assert set(outcome.new_activities) == {"accuracy", "memory"}


def test_stat_gains_shrink_near_the_cap() -> None:
    low = _train(100, stats={**{s: 30 for s in NADDER.stat_caps}, "agility": 10})
    high = _train(100, stats={**{s: 30 for s in NADDER.stat_caps}, "agility": 90})
    assert low.stat_deltas["agility"] > high.stat_deltas["agility"]
    assert set(low.stat_deltas) == set(FLIGHT.trains)


def test_training_costs_energy_and_hunger_and_builds_trust() -> None:
    outcome = _train(80)
    assert outcome.needs["energy"] == WELL["energy"] - FLIGHT.energy_cost
    assert outcome.needs["hunger"] == WELL["hunger"] + 8
    assert outcome.needs["happiness"] == WELL["happiness"] + 5  # a good score
    assert outcome.trust == 23  # +2, +1 because its needs were met
    assert _train(80, needs_at_start={"hunger": 80, "energy": 80, "happiness": 60}).trust == 22
    assert _train(10).needs["happiness"] == WELL["happiness"] - 5  # a poor score


@pytest.mark.parametrize(
    ("needs", "level", "activity", "error", "reason"),
    [
        ({**WELL, "energy": 10}, 1, "flight", Refused, "exhausted"),
        ({**WELL, "hunger": 90}, 1, "flight", Refused, "too hungry"),
        (WELL, 1, "accuracy", Locked, "Young stage"),
    ],
)
def test_when_it_wont_train(
    needs: dict[Need, int], level: int, activity: str, error: type[Exception], reason: str
) -> None:
    with pytest.raises(error, match=reason):
        check_can_train(RULES, RULES.activity(activity), name="Ember", level=level, needs=needs)


def test_plausible_durations() -> None:
    check_duration(FLIGHT, 10_000, elapsed_ms=12_000)
    with pytest.raises(Implausible):
        check_duration(FLIGHT, 100, elapsed_ms=12_000)  # too quick to be real
    with pytest.raises(Implausible):
        check_duration(FLIGHT, 60_000, elapsed_ms=12_000)  # longer than the session


scores = st.integers(min_value=0, max_value=100)


@given(a=scores, b=scores, mood=st.sampled_from(MOODS))
def test_a_higher_score_never_gives_less_xp(a: int, b: int, mood: str) -> None:
    low, high = sorted((a, b))
    assert _train(low, mood=mood).xp_gained <= _train(high, mood=mood).xp_gained


@given(
    score=scores,
    mood=st.sampled_from(MOODS),
    start=st.dictionaries(
        st.sampled_from(sorted(NADDER.stat_caps)), st.integers(0, 100), min_size=7
    ),
)
def test_stats_never_pass_their_caps(score: int, mood: str, start: dict[Stat, int]) -> None:
    stats = {s: min(v, NADDER.stat_caps[s]) for s, v in start.items()}
    outcome = _train(score, mood=mood, stats=stats)
    for stat, value in outcome.stats.items():
        assert stats[stat] <= value <= NADDER.stat_caps[stat]
