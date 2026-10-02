"""Training and progression (Plan.md §9.6): XP, levels, stages, unlocks, stat gains, costs.

Pure: every function takes the state it needs and returns new values. The numbers come from
data/game/progression.yaml.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.engines.care import MOODS, Mood, Need
from app.engines.game_data import GAME_DIR, Stat

ActivityId = Literal["flight", "speed", "accuracy", "memory", "obedience"]

Positive = Annotated[int, Field(ge=0)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Stage(_Model):
    id: str
    label: str
    from_level: Annotated[int, Field(ge=1)]


class Activity(_Model):
    id: ActivityId
    label: str
    description: str
    trains: tuple[Stat, ...]
    stage: str
    energy_cost: Annotated[int, Field(ge=0, le=100)]
    min_ms: Positive
    max_ms: Positive


class Refuse(_Model):
    energy_below: Annotated[int, Field(ge=0, le=100)]
    hunger_above: Annotated[int, Field(ge=0, le=100)]


class HappinessRule(_Model):
    good_score: Annotated[int, Field(ge=0, le=100)]
    bonus: Positive
    poor_score: Annotated[int, Field(ge=0, le=100)]
    penalty: Positive


class NeedsMet(_Model):
    hunger_max: Annotated[int, Field(ge=0, le=100)]
    energy_min: Annotated[int, Field(ge=0, le=100)]


class TrustRule(_Model):
    per_session: Positive
    needs_met_bonus: Positive
    needs_met: NeedsMet


class Curve(_Model):
    scale: Annotated[float, Field(gt=0)]
    power: Annotated[float, Field(gt=0)]


class Messages(_Model):
    refused_tired: str
    refused_hungry: str
    locked: str
    great: str
    good: str
    poor: str


class Progression(_Model):
    version: str
    max_level: Annotated[int, Field(ge=1)]
    xp_base: float
    xp_per_point: float
    xp_curve: Curve
    stat_gain: Annotated[float, Field(ge=0)]
    mood_mult: dict[Mood, Annotated[float, Field(gt=0, le=3)]]
    costs: dict[Literal["hunger"], Annotated[int, Field(ge=0, le=100)]]
    refuse: Refuse
    happiness: HappinessRule
    trust: TrustRule
    session_expires_minutes: Annotated[int, Field(ge=1)]
    stages: tuple[Stage, ...]
    activities: tuple[Activity, ...]
    messages: Messages

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if missing := set(MOODS) - set(self.mood_mult):
            raise ValueError(f"progression.yaml: no mood_mult for {sorted(missing)}")
        levels = [s.from_level for s in self.stages]
        if not levels or levels[0] != 1 or levels != sorted(set(levels)):
            raise ValueError("progression.yaml: stages must start at level 1 and go up")
        stage_ids = {s.id for s in self.stages}
        for a in self.activities:
            if a.stage not in stage_ids:
                raise ValueError(f"progression.yaml: {a.id} unlocks at unknown stage {a.stage}")
            if not a.min_ms < a.max_ms:
                raise ValueError(f"progression.yaml: {a.id} needs min_ms < max_ms")
        if len({a.id for a in self.activities}) != len(self.activities):
            raise ValueError("progression.yaml: activity ids must be unique")
        return self

    def activity(self, activity_id: str) -> Activity:
        for a in self.activities:
            if a.id == activity_id:
                return a
        raise KeyError(activity_id)

    def stage(self, stage_id: str) -> Stage:
        return next(s for s in self.stages if s.id == stage_id)


def load_progression(game_dir: Path = GAME_DIR) -> Progression:
    with (game_dir / "progression.yaml").open(encoding="utf-8") as fh:
        return Progression.model_validate(yaml.safe_load(fh))


@lru_cache
def get_progression() -> Progression:
    return load_progression()


# ── levels and unlocks ───────────────────────────────────────────────────────


def xp_to_next(rules: Progression, level: int) -> int | None:
    """XP needed to go from `level` to the next; None at the top level."""
    if level >= rules.max_level:
        return None
    return round(rules.xp_curve.scale * math.pow(level, rules.xp_curve.power))


def stage_for(rules: Progression, level: int) -> Stage:
    return [s for s in rules.stages if s.from_level <= level][-1]


def unlocked(rules: Progression, level: int) -> list[Activity]:
    reached = {s.id for s in rules.stages if s.from_level <= level}
    return [a for a in rules.activities if a.stage in reached]


# ── starting a session ───────────────────────────────────────────────────────


class Locked(Exception):
    """The activity needs a later stage."""


class Refused(Exception):
    """The dragon won't train right now; the message says why."""


