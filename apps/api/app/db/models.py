"""SQLAlchemy mappings for the canon tables.

The schema itself lives in supabase/migrations/; these classes only describe it for queries.
"""

from datetime import date
from enum import StrEnum

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.schemas.canon import AppearanceType, Confidence, Relation, Scope, Size, SourceType


def _pg_enum[E: StrEnum](enum: type[E], name: str) -> Enum:
    # Existing Postgres enum types, matched by value ("on_screen"), not by member name.
    return Enum(enum, name=name, create_type=False, values_callable=lambda e: [m.value for m in e])


class Base(DeclarativeBase):
    pass


class MovieRow(Base):
    __tablename__ = "movies"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str]
    year: Mapped[int]
    ordinal: Mapped[int]


class SourceRow(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    title: Mapped[str]
    type: Mapped[SourceType] = mapped_column(Text)  # values checked by the table's constraint
    url: Mapped[str | None]
    accessed_on: Mapped[date | None]


class SpeciesRow(Base):
    __tablename__ = "species"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str]
    class_: Mapped[str | None] = mapped_column("class")
    class_scope: Mapped[Scope | None] = mapped_column(_pg_enum(Scope, "source_scope"))
    size: Mapped[Size | None] = mapped_column(Text)  # values checked by the table's constraint
    diet: Mapped[str | None]
    description: Mapped[str | None]
    notes: Mapped[str | None]
    source_ids: Mapped[list[str]] = mapped_column(ARRAY(Text))
    confidence: Mapped[Confidence] = mapped_column(_pg_enum(Confidence, "confidence"))


class IndividualRow(Base):
    __tablename__ = "individuals"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str]
    species_id: Mapped[str] = mapped_column(ForeignKey("species.id"))
    description: Mapped[str | None]
    notes: Mapped[str | None]
    source_ids: Mapped[list[str]] = mapped_column(ARRAY(Text))
    confidence: Mapped[Confidence] = mapped_column(_pg_enum(Confidence, "confidence"))


class CharacterRow(Base):
    __tablename__ = "characters"

    id: Mapped[str] = mapped_column(Text, primary_key=True)
    name: Mapped[str]


class AppearanceRow(Base):
    __tablename__ = "appearances"

    id: Mapped[int] = mapped_column(primary_key=True)
    entity_kind: Mapped[str]
    entity_id: Mapped[str]
    movie_id: Mapped[str] = mapped_column(ForeignKey("movies.id"))
    appearance_type: Mapped[AppearanceType] = mapped_column(
        _pg_enum(AppearanceType, "appearance_type")
    )
    scope: Mapped[Scope] = mapped_column(_pg_enum(Scope, "source_scope"))
    evidence: Mapped[str | None]
    source_ids: Mapped[list[str]] = mapped_column(ARRAY(Text))
    confidence: Mapped[Confidence] = mapped_column(_pg_enum(Confidence, "confidence"))


class RiderLinkRow(Base):
    __tablename__ = "rider_links"

    individual_id: Mapped[str] = mapped_column(ForeignKey("individuals.id"), primary_key=True)
    character_id: Mapped[str] = mapped_column(ForeignKey("characters.id"), primary_key=True)
    movie_id: Mapped[str] = mapped_column(ForeignKey("movies.id"), primary_key=True)
    relation: Mapped[Relation] = mapped_column(Text)  # values checked by the table's constraint
    source_ids: Mapped[list[str]] = mapped_column(ARRAY(Text))
    confidence: Mapped[Confidence] = mapped_column(_pg_enum(Confidence, "confidence"))
