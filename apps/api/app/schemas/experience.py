"""Habitat rewards and the authored rescue mission."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class Achievement(BaseModel):
    id: str
    title: str
    description: str
    earned: bool
    progress: int
    target: int
    decoration: str


class JournalEntry(BaseModel):
    id: int
    text: str
    at: datetime


class Milestone(BaseModel):
    label: str
    level: int
    xp_remaining: int


class AdventureState(BaseModel):
    id: UUID
    node: Literal["approach", "flight", "rescue", "complete"]
    approach: str | None = None
    training_session_id: UUID | None = None
    flight_finished: bool = False
    score: int | None = None
    outcome: str | None = None
    xp_reward: int = 0
    trust_reward: int = 0
    discovered_species: str | None = None


class Experience(BaseModel):
    achievements: list[Achievement]
    decoration: str
    milestone: Milestone | None
    journal: list[JournalEntry]
    adventure: AdventureState | None


class DecorationChoice(BaseModel):
    decoration: Literal["camp", "lanterns", "flowers", "pennant", "beacon"]


class AdventureChoice(BaseModel):
    choice: Literal["gentle", "bold", "clever", "continue", "untie", "lift"]


class HabitatPoint(BaseModel):
    x: float = Field(ge=7, le=90)
    y: float = Field(ge=30, le=90)


class HabitatLayout(BaseModel):
    positions: dict[Literal["lanterns", "flowers", "pennant", "beacon"], HabitatPoint]


class IslandState(BaseModel):
    treasures: list[str]
    lookout_unlocked: bool
    xp_reward: int
    layout: HabitatLayout
