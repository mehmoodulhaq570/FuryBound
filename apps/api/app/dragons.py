"""The player's dragon: adoption and the dragon card (Plan.md §9.5)."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import PlayerDragonRow, SpeciesRow
from app.engines.adoption import Adoption, clean_name, roll_dragon
from app.engines.game_data import TRAITS, GameData
from app.quiz import AttemptConflict, own_attempt
from app.schemas.dragons import DragonAdopt, Labelled, PlayerDragon, Quirk

NEEDS = ("hunger", "energy", "happiness")


class NoDragon(LookupError):
    pass


async def _mine(session: AsyncSession, user_id: UUID) -> PlayerDragonRow | None:
    query = select(PlayerDragonRow).where(PlayerDragonRow.user_id == user_id)
    return (await session.execute(query)).scalar_one_or_none()


async def present(
    session: AsyncSession, data: GameData, adoption: Adoption, row: PlayerDragonRow
) -> PlayerDragon:
    name = await session.scalar(select(SpeciesRow.name).where(SpeciesRow.id == row.species_id))
    trait_labels = {t.id: t.label for t in data.traits.traits}
    quirk_labels = {q.id: q.label for q in adoption.quirks}
    profile = next(s for s in data.species if s.id == row.species_id)
    return PlayerDragon(
        id=row.id,
        name=row.name,
        species_id=row.species_id,
        species_name=name or row.species_id.replace("_", " ").title(),
        rarity=profile.rarity,
        compatibility=row.compatibility,
        color_variant=row.color_variant,
        personality=[
            Labelled(id=t, label=trait_labels[t], value=row.personality[t]) for t in TRAITS
        ],
        stats=[Labelled(id=s, label=s.title(), value=v) for s, v in row.stats.items()],
        needs=[Labelled(id=n, label=n.title(), value=row.needs[n]) for n in NEEDS],
        quirks=[Quirk(id=q, label=quirk_labels.get(q, q)) for q in row.quirks],
        likes=row.likes,
        dislikes=row.dislikes,
        trust=row.trust,
        level=row.level,
        stage=row.stage,
        created_at=row.created_at,
    )


async def adopt(
    session: AsyncSession, data: GameData, adoption: Adoption, user_id: UUID, body: DragonAdopt
) -> PlayerDragon:
    """Adopt the top match of a finished attempt.

    Raises InvalidName, AttemptNotFound, or AttemptConflict (encounter not done, or the
    player already has a dragon).
    """
    name = clean_name(adoption, body.name)
    attempt = await own_attempt(session, user_id, body.attempt_id)
    if not attempt.ranking:
        raise AttemptConflict("Finish the encounter first: no dragon has chosen you yet")
    if await _mine(session, user_id) is not None:
        raise AttemptConflict("You already have a dragon")

    top = attempt.ranking[0]
    species = next(s for s in data.species if s.id == top["species_id"])
    rolled = roll_dragon(adoption, species, seed=str(attempt.id))
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
        trust=rolled.trust,
        compatibility=top["compatibility"],
        rules_version=adoption.version,
    )
    session.add(row)
    try:
        await session.commit()
    except IntegrityError as exc:  # adopted at the same moment in another tab
        await session.rollback()
        raise AttemptConflict("You already have a dragon") from exc
    await session.refresh(row)
    return await present(session, data, adoption, row)


async def get_mine(
    session: AsyncSession, data: GameData, adoption: Adoption, user_id: UUID
) -> PlayerDragon:
    row = await _mine(session, user_id)
    if row is None:
        raise NoDragon("You haven't adopted a dragon yet")
    return await present(session, data, adoption, row)
