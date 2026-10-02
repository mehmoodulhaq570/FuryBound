"""Request and response models for training (Plan.md §9.6, §10)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.dragons import PlayerDragon


class StageInfo(BaseModel):
    id: str = Field(examples=["newborn"])
    label: str = Field(examples=["Newborn"])


class TrainingActivity(BaseModel):
    id: str = Field(examples=["flight"])
    label: str = Field(examples=["Flight"])
    description: str
    trains: list[str] = Field(examples=[["agility", "speed"]])
    energy_cost: int
    unlocked: bool
    unlocks_at: StageInfo
    unlocks_at_level: int


class TrainingOverview(BaseModel):
    level: int
    xp: int
    xp_to_next: int | None
    stage: StageInfo
    activities: list[TrainingActivity]


class SessionStart(BaseModel):
    activity: str = Field(examples=["flight"])


class TrainingSession(BaseModel):
    id: UUID
    activity: str
    started_at: datetime
    min_ms: int = Field(description="Shortest plausible attempt")
    max_ms: int = Field(description="Longest plausible attempt")


class ActivityResult(BaseModel):
    """What every activity reports when it finishes (Plan §9.6 activity contract)."""

    score: int = Field(ge=0, le=100)
    duration_ms: int = Field(ge=0)
    meta: dict[str, Any] | None = None


class StatChange(BaseModel):
    id: str = Field(examples=["speed"])
    label: str = Field(examples=["Speed"])
    delta: int
    value: int


class TrainingResult(BaseModel):
    message: str = Field(examples=["Ember nailed it!"])
    score: int
    xp_gained: int
    stat_changes: list[StatChange]
    level_ups: list[int] = Field(description="Every level reached, in order (often empty)")
    stage: StageInfo
    new_activities: list[str] = Field(description="Activity ids this session unlocked")
    dragon: PlayerDragon


class HistoryEntry(BaseModel):
    id: UUID
    activity: str
    completed_at: datetime
    score: int
    xp_gained: int
    stat_deltas: dict[str, int]
    stats_after: dict[str, int]
