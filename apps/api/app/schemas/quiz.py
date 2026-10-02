"""Request and response models for the personality quiz (Plan.md §9.2, §10)."""

from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class QuizOption(BaseModel):
    id: str
    label: str


class QuizQuestion(BaseModel):
    id: str
    prompt: str
    options: list[QuizOption] = Field(description="In this player's shuffled order")


class Quiz(BaseModel):
    version: str = Field(examples=["quiz_v1"])
    questions: list[QuizQuestion]


class QuizAttemptCreate(BaseModel):
    quiz_version: str = Field(examples=["quiz_v1"])
    answers: dict[str, str] = Field(
        description="Chosen option id per question id; every question exactly once",
        examples=[{"q01_injured_dragon": "a"}],
    )


class TraitScore(BaseModel):
    id: str = Field(examples=["courage"])
    label: str = Field(examples=["Courage"])
    score: int = Field(ge=0, le=100, description="0-100 within what this quiz allows")
    low: str = Field(description="What a low score means")
    high: str = Field(description="What a high score means")


class QuizAttempt(BaseModel):
    id: UUID
    quiz_version: str
    traits: list[TraitScore]


# ── encounter (Plan.md §9.4) ─────────────────────────────────────────────────


class EncounterScene(BaseModel):
    id: Literal["first_contact", "offering", "startle"]
    prompt: str
    options: list[QuizOption] = Field(description="In this player's shuffled order")


class Encounter(BaseModel):
    version: str = Field(examples=["encounter_v1"])
    scenes: list[EncounterScene] = Field(description="In the order they are played")


class EncounterChoices(BaseModel):
    encounter_version: str = Field(examples=["encounter_v1"])
    first_contact: str = Field(examples=["stay_still"])
    offering: str = Field(examples=["fish"])
    startle: str = Field(examples=["calm_it"])


class DragonMatch(BaseModel):
    species_id: str = Field(examples=["night_fury"])
    name: str = Field(examples=["Night Fury"])
    rarity: str = Field(examples=["legendary"])
    summary: str
    compatibility: int = Field(ge=60, le=99, description="Displayed compatibility, 60-99%")
    explanation: str


class QuizMatch(BaseModel):
    top: DragonMatch
    runners_up: list[DragonMatch]


class QuizAttemptDetail(QuizAttempt):
    match: QuizMatch | None = Field(description="Set once the encounter is done")
