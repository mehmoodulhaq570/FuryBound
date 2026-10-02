"""SQLAlchemy mappings for the canon tables and player data.

The schema itself lives in supabase/migrations/; these classes only describe it for queries.
"""

from datetime import date, datetime
from enum import StrEnum
from typing import Any, ClassVar
from uuid import UUID

from sqlalchemy import DateTime, Enum, ForeignKey, Text, text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.schemas.canon import AppearanceType, Confidence, Relation, Scope, Size, SourceType


def _pg_enum[E: StrEnum](enum: type[E], name: str) -> Enum:
    # Existing Postgres enum types, matched by value ("on_screen"), not by member name.
    return Enum(enum, name=name, create_type=False, values_callable=lambda e: [m.value for m in e])


class Base(DeclarativeBase):
    # Every timestamp column is timestamptz, so datetimes carry their time zone.
    type_annotation_map: ClassVar[dict[Any, Any]] = {datetime: DateTime(timezone=True)}


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


# ── player data (layer 4) ────────────────────────────────────────────────────


class QuizAttemptRow(Base):
    __tablename__ = "quiz_attempts"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID]
    quiz_id: Mapped[str]
    answers: Mapped[dict[str, str]] = mapped_column(JSONB)
    trait_scores: Mapped[dict[str, float] | None] = mapped_column(JSONB)
    encounter_signals: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    ranking: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    algorithm_version: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    completed_at: Mapped[datetime | None]


class PlayerDragonRow(Base):
    __tablename__ = "player_dragons"

    id: Mapped[UUID] = mapped_column(primary_key=True, server_default=text("gen_random_uuid()"))
    user_id: Mapped[UUID]
    species_id: Mapped[str]
    quiz_attempt_id: Mapped[UUID | None]
    name: Mapped[str]
    color_variant: Mapped[str | None]
    personality: Mapped[dict[str, int]] = mapped_column(JSONB)
    quirks: Mapped[list[str]] = mapped_column(ARRAY(Text))
    likes: Mapped[list[str]] = mapped_column(ARRAY(Text))
    dislikes: Mapped[list[str]] = mapped_column(ARRAY(Text))
    level: Mapped[int] = mapped_column(server_default=text("1"))
    xp: Mapped[int] = mapped_column(server_default=text("0"))
    stage: Mapped[str] = mapped_column(server_default=text("'newborn'"))
    stats: Mapped[dict[str, int]] = mapped_column(JSONB)
    needs: Mapped[dict[str, int]] = mapped_column(JSONB)
    needs_updated_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
    trust: Mapped[int]
    compatibility: Mapped[int | None]
    rules_version: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))


class DragonEventRow(Base):
    __tablename__ = "dragon_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    dragon_id: Mapped[UUID]
    kind: Mapped[str]
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(server_default=text("now()"))
