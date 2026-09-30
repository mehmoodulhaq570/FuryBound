"""Public, read-only canon endpoints: films, species, named dragons and search."""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Query, status

from app import canon
from app.auth import ErrorResponse
from app.db.session import DbSession
from app.schemas.canon import (
    IndividualDetail,
    IndividualSummary,
    Movie,
    SearchResult,
    SpeciesDetail,
    SpeciesSummary,
)

router = APIRouter(tags=["canon"])

NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "No entry with this id"}
}

MovieFilter = Annotated[
    str | None, Query(description="Only entries that appear in this film, e.g. `httyd2`")
]
EntryId = Annotated[str, Path(pattern=r"^[a-z0-9_]+$", examples=["night_fury"])]


@router.get("/movies")
async def list_movies(session: DbSession) -> list[Movie]:
    """The three films, in release order."""
    return await canon.list_movies(session)


@router.get("/species")
async def list_species(session: DbSession, movie: MovieFilter = None) -> list[SpeciesSummary]:
    """Every dragon species in the catalog, by name."""
    return await canon.list_species(session, movie)


@router.get("/species/{species_id}", responses=NOT_FOUND)
async def get_species(session: DbSession, species_id: EntryId) -> SpeciesDetail:
    """One species with its film appearances, named dragons and sources."""
    species = await canon.get_species(session, species_id)
    if species is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Species not found")
    return species


@router.get("/individuals")
async def list_individuals(
    session: DbSession, movie: MovieFilter = None
) -> list[IndividualSummary]:
    """Every named dragon in the catalog, by name."""
    return await canon.list_individuals(session, movie)


@router.get("/individuals/{individual_id}", responses=NOT_FOUND)
async def get_individual(session: DbSession, individual_id: EntryId) -> IndividualDetail:
    """One named dragon with its species, film appearances, riders per film and sources."""
    individual = await canon.get_individual(session, individual_id)
    if individual is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Dragon not found")
    return individual


@router.get("/search")
async def search(
    session: DbSession,
    q: Annotated[str, Query(min_length=1, max_length=100, description="Part of a name")],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
) -> list[SearchResult]:
    """Species and named dragons whose name contains `q`, prefix matches first."""
    return await canon.search(session, q.strip(), limit)
