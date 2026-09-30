"""Read-only canon service: films, species and named dragons from the catalog tables.

The dataset is small (tens of species), so lists load each table once and join in Python
rather than building one large query per endpoint.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import (
    AppearanceRow,
    CharacterRow,
    IndividualRow,
    MovieRow,
    RiderLinkRow,
    SourceRow,
    SpeciesRow,
)
from app.schemas.canon import (
    Appearance,
    CharacterRef,
    DragonClass,
    IndividualDetail,
    IndividualRef,
    IndividualSummary,
    Movie,
    Rider,
    SearchResult,
    Source,
    SpeciesDetail,
    SpeciesRef,
    SpeciesSummary,
)


async def list_movies(session: AsyncSession) -> list[Movie]:
    rows = await session.scalars(select(MovieRow).order_by(MovieRow.ordinal))
    return [Movie.model_validate(r, from_attributes=True) for r in rows]


async def _appearances(
    session: AsyncSession, kind: str, entity_ids: Iterable[str] | None = None
) -> dict[str, list[AppearanceRow]]:
    """Appearances per entity id, in film order."""
    query = (
        select(AppearanceRow)
        .join(MovieRow, MovieRow.id == AppearanceRow.movie_id)
        .where(AppearanceRow.entity_kind == kind)
        .order_by(MovieRow.ordinal)
    )
    if entity_ids is not None:
        query = query.where(AppearanceRow.entity_id.in_(list(entity_ids)))
    by_entity: dict[str, list[AppearanceRow]] = defaultdict(list)
    for row in await session.scalars(query):
        by_entity[row.entity_id].append(row)
    return by_entity


async def _sources(session: AsyncSession, source_ids: Sequence[str]) -> list[Source]:
    """Sources in the order the row cites them."""
    rows = {
        r.id: r
        for r in await session.scalars(select(SourceRow).where(SourceRow.id.in_(source_ids)))
    }
    return [Source.model_validate(rows[i], from_attributes=True) for i in source_ids if i in rows]


def _appearance(row: AppearanceRow) -> Appearance:
    return Appearance(
        movie_id=row.movie_id,
        appearance_type=row.appearance_type,
        confidence=row.confidence,
        evidence=row.evidence or None,
    )


def _dragon_class(row: SpeciesRow) -> DragonClass | None:
    if row.class_ and row.class_scope:
        return DragonClass(value=row.class_, scope=row.class_scope)
    return None


def _species_summary(row: SpeciesRow, appearances: list[AppearanceRow]) -> SpeciesSummary:
    return SpeciesSummary(
        id=row.id,
        name=row.name,
        class_=_dragon_class(row),
        size=row.size,
        confidence=row.confidence,
        movies=[a.movie_id for a in appearances],
    )


async def list_species(session: AsyncSession, movie: str | None = None) -> list[SpeciesSummary]:
    appearances = await _appearances(session, "species")
    rows = await session.scalars(select(SpeciesRow).order_by(SpeciesRow.name))
    return [
        _species_summary(r, appearances[r.id])
        for r in rows
        if movie is None or movie in {a.movie_id for a in appearances[r.id]}
    ]


async def get_species(session: AsyncSession, species_id: str) -> SpeciesDetail | None:
    row = await session.get(SpeciesRow, species_id)
    if row is None:
        return None
    appearances = (await _appearances(session, "species", [species_id]))[species_id]
    individuals = await session.scalars(
        select(IndividualRow)
        .where(IndividualRow.species_id == species_id)
        .order_by(IndividualRow.name)
    )
    return SpeciesDetail(
        **_species_summary(row, appearances).model_dump(),
        diet=row.diet,
        description=row.description or None,
        notes=row.notes or None,
        appearances=[_appearance(a) for a in appearances],
        individuals=[IndividualRef(id=i.id, name=i.name) for i in individuals],
        sources=await _sources(session, row.source_ids),
    )


def _individual_summary(
    row: IndividualRow, species: SpeciesRow, appearances: list[AppearanceRow]
) -> IndividualSummary:
    return IndividualSummary(
        id=row.id,
        name=row.name,
        species=SpeciesRef(id=species.id, name=species.name),
        confidence=row.confidence,
        movies=[a.movie_id for a in appearances],
    )


async def list_individuals(
    session: AsyncSession, movie: str | None = None
) -> list[IndividualSummary]:
    appearances = await _appearances(session, "individual")
    rows = await session.execute(
        select(IndividualRow, SpeciesRow)
        .join(SpeciesRow, SpeciesRow.id == IndividualRow.species_id)
        .order_by(IndividualRow.name)
    )
    return [
        _individual_summary(individual, species, appearances[individual.id])
        for individual, species in rows
        if movie is None or movie in {a.movie_id for a in appearances[individual.id]}
    ]


async def get_individual(session: AsyncSession, individual_id: str) -> IndividualDetail | None:
    result = await session.execute(
        select(IndividualRow, SpeciesRow)
        .join(SpeciesRow, SpeciesRow.id == IndividualRow.species_id)
        .where(IndividualRow.id == individual_id)
    )
    found = result.first()
    if found is None:
        return None
    row, species = found
    appearances = (await _appearances(session, "individual", [individual_id]))[individual_id]
    riders = await session.execute(
        select(RiderLinkRow, CharacterRow)
        .join(CharacterRow, CharacterRow.id == RiderLinkRow.character_id)
        .join(MovieRow, MovieRow.id == RiderLinkRow.movie_id)
        .where(RiderLinkRow.individual_id == individual_id)
        .order_by(MovieRow.ordinal, CharacterRow.name)
    )
    return IndividualDetail(
        **_individual_summary(row, species, appearances).model_dump(),
        description=row.description or None,
        notes=row.notes or None,
        appearances=[_appearance(a) for a in appearances],
        riders=[
            Rider(
                movie_id=link.movie_id,
                character=CharacterRef(id=character.id, name=character.name),
                relation=link.relation,
                confidence=link.confidence,
            )
            for link, character in riders
        ],
        sources=await _sources(session, row.source_ids),
    )


async def search(session: AsyncSession, q: str, limit: int) -> list[SearchResult]:
    """Case-insensitive name search. Names starting with `q` rank before other matches."""
    species = await session.scalars(
        select(SpeciesRow).where(SpeciesRow.name.icontains(q, autoescape=True))
    )
    individuals = await session.execute(
        select(IndividualRow, SpeciesRow)
        .join(SpeciesRow, SpeciesRow.id == IndividualRow.species_id)
        .where(IndividualRow.name.icontains(q, autoescape=True))
    )
    results = [
        SearchResult(kind="species", id=s.id, name=s.name, species=None) for s in species
    ] + [
        SearchResult(
            kind="individual", id=i.id, name=i.name, species=SpeciesRef(id=s.id, name=s.name)
        )
        for i, s in individuals
    ]
    starts = q.casefold()
    results.sort(key=lambda r: (not r.name.casefold().startswith(starts), r.name.casefold()))
    return results[:limit]