def check_can_train(
    rules: Progression, activity: Activity, *, name: str, level: int, needs: Mapping[Need, int]
) -> None:
    """Raises Locked or Refused (Plan §9.6: below 15 energy or above 85 hunger)."""
    if activity not in unlocked(rules, level):
        stage = rules.stage(activity.stage)
        raise Locked(
            rules.messages.locked.format(
                activity=activity.label, name=name, stage=stage.label, level=stage.from_level
            )
        )
    if needs["energy"] < rules.refuse.energy_below:
        raise Refused(rules.messages.refused_tired.format(name=name))
    if needs["hunger"] > rules.refuse.hunger_above:
        raise Refused(rules.messages.refused_hungry.format(name=name))


# ── finishing a session ──────────────────────────────────────────────────────


class Implausible(ValueError):
    """The reported duration can't be a real attempt."""


def check_duration(activity: Activity, duration_ms: int, elapsed_ms: float) -> None:
    """The attempt must fit the activity's range and the time since the session started."""
    if not activity.min_ms <= duration_ms <= activity.max_ms:
        raise Implausible(
            f"{activity.label} takes {activity.min_ms}-{activity.max_ms} ms; got {duration_ms}"
        )
    if duration_ms > elapsed_ms + 5000:  # a little slack for clock and network
        raise Implausible("The attempt can't be longer than the session")


@dataclass(frozen=True)
class TrainingOutcome:
    xp_gained: int
    stat_deltas: dict[Stat, int]
    stats: dict[Stat, int]
    level: int
    xp: int  # progress toward the next level
    level_ups: tuple[int, ...]  # every level reached, in order
    stage: Stage
    new_activities: tuple[str, ...]  # activity ids unlocked by this session
    needs: dict[Need, int]
    trust: int
    message: str


def complete(
    rules: Progression,
    activity: Activity,
    *,
    name: str,
    score: int,
    mood: Mood,
    needs_at_start: Mapping[Need, int],
    needs: Mapping[Need, int],
    trust: int,
    stats: Mapping[Stat, int],
    caps: Mapping[Stat, int],
    level: int,
    xp: int,
) -> TrainingOutcome:
    """Apply a finished session's XP, stat gains and costs (Plan §9.6 formulas)."""
    mult = rules.mood_mult[mood]
    xp_gained = round((rules.xp_base + rules.xp_per_point * score) * mult)

    deltas: dict[Stat, int] = {}
    new_stats = dict(stats)
    for stat in activity.trains:
        cap = caps[stat]
        gain = rules.stat_gain * (score / 100) * (1 - stats[stat] / cap) * mult if cap else 0
        new_stats[stat] = min(cap, stats[stat] + round(gain))
        deltas[stat] = new_stats[stat] - stats[stat]

    new_level, new_xp, level_ups = level, xp + xp_gained, []
    while (need := xp_to_next(rules, new_level)) is not None and new_xp >= need:
        new_xp -= need
        new_level += 1
        level_ups.append(new_level)

    before = {a.id for a in unlocked(rules, level)}
    new_activities = tuple(a.id for a in unlocked(rules, new_level) if a.id not in before)

    happiness = 0
    if score >= rules.happiness.good_score:
        happiness = rules.happiness.bonus
    elif score < rules.happiness.poor_score:
        happiness = -rules.happiness.penalty
    met = rules.trust.needs_met
    needs_were_met = (
        needs_at_start["hunger"] <= met.hunger_max and needs_at_start["energy"] >= met.energy_min
    )
    trust_gain = rules.trust.per_session + (rules.trust.needs_met_bonus if needs_were_met else 0)

    message = (
        rules.messages.great
        if score >= rules.happiness.good_score
        else rules.messages.poor
        if score < rules.happiness.poor_score
        else rules.messages.good
    )
    return TrainingOutcome(
        xp_gained=xp_gained,
        stat_deltas=deltas,
        stats=new_stats,
        level=new_level,
        xp=new_xp,
        level_ups=tuple(level_ups),
        stage=stage_for(rules, new_level),
        new_activities=new_activities,
        needs={
            "hunger": _clamp(needs["hunger"] + rules.costs["hunger"]),
            "energy": _clamp(needs["energy"] - activity.energy_cost),
            "happiness": _clamp(needs["happiness"] + happiness),
        },
        trust=_clamp(trust + trust_gain),
        message=message.format(name=name),
    )


def _clamp(value: float) -> int:
    return max(0, min(100, round(value)))
