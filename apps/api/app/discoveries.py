"""Which dragons a player has met, for the Dragon Book's Academy mode (Plan.md §9.1)."""

from collections.abc import Iterable
from typing import Literal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import DiscoveryRow
from app.schemas.discoveries import Discovery

Via = Literal["quiz", "arena", "story", "training", "starter"]


async def discover(
    session: AsyncSession, user_id: UUID, species_ids: Iterable[str], via: Via
) -> None:
    """Record species as met. Meeting one again keeps the first date. Doesn't commit."""
    rows = [
        {"user_id": user_id, "entity_kind": "species", "entity_id": s, "via": via}
        for s in dict.fromkeys(species_ids)
    ]
    if rows:
        await session.execute(insert(DiscoveryRow).values(rows).on_conflict_do_nothing())


async def list_for(session: AsyncSession, user_id: UUID) -> list[Discovery]:
    rows = await session.scalars(
        select(DiscoveryRow)
        .where(DiscoveryRow.user_id == user_id)
        .order_by(DiscoveryRow.discovered_at, DiscoveryRow.entity_id)
    )
    return [
        Discovery(
            entity_kind=r.entity_kind,
            entity_id=r.entity_id,
            via=r.via,
            discovered_at=r.discovered_at,
        )
        for r in rows
    ]
