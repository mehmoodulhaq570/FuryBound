"""Shared catalog definitions: row schemas, file locations and CSV loading (Plan.md §8.1).

Used by import_scene_logs.py, validate_catalog.py and build_catalog.py.
"""

import csv
from datetime import date
from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, BeforeValidator, ConfigDict, StringConstraints

ROOT = Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data" / "catalog"
RESEARCH = ROOT / "data" / "research"
BUILD = ROOT / "data" / "build"

MOVIE_IDS = ("httyd1", "httyd2", "httyd3")


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


def _split_ids(value: object) -> object:
    if isinstance(value, str):
        return [v for v in value.split("|") if v]
    return value


def _blank_to_none(value: object) -> object:
    return None if value == "" else value


Slug = Annotated[str, StringConstraints(pattern=r"^[a-z0-9]+(_[a-z0-9]+)*$")]
Ids = Annotated[list[Slug], BeforeValidator(_split_ids)]
Text = Annotated[str, StringConstraints(strip_whitespace=True)]
Size = Literal["tiny", "small", "medium", "large", "titan"]

# Empty CSV cells become None.
OptStr = Annotated[str | None, BeforeValidator(_blank_to_none)]
OptDate = Annotated[date | None, BeforeValidator(_blank_to_none)]
OptScope = Annotated[Scope | None, BeforeValidator(_blank_to_none)]
OptSize = Annotated[Size | None, BeforeValidator(_blank_to_none)]


class Row(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Movie(Row):
    movie_id: Slug
    title: Text
    year: int
    ordinal: int


class Source(Row):
    source_id: Slug
    title: Text
    type: Literal["film", "official", "book", "wiki", "other"]
    url: OptStr
    accessed_on: OptDate


class Species(Row):
    species_id: Slug
    name: Text
    class_: OptStr
    class_scope: OptScope
    size: OptSize
    diet: OptStr
    description: Text
    notes: Text
    source_ids: Ids
    confidence: Confidence


class Individual(Row):
    individual_id: Slug
    name: Text
    species_id: Slug
    description: Text
    notes: Text
    source_ids: Ids
    confidence: Confidence


class Character(Row):
    character_id: Slug
    name: Text


class Ability(Row):
    ability_id: Slug
    name: Text
    category: Literal["fire", "physical", "sensory", "defensive", "utility", "special"]
    description: Text


class SpeciesAbility(Row):
    species_id: Slug
    ability_id: Slug
    scope: Scope


class Appearance(Row):
    entity_kind: Literal["species", "individual"]
    entity_id: Slug
    movie_id: Slug
    appearance_type: AppearanceType
    scope: Scope
    evidence: Text
    source_ids: Ids
    confidence: Confidence


class RiderLink(Row):
    individual_id: Slug
    character_id: Slug
    movie_id: Slug
    relation: Literal["rider", "owner", "controller", "companion"]
    source_ids: Ids
    confidence: Confidence


# File name -> row model. Column order in each CSV follows the model's field order;
# `class_` is written as `class` in the files.
FILES: dict[str, type[Row]] = {
    "movies.csv": Movie,
    "sources.csv": Source,
    "species.csv": Species,
    "individuals.csv": Individual,
    "characters.csv": Character,
    "abilities.csv": Ability,
    "species_abilities.csv": SpeciesAbility,
    "appearances.csv": Appearance,
    "rider_links.csv": RiderLink,
}


def columns(model: type[Row]) -> list[str]:
    return [name.rstrip("_") for name in model.model_fields]


def read_rows(file_name: str) -> list[dict[str, str]]:
    with (CATALOG / file_name).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(file_name: str, rows: list[dict[str, str]]) -> None:
    model = FILES[file_name]
    with (CATALOG / file_name).open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns(model), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def parse(model: type[Row], raw: dict[str, str]) -> Row:
    data = {("class_" if k == "class" else k): v for k, v in raw.items()}
    return model.model_validate(data)
