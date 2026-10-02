"""Request and response models for the player's dragon (Plan.md §9.5, §10)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class DragonAdopt(BaseModel):
    attempt_id: UUID = Field(description="The finished quiz attempt whose top match to adopt")
    name: str = Field(examples=["Ember"], description="2-20 letters; spaces, - and ' between")


class Labelled(BaseModel):
    id: str
    label: str
    value: int = Field(ge=0, le=100)


class Quirk(BaseModel):
    id: str = Field(examples=["hoards_shiny"])
    label: str = Field(examples=["Hoards shiny things"])


class MoodState(BaseModel):
    id: str = Field(examples=["hungry"])
    label: str = Field(examples=["Hungry"])


class PlayerDragon(BaseModel):
    id: UUID
    name: str
    species_id: str = Field(examples=["deadly_nadder"])
    species_name: str = Field(examples=["Deadly Nadder"])
    rarity: str
    compatibility: int | None = Field(description="From the quiz match, 60-99%")
    color_variant: str | None = Field(examples=["sky blue"])
    color_hex: str | None = Field(examples=["#4a90c8"], description="For drawing the dragon")
    personality: list[Labelled] = Field(description="Traits in the quiz's order")
    stats: list[Labelled]
    needs: list[Labelled] = Field(description="Hunger, energy and happiness, as of now")
    mood: MoodState
    thought: str = Field(description="What the dragon is up to (changes every hour)")
    foods: list[str] = Field(description="What can be offered when feeding")
    quirks: list[Quirk]
    likes: list[str]
    dislikes: list[str]
    trust: int = Field(ge=0, le=100)
    level: int
    xp: int = Field(description="Progress toward the next level")
    xp_to_next: int | None = Field(description="XP the next level needs; null at the top")
    stage: str = Field(examples=["newborn"])
    stage_label: str = Field(examples=["Newborn"])
    created_at: datetime


class FeedRequest(BaseModel):
    food: str = Field(examples=["fish"])


class CareResult(BaseModel):
    message: str = Field(examples=["Ember gobbles the fish and hums happily."])
    dragon: PlayerDragon
