"""Request and response models for chatting with your dragon (Plan.md §9.8, §10)."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(examples=["Did you like the fish?"], description="Up to 500 characters")
    mode: Literal["narrated", "talking"] = Field(
        default="narrated",
        description="narrated: body language and a thought (canon-friendly); talking: speaks",
    )


class ChatMessage(BaseModel):
    id: int
    role: Literal["user", "dragon"]
    content: str
    mode: Literal["narrated", "talking"]
    created_at: datetime


class StreamDelta(BaseModel):
    """A piece of the reply as it's generated (one server-sent event)."""

    type: Literal["delta"] = "delta"
    text: str


class StreamDone(BaseModel):
    """The final, checked reply; it replaces whatever was streamed (last server-sent event)."""

    type: Literal["done"] = "done"
    message: ChatMessage
    fallback: bool = Field(description="True if the AI failed and a stock reply was used")


class DragonMemory(BaseModel):
    """What the dragon knows from its diary (structured memory, Plan §9.9 tier 1)."""

    favourite_food: str | None
    favourite_activity: str | None
    disliked_foods: list[str]
    refused_activities: list[str]
    times_fed: int
    times_played: int
    sessions_trained: int
    days_together: int
    streak_days: int
    lines: list[str] = Field(description="The same, as sentences")
