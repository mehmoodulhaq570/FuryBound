"""The player's dragon: adoption, the dragon card and care (Plan.md §9.5-9.7)."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DragonEventRow, PlayerDragonRow, SpeciesRow
from app.engines import care, training
from app.engines.adoption import Adoption, clean_name, get_adoption, roll_dragon
from app.engines.game_data import TRAITS, GameData, get_game_data
from app.quiz import AttemptConflict, own_attempt
from app.schemas.dragons import (
    CareResult,
    DragonAdopt,
    Labelled,
    MoodState,
    PlayerDragon,
    Quirk,
)


@dataclass(frozen=True)
class Rulebook:
    """All the game data a dragon needs: matching profiles, adoption and care rules."""

    game: GameData
    adoption: Adoption
    care: care.CareRules
    progression: training.Progression


@lru_cache
def get_rulebook() -> Rulebook:
    return Rulebook(get_game_data(), get_adoption(), care.get_care(), training.get_progression())


class NoDragon(LookupError):
    pass


class InvalidFood(ValueError):
    pass


def now() -> datetime:
    return datetime.now(UTC)


async def mine(
    session: AsyncSession, user_id: UUID, dragon_id: UUID | None = None, *, lock: bool = False
) -> PlayerDragonRow | None:
    query = select(PlayerDragonRow).where(PlayerDragonRow.user_id == user_id)
    if dragon_id is not None:
        query = query.where(PlayerDragonRow.id == dragon_id)
    if lock:
        query = query.with_for_update()
    return (await session.execute(query)).scalar_one_or_none()


def _current_needs(book: Rulebook, row: PlayerDragonRow, now: datetime) -> dict[care.Need, int]:
    hours = (now - row.needs_updated_at).total_seconds() / 3600
    return care.decay(book.care, row.needs, hours)


async def state(
    session: AsyncSession, book: Rulebook, row: PlayerDragonRow, at: datetime
) -> tuple[dict[care.Need, int], care.Mood]:
    """The dragon's needs and mood as of `at` (moods read the last hour's events)."""
    recent = await session.scalars(
        select(DragonEventRow.kind).where(
            DragonEventRow.dragon_id == row.id,
            DragonEventRow.created_at > at - timedelta(hours=1),
        )
    )
    needs = _current_needs(book, row, at)
    return needs, care.mood(needs, row.trust, row.personality["curiosity"], set(recent))


async def present(
    session: AsyncSession, book: Rulebook, row: PlayerDragonRow, at: datetime | None = None
) -> PlayerDragon:
    at = at or now()
    name = await session.scalar(select(SpeciesRow.name).where(SpeciesRow.id == row.species_id))
    needs, current = await state(session, book, row, at)
    trait_labels = {t.id: t.label for t in book.game.traits.traits}
    quirk_labels = {q.id: q.label for q in book.adoption.quirks}
    profile = next(s for s in book.game.species if s.id == row.species_id)
    return PlayerDragon(
        id=row.id,
        name=row.name,
        species_id=row.species_id,
        species_name=name or row.species_id.replace("_", " ").title(),
        rarity=profile.rarity,
        compatibility=row.compatibility,
        color_variant=row.color_variant,
        color_hex=book.adoption.color_hex(row.species_id, row.color_variant),
        personality=[
            Labelled(id=t, label=trait_labels[t], value=row.personality[t]) for t in TRAITS
        ],
        stats=[Labelled(id=s, label=s.title(), value=v) for s, v in row.stats.items()],
        needs=[Labelled(id=n, label=n.title(), value=needs[n]) for n in care.NEEDS],
        mood=MoodState(id=current, label=current.title()),
        # A new line each hour, steady across reloads within it.
        thought=care.thought(book.care, current, row.name, f"{row.id}:{at:%Y-%m-%dT%H}"),
        foods=list(book.game.profiles.foods),
        quirks=[Quirk(id=q, label=quirk_labels.get(q, q)) for q in row.quirks],
        likes=row.likes,
        dislikes=row.dislikes,
        trust=row.trust,
        level=row.level,
        xp=row.xp,
        xp_to_next=training.xp_to_next(book.progression, row.level),
        stage=row.stage,
        stage_label=book.progression.stage(row.stage).label,
        created_at=row.created_at,
    )


async def adopt(
    session: AsyncSession, book: Rulebook, user_id: UUID, body: DragonAdopt
) -> PlayerDragon:
    """Adopt the top match of a finished attempt.

    Raises InvalidName, AttemptNotFound, or AttemptConflict (encounter not done, or the
    player already has a dragon).
    """
    name = clean_name(book.adoption, body.name)
    attempt = await own_attempt(session, user_id, body.attempt_id)
    if not attempt.ranking:
        raise AttemptConflict("Finish the encounter first: no dragon has chosen you yet")
    if await mine(session, user_id) is not None:
        raise AttemptConflict("You already have a dragon")

    top = attempt.ranking[0]
    species = next(s for s in book.game.species if s.id == top["species_id"])
    rolled = roll_dragon(book.adoption, species, seed=str(attempt.id))
    row = PlayerDragonRow(
        user_id=user_id,
        species_id=rolled.species_id,
        quiz_attempt_id=attempt.id,
        name=name,
        color_variant=rolled.color_variant,
        personality=rolled.personality,
        quirks=list(rolled.quirks),
        likes=list(rolled.likes),
        dislikes=list(rolled.dislikes),
        stats=rolled.stats,
        needs=rolled.needs,
        needs_updated_at=now(),
        trust=rolled.trust,
        compatibility=top["compatibility"],
        rules_version=book.adoption.version,
    )
    session.add(row)
    try:
        await session.flush()
    except IntegrityError as exc:  # adopted at the same moment in another tab
        await session.rollback()
        raise AttemptConflict("You already have a dragon") from exc
    session.add(DragonEventRow(dragon_id=row.id, kind="adopted", payload={"name": name}))
    await session.commit()
    await session.refresh(row)
    return await present(session, book, row)


async def get_mine(session: AsyncSession, book: Rulebook, user_id: UUID) -> PlayerDragon:
    row = await mine(session, user_id)
    if row is None:
        raise NoDragon("You haven't adopted a dragon yet")
    return await present(session, book, row)


async def look_after(
    session: AsyncSession,
    book: Rulebook,
    user_id: UUID,
    dragon_id: UUID,
    action: care.Action,
    food: str | None = None,
) -> CareResult:
    """Feed, rest or play with the player's dragon.

    Raises NoDragon, InvalidFood, or care.Refused (with the dragon's reason).
    """
    if action == "feed" and food not in book.game.profiles.foods:
        raise InvalidFood(f"Unknown food {food!r}; try one of {list(book.game.profiles.foods)}")
    row = await mine(session, user_id, dragon_id, lock=True)
    if row is None:
        raise NoDragon(f"No dragon {dragon_id}")

    at = now()
    outcome = care.care(
        book.care,
        action,
        name=row.name,
        needs=_current_needs(book, row, at),
        trust=row.trust,
        likes=row.likes,
        dislikes=row.dislikes,
        food=food,
    )
    row.needs = {str(n): v for n, v in outcome.needs.items()}
    row.needs_updated_at = at
    row.trust = outcome.trust
    session.add(DragonEventRow(dragon_id=row.id, kind=outcome.event, payload=outcome.detail))
    await session.commit()
    await session.refresh(row)
    return CareResult(message=outcome.message, dragon=await present(session, book, row, at))
