"""Looking after a dragon (Plan.md §9.6-9.7): needs over time, care actions, mood, thoughts.

Pure: every function takes the time and state it needs, so the same inputs always give the
same result. The numbers come from data/game/care.yaml.
"""

import random
from collections.abc import Collection, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.engines.game_data import GAME_DIR

Need = Literal["hunger", "energy", "happiness"]
NEEDS: tuple[Need, ...] = ("hunger", "energy", "happiness")
Action = Literal["feed", "rest", "play"]
Mood = Literal["hungry", "tired", "angry", "excited", "curious", "happy"]
MOODS: tuple[Mood, ...] = ("hungry", "tired", "angry", "excited", "curious", "happy")

Change = Annotated[int, Field(ge=-100, le=100)]
Level = Annotated[int, Field(ge=0, le=100)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Effect(_Model):
    """Changes to needs and trust."""

    hunger: Change = 0
    energy: Change = 0
    happiness: Change = 0
    trust: Change = 0


class ActionRule(_Model):
    changes: Effect
    liked: Effect = Effect()
    disliked: Effect = Effect()
    refuse_below: dict[Need, Level] = {}
    refuse_above: dict[Need, Level] = {}


class Messages(_Model):
    fed_liked: str
    fed: str
    fed_disliked: str
    rested: str
    played: str
    refused_feed: str
    refused_rest: str
    refused_play: str


class CareRules(_Model):
    version: str
    decay_per_hour: dict[Need, Annotated[float, Field(ge=-50, le=50)]]
    actions: dict[Action, ActionRule]
    messages: Messages
    thoughts: dict[Mood, tuple[str, ...]]

    @model_validator(mode="after")
    def _complete(self) -> Self:
        if missing := set(MOODS) - {m for m, lines in self.thoughts.items() if lines}:
            raise ValueError(f"care.yaml: no thoughts for moods {sorted(missing)}")
        if missing_actions := {"feed", "rest", "play"} - set(self.actions):
            raise ValueError(f"care.yaml: no rules for actions {sorted(missing_actions)}")
        return self


def load_care(game_dir: Path = GAME_DIR) -> CareRules:
    with (game_dir / "care.yaml").open(encoding="utf-8") as fh:
        return CareRules.model_validate(yaml.safe_load(fh))


@lru_cache
def get_care() -> CareRules:
    return load_care()


# ── needs over time ──────────────────────────────────────────────────────────


def decay(
    rules: CareRules, needs: Mapping[str, int] | Mapping[Need, int], hours: float
) -> dict[Need, int]:
    """Needs after `hours` away: each drifts by its hourly rate, kept within 0-100."""
    hours = max(0.0, hours)  # a clock running backwards changes nothing
    return {n: _clamp(needs[n] + rules.decay_per_hour.get(n, 0) * hours) for n in NEEDS}


# ── care actions ─────────────────────────────────────────────────────────────


class Refused(Exception):
    """The dragon won't do it right now; the message says why, in the dragon's voice."""


@dataclass(frozen=True)
class CareOutcome:
    needs: dict[Need, int]
    trust: int
    event: str  # what to record: fed, rested or played
    message: str
    detail: dict[str, str]  # extra facts for the event log, e.g. the food


def care(
    rules: CareRules,
    action: Action,
    *,
    name: str,
    needs: Mapping[Need, int],
    trust: int,
    likes: Collection[str] = (),
    dislikes: Collection[str] = (),
    food: str | None = None,
) -> CareOutcome:
    """Apply a care action to current (already decayed) needs. Raises Refused."""
    rule = rules.actions[action]
    words = {"name": name, "food": food or ""}
    too_low = any(needs[n] < limit for n, limit in rule.refuse_below.items())
    too_high = any(needs[n] > limit for n, limit in rule.refuse_above.items())
    if too_low or too_high:
        raise Refused(getattr(rules.messages, f"refused_{action}").format(**words))

    effects = [rule.changes]
    event = {"feed": "fed", "rest": "rested", "play": "played"}[action]
    message_key = event
    detail: dict[str, str] = {}
    if action == "feed":
        if food is None:
            raise ValueError("feeding needs a food")
        detail["food"] = food
        if food in likes:
            effects.append(rule.liked)
            message_key = "fed_liked"
        elif food in dislikes:
            effects.append(rule.disliked)
            message_key = "fed_disliked"

    new_needs = {n: _clamp(needs[n] + sum(getattr(e, n) for e in effects)) for n in NEEDS}
    new_trust = _clamp(trust + sum(e.trust for e in effects))
    return CareOutcome(
        needs=new_needs,
        trust=new_trust,
        event=event,
        message=getattr(rules.messages, message_key).format(**words),
        detail=detail,
    )


# ── mood and thoughts ────────────────────────────────────────────────────────

# Events that sour a low-trust dragon's mood for an hour (Plan §9.7). They arrive with training.
SOURING_EVENTS = frozenset({"refused", "overtrained"})


def mood(
    needs: Mapping[Need, int],
    trust: int,
    curiosity: int,
    recent_events: Collection[str] = (),
) -> Mood:
    """The Plan's mood table: the first rule that matches wins.

    Scared (after a storm in a story or encounter) comes with those features; until then the
    table starts at Hungry. `recent_events` are the kinds logged in the last hour.
    """
    if needs["hunger"] > 70:
        return "hungry"
    if needs["energy"] < 25:
        return "tired"
    if trust < 25 and SOURING_EVENTS & set(recent_events):
        return "angry"
    if needs["happiness"] > 75 and needs["energy"] > 60:
        return "excited"
    if curiosity > 65:
        return "curious"
    return "happy"


def thought(rules: CareRules, current: Mood, name: str, seed: str) -> str:
    """One of the mood's idle lines. `seed` (e.g. dragon id + hour) keeps it steady on reload."""
    lines = rules.thoughts[current]
    return random.Random(f"{rules.version}:{seed}").choice(lines).format(name=name)


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))
