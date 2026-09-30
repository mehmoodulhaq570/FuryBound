"""Response models for the canon (film and franchise) endpoints (Plan.md §10)."""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class Scope(StrEnum):
    FILM = "film"
    FRANCHISE = "franchise"


class AppearanceType(StrEnum):
    FEATURED = "featured"
    ON_SCREEN = "on_screen"
    BACKGROUND = "background"
    MENTIONED = "mentioned"
    PICTURED = "pictured"


class Confidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


Size = Literal["tiny", "small", "medium", "large", "titan"]
SourceType = Literal["film", "official", "book", "wiki", "other"]
Relation = Literal["rider", "owner", "controller", "companion"]


class Movie(BaseModel):
    id: str
    title: str
    year: int
    ordinal: int


class Source(BaseModel):
    id: str
    title: str
    type: SourceType
    url: str | None
    accessed_on: date | None


class DragonClass(BaseModel):
    value: str
    scope: Scope = Field(description="`franchise` means the class comes from outside the films")


class Appearance(BaseModel):
    movie_id: str
    appearance_type: AppearanceType
    confidence: Confidence
    evidence: str | None


class SpeciesRef(BaseModel):
    id: str
    name: str


class IndividualRef(BaseModel):
    id: str
    name: str


class CharacterRef(BaseModel):
    id: str
    name: str


class Rider(BaseModel):
    movie_id: str
    character: CharacterRef
    relation: Relation
    confidence: Confidence


class SpeciesSummary(BaseModel):
    id: str
    name: str
    class_: DragonClass | None = Field(serialization_alias="class")
    size: Size | None
    confidence: Confidence
    movies: list[str] = Field(description="Films the species appears in, in film order")


class SpeciesDetail(SpeciesSummary):
    diet: str | None
    description: str | None
    notes: str | None
    appearances: list[Appearance]
    individuals: list[IndividualRef] = Field(description="Named dragons of this species")
    sources: list[Source]


class IndividualSummary(BaseModel):
    id: str
    name: str
    species: SpeciesRef
    confidence: Confidence
    movies: list[str] = Field(description="Films the dragon appears in, in film order")


class IndividualDetail(IndividualSummary):
    description: str | None
    notes: str | None
    appearances: list[Appearance]
    riders: list[Rider]
    sources: list[Source]


class SearchResult(BaseModel):
    kind: Literal["species", "individual"]
    id: str
    name: str
    species: SpeciesRef | None = Field(description="For individuals: their species")
