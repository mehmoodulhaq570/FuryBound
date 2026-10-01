"""Request and response models for the personality quiz (Plan.md §9.2, §10)."""

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
