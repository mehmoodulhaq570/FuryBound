"""Typed loading of the game-balancing data in data/game/ (layer 3, Plan.md §3 and §9.2-9.4).

Everything is validated on load, including the quiz authoring rules, so a broken YAML edit
fails loudly in tests and CI instead of producing odd matches.
"""

from functools import lru_cache
from pathlib import Path
from typing import Annotated, Literal, Self

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

GAME_DIR = Path(__file__).resolve().parents[4] / "data" / "game"

Trait = Literal[
    "courage", "curiosity", "loyalty", "aggression", "patience", "independence", "intelligence"
]
TRAITS: tuple[Trait, ...] = (
    "courage",
    "curiosity",
    "loyalty",
    "aggression",
    "patience",
    "independence",
    "intelligence",
)
Approach = Literal["calm", "bold", "gentle", "playful"]
Food = Literal["fish", "chicken", "mutton", "rock", "bread", "eel"]
Stat = Literal["speed", "agility", "strength", "firepower", "stamina", "intelligence", "obedience"]
Rarity = Literal["common", "uncommon", "rare", "legendary"]

Score = Annotated[int, Field(ge=0, le=100)]
Delta = Annotated[int, Field(ge=-10, le=15)]

MIN_QUESTIONS_PER_TRAIT = 4


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


# ── traits.yaml ──────────────────────────────────────────────────────────────


class TraitDef(_Model):
    id: Trait
    label: str
    player: str
    dragon: str
    low: str
    high: str


class TraitsFile(_Model):
    version: str
    traits: tuple[TraitDef, ...]

    @model_validator(mode="after")
    def _all_traits_in_order(self) -> Self:
        if tuple(t.id for t in self.traits) != TRAITS:
            raise ValueError(f"traits must be exactly {TRAITS}, in that order")
        return self


# ── quiz_v1.yaml ─────────────────────────────────────────────────────────────


class QuizOption(_Model):
    id: str
    label: str
    deltas: dict[Trait, Delta]


class QuizQuestion(_Model):
    id: str
    prompt: str
    options: tuple[QuizOption, QuizOption, QuizOption, QuizOption]

    @model_validator(mode="after")
    def _unique_option_ids(self) -> Self:
        if len({o.id for o in self.options}) != len(self.options):
            raise ValueError(f"{self.id}: option ids must be unique")
        return self

    def option(self, option_id: str) -> QuizOption:
        for opt in self.options:
            if opt.id == option_id:
                return opt
        raise KeyError(f"{self.id}: no option {option_id!r}")


class Quiz(_Model):
    version: str
    questions: Annotated[tuple[QuizQuestion, ...], Field(min_length=10, max_length=15)]

    @model_validator(mode="after")
    def _authoring_rules(self) -> Self:
        if len({q.id for q in self.questions}) != len(self.questions):
            raise ValueError("question ids must be unique")
        for trait in TRAITS:
            touched = sum(any(trait in o.deltas for o in q.options) for q in self.questions)
            if touched < MIN_QUESTIONS_PER_TRAIT:
                raise ValueError(
                    f"{trait} is touched by {touched} questions; "
                    f"needs at least {MIN_QUESTIONS_PER_TRAIT}"
                )
        return self

    def bounds(self, trait: Trait) -> tuple[int, int]:
        """Lowest and highest raw total a player can reach for one trait."""
        low = sum(min(o.deltas.get(trait, 0) for o in q.options) for q in self.questions)
        high = sum(max(o.deltas.get(trait, 0) for o in q.options) for q in self.questions)
        return low, high


# ── species_profiles.yaml ────────────────────────────────────────────────────


