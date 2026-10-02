"""Care rules: needs over time, care actions, mood and thoughts (Plan.md §9.6-9.7). No database."""

import pytest

from app.engines.care import (
    Action,
    CareOutcome,
    CareRules,
    Need,
    Refused,
    care,
    decay,
    load_care,
    mood,
    thought,
)


@pytest.fixture(scope="module")
def rules() -> CareRules:
    return load_care()


Needs = dict[Need, int]
START: Needs = {"hunger": 30, "energy": 80, "happiness": 60}


def test_needs_drift_while_away(rules: CareRules) -> None:
    assert decay(rules, START, 5) == {"hunger": 50, "energy": 100, "happiness": 50}
    assert decay(rules, START, 0) == START


def test_needs_stay_within_bounds(rules: CareRules) -> None:
    assert decay(rules, START, 1000) == {"hunger": 100, "energy": 100, "happiness": 0}


def test_a_clock_running_backwards_changes_nothing(rules: CareRules) -> None:
    assert decay(rules, START, -3) == START


def _feed(rules: CareRules, food: str, needs: Needs = START, trust: int = 20) -> CareOutcome:
    return care(
        rules,
        "feed",
        name="Ember",
        needs=needs,
        trust=trust,
        likes=["fish"],
        dislikes=["eel"],
        food=food,
    )


def test_feeding_a_liked_food_pleases_most(rules: CareRules) -> None:
    liked, plain, disliked = (_feed(rules, f) for f in ("fish", "bread", "eel"))
    for outcome in (liked, plain, disliked):
        assert outcome.needs["hunger"] == 0
    happiness = [o.needs["happiness"] for o in (liked, plain, disliked)]
    assert happiness[0] > happiness[1] > happiness[2]
    trust = [o.trust for o in (liked, plain, disliked)]
    assert trust[0] > trust[1] > trust[2]
    assert liked.message == "Ember gobbles the fish and hums happily."
    assert liked.detail == {"food": "fish"}


def test_trust_never_drops_below_zero(rules: CareRules) -> None:
    assert _feed(rules, "eel", trust=0).trust == 0


@pytest.mark.parametrize(
    ("action", "needs", "reason"),
    [
        ("feed", {**START, "hunger": 5}, "isn't hungry"),
        ("rest", {**START, "energy": 95}, "wide awake"),
        ("play", {**START, "energy": 10}, "too tired"),
    ],
)
def test_the_dragon_says_no_with_a_reason(
    rules: CareRules, action: Action, needs: Needs, reason: str
) -> None:
    with pytest.raises(Refused, match=reason) as refused:
        care(rules, action, name="Ember", needs=needs, trust=20, food="fish")
    assert "Ember" in str(refused.value)


def test_rest_and_play(rules: CareRules) -> None:
    tired: Needs = {**START, "energy": 30}
    assert care(rules, "rest", name="E", needs=tired, trust=20).needs["energy"] == 65
    played = care(rules, "play", name="E", needs=START, trust=20)
    assert played.needs["happiness"] == 75 and played.needs["energy"] == 65
    assert played.trust == 22
    assert played.event == "played"


@pytest.mark.parametrize(
    ("needs", "trust", "curiosity", "events", "expected"),
    [
        # Hungry wins over everything below it, even being tired.
        ({"hunger": 80, "energy": 10, "happiness": 90}, 50, 90, (), "hungry"),
        ({"hunger": 30, "energy": 10, "happiness": 90}, 50, 90, (), "tired"),
        ({"hunger": 30, "energy": 50, "happiness": 50}, 10, 90, ("refused",), "angry"),
        # Low trust alone doesn't make it angry.
        ({"hunger": 30, "energy": 50, "happiness": 50}, 10, 20, (), "happy"),
        ({"hunger": 30, "energy": 70, "happiness": 80}, 50, 90, (), "excited"),
        ({"hunger": 30, "energy": 50, "happiness": 50}, 50, 70, (), "curious"),
        ({"hunger": 30, "energy": 50, "happiness": 50}, 50, 50, (), "happy"),
    ],
)
def test_mood_takes_the_first_rule_that_matches(
    needs: Needs, trust: int, curiosity: int, events: tuple[str, ...], expected: str
) -> None:
    assert mood(needs, trust, curiosity, events) == expected


def test_thoughts_are_steady_and_use_the_name(rules: CareRules) -> None:
    line = thought(rules, "hungry", "Ember", "dragon-1:2026-10-03T09")
    assert line == thought(rules, "hungry", "Ember", "dragon-1:2026-10-03T09")
    assert "Ember" in line and "{" not in line
    lines = {thought(rules, "happy", "Ember", f"dragon-1:hour-{h}") for h in range(24)}
    assert len(lines) > 1
