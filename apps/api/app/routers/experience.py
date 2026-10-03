"""Habitat achievements, cosmetics, journal and the Misty Cove mission."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app import experience
from app.auth import AUTH_RESPONSES, AuthenticatedUser
from app.db.session import DbSession
from app.dragons import NoDragon, Rulebook, get_rulebook
from app.engines.training import Refused
from app.schemas.experience import (
    AdventureChoice,
    AdventureState,
    DecorationChoice,
    Experience,
)

router = APIRouter(tags=["experience"], responses=AUTH_RESPONSES)
Rules = Annotated[Rulebook, Depends(get_rulebook)]


@router.get("/dragons/{dragon_id}/experience")
async def dragon_experience(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession, rules: Rules
) -> Experience:
    try:
        return await experience.overview(session, rules, user.id, dragon_id)
    except NoDragon as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@router.post("/dragons/{dragon_id}/decoration")
async def decorate_habitat(
    dragon_id: UUID,
    body: DecorationChoice,
    user: AuthenticatedUser,
    session: DbSession,
    rules: Rules,
) -> Experience:
    try:
        await experience.decorate(session, user.id, dragon_id, body.decoration)
        return await experience.overview(session, rules, user.id, dragon_id)
    except NoDragon as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except experience.ExperienceConflict as exc:
        raise HTTPException(409, detail=str(exc)) from exc


@router.post("/dragons/{dragon_id}/adventure")
async def start_rescue(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession
) -> AdventureState:
    try:
        return await experience.start(session, user.id, dragon_id)
    except NoDragon as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@router.post("/dragons/{dragon_id}/adventure/{run_id}/choice")
async def rescue_choice(
    dragon_id: UUID,
    run_id: UUID,
    body: AdventureChoice,
    user: AuthenticatedUser,
    session: DbSession,
    rules: Rules,
) -> AdventureState:
    try:
        return await experience.choose(session, rules, user.id, dragon_id, run_id, body.choice)
    except NoDragon as exc:
        raise HTTPException(404, detail=str(exc)) from exc
    except (experience.ExperienceConflict, Refused) as exc:
        raise HTTPException(409, detail=str(exc)) from exc