class SpeciesProfile(_Model):
    id: str
    rarity: Rarity
    summary: str
    traits: dict[Trait, Score]
    weights: dict[Trait, Annotated[float, Field(gt=0, le=3)]]
    requirements: dict[Trait, Score]
    approach_pref: Approach
    diet_likes: tuple[Food, ...]
    diet_dislikes: tuple[Food, ...]
    stat_caps: dict[Stat, Score]

    @model_validator(mode="after")
    def _complete(self) -> Self:
        if set(self.traits) != set(TRAITS):
            raise ValueError(f"{self.id}: traits must list all of {TRAITS}")
        if set(self.diet_likes) & set(self.diet_dislikes):
            raise ValueError(f"{self.id}: a food can't be both liked and disliked")
        return self

    def weight(self, trait: Trait) -> float:
        return self.weights.get(trait, 1.0)


class ProfilesFile(_Model):
    version: str
    foods: tuple[Food, ...]
    stats: tuple[Stat, ...]
    species: tuple[SpeciesProfile, ...]

    @model_validator(mode="after")
    def _unique_and_complete(self) -> Self:
        ids = [s.id for s in self.species]
        if len(set(ids)) != len(ids):
            raise ValueError("species ids must be unique")
        for s in self.species:
            if set(s.stat_caps) != set(self.stats):
                raise ValueError(f"{s.id}: stat_caps must list all of {self.stats}")
        return self


# ── complements.yaml ─────────────────────────────────────────────────────────


class ComplementWhen(_Model):
    dragon: Trait
    gte: Score | None = None
    lte: Score | None = None

    @model_validator(mode="after")
    def _one_test(self) -> Self:
        if (self.gte is None) == (self.lte is None):
            raise ValueError("a complement rule needs exactly one of gte / lte")
        return self

    def fires(self, dragon: SpeciesProfile) -> bool:
        value = dragon.traits[self.dragon]
        return value >= self.gte if self.gte is not None else value <= (self.lte or 0)


class ComplementReward(_Model):
    trainer: Trait


class ComplementRule(_Model):
    id: str
    when: ComplementWhen
    reward: ComplementReward
    reason: str


class ComplementsFile(_Model):
    version: str
    rules: tuple[ComplementRule, ...]


# ── encounter_v1.yaml ────────────────────────────────────────────────────────


class ApproachOption(_Model):
    id: str
    label: str
    approach: Approach


class OfferingOption(_Model):
    id: str
    label: str
    food: Food


class StartleOption(_Model):
    id: str
    label: str
    deltas: dict[Trait, Delta]


class ApproachScene(_Model):
    prompt: str
    options: tuple[ApproachOption, ...]


class OfferingScene(_Model):
    prompt: str
    options: tuple[OfferingOption, ...]


class StartleScene(_Model):
    prompt: str
    options: tuple[StartleOption, ...]


class EncounterScenes(_Model):
    first_contact: ApproachScene
    offering: OfferingScene
    startle: StartleScene


class Encounter(_Model):
    version: str
    startle_weight: Annotated[float, Field(ge=0, le=1)]
    approach_opposites: dict[Approach, Approach]
    scenes: EncounterScenes


# ── all together ─────────────────────────────────────────────────────────────


class GameData(_Model):
    traits: TraitsFile
    quiz: Quiz
    profiles: ProfilesFile
    complements: ComplementsFile
    encounter: Encounter

    @property
    def species(self) -> tuple[SpeciesProfile, ...]:
        return self.profiles.species


def _read(path: Path) -> object:
    with path.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def load_game_data(game_dir: Path = GAME_DIR, quiz: str = "quiz_v1") -> GameData:
    return GameData(
        traits=TraitsFile.model_validate(_read(game_dir / "traits.yaml")),
        quiz=Quiz.model_validate(_read(game_dir / f"{quiz}.yaml")),
        profiles=ProfilesFile.model_validate(_read(game_dir / "species_profiles.yaml")),
        complements=ComplementsFile.model_validate(_read(game_dir / "complements.yaml")),
        encounter=Encounter.model_validate(_read(game_dir / "encounter_v1.yaml")),
    )


@lru_cache
def get_game_data() -> GameData:
    return load_game_data()
