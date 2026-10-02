"""Rolling a newly adopted dragon (Plan.md §9.5). Pure: the same seed gives the same dragon.

The rules come from data/game/adoption.yaml; the species' traits, diet and stat caps from
species_profiles.yaml.
"""

import random
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.engines.game_data import (
    GAME_DIR,
    TRAITS,
    GameData,
    SpeciesProfile,
    Stat,
    Trait,
    get_game_data,
)

Share = Annotated[float, Field(ge=0, le=1)]
Score = Annotated[int, Field(ge=0, le=100)]


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Range(_Model):
    min: float
    max: float

    @model_validator(mode="after")
    def _ordered(self) -> Self:
        if self.min > self.max:
            raise ValueError("min must not exceed max")
        return self


class Needs(_Model):
    hunger: Score
    energy: Score
    happiness: Score


class Start(_Model):
    needs: Needs
    trust: Score


class NameRules(_Model):
    min_length: Annotated[int, Field(ge=1)]
    max_length: Annotated[int, Field(le=40)]


class Quirk(_Model):
    id: str
    label: str
    likes: tuple[str, ...] = ()
    dislikes: tuple[str, ...] = ()


class Adoption(_Model):
    version: str
    personality_sigma: Annotated[float, Field(ge=0, le=25)]
    stat_start: Range
    quirks_per_dragon: Range
    start: Start
    name: NameRules
    quirks: tuple[Quirk, ...]
    color_variants: dict[str, tuple[str, ...]]

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if not 0 <= self.stat_start.min <= self.stat_start.max <= 1:
            raise ValueError("stat_start must be shares between 0 and 1")
        if self.quirks_per_dragon.max > len(self.quirks):
            raise ValueError("more quirks per dragon than quirks defined")
        if len({q.id for q in self.quirks}) != len(self.quirks):
            raise ValueError("quirk ids must be unique")
        if empty := [s for s, colors in self.color_variants.items() if not colors]:
            raise ValueError(f"no color variants for {empty}")
        return self

    def check_species(self, data: GameData) -> Self:
        """Every matchable species needs colours (and only matchable species have them)."""
        matchable = {s.id for s in data.species}
        if missing := matchable - set(self.color_variants):
            raise ValueError(f"adoption.yaml: no color_variants for {sorted(missing)}")
        if unknown := set(self.color_variants) - matchable:
            raise ValueError(f"adoption.yaml: color_variants for unknown species {sorted(unknown)}")
        return self


def load_adoption(game_dir: Path = GAME_DIR) -> Adoption:
    with (game_dir / "adoption.yaml").open(encoding="utf-8") as fh:
        return Adoption.model_validate(yaml.safe_load(fh))


@lru_cache
def get_adoption() -> Adoption:
    return load_adoption().check_species(get_game_data())


# ── rolling a dragon ─────────────────────────────────────────────────────────


@dataclass(frozen=True)
class NewDragon:
    species_id: str
    personality: dict[Trait, int]
    stats: dict[Stat, int]
    color_variant: str
    quirks: tuple[str, ...]  # quirk ids
    likes: tuple[str, ...]
    dislikes: tuple[str, ...]
    needs: dict[str, int]
    trust: int


def roll_dragon(adoption: Adoption, species: SpeciesProfile, seed: str) -> NewDragon:
    """A new dragon of `species`; `seed` (e.g. the quiz attempt id) makes it reproducible."""
    rng = random.Random(f"{adoption.version}:{seed}")
    personality = {
        t: _clamp(round(species.traits[t] + rng.gauss(0, adoption.personality_sigma)))
        for t in TRAITS
    }
    stats = {
        stat: round(cap * rng.uniform(adoption.stat_start.min, adoption.stat_start.max))
        for stat, cap in species.stat_caps.items()
    }
    count = rng.randint(int(adoption.quirks_per_dragon.min), int(adoption.quirks_per_dragon.max))
    quirks = rng.sample(adoption.quirks, count)
    return NewDragon(
        species_id=species.id,
        personality=personality,
        stats=stats,
        color_variant=rng.choice(adoption.color_variants[species.id]),
        quirks=tuple(q.id for q in quirks),
        likes=_unique((*species.diet_likes, *(like for q in quirks for like in q.likes))),
        dislikes=_unique((*species.diet_dislikes, *(d for q in quirks for d in q.dislikes))),
        needs=adoption.start.needs.model_dump(),
        trust=adoption.start.trust,
    )


# ── names ────────────────────────────────────────────────────────────────────


class InvalidName(ValueError):
    pass


# A short list on purpose: it catches the obvious, and whole words only, so names like
# "Cassandra" or "Scunthorpe" aren't blocked.
_BLOCKED = frozenset(
    {
        "arse", "ass", "asshole", "bastard", "bitch", "bollocks", "cock", "cunt", "dick",
        "fag", "faggot", "fuck", "fucker", "nazi", "nigga", "nigger", "piss", "porn",
        "prick", "pussy", "rape", "retard", "shit", "slut", "twat", "wank", "whore",
    }
)  # fmt: skip
_ALLOWED = re.compile(r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$")


def clean_name(adoption: Adoption, raw: str) -> str:
    """The name to store: trimmed with single spaces. Raises InvalidName with a reason."""
    name = " ".join(raw.split())
    rules = adoption.name
    if not rules.min_length <= len(name) <= rules.max_length:
        raise InvalidName(f"Names are {rules.min_length} to {rules.max_length} characters long")
    if not _ALLOWED.match(name):
        raise InvalidName("Use letters, with single spaces, hyphens or apostrophes between them")
    words = re.split(r"[ '\-]", name.lower())
    if any(w in _BLOCKED for w in [*words, "".join(words)]):
        raise InvalidName("Please choose a kinder name")
    return name


def _clamp(value: int) -> int:
    return max(0, min(100, value))


def _unique(items: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(items))
