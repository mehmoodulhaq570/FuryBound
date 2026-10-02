"""Training (Plan.md §9.6, §10). Signed-in players only."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app import training
from app.auth import AUTH_RESPONSES, AuthenticatedUser, ErrorResponse
from app.db.session import DbSession
from app.dragons import NoDragon, Rulebook, get_rulebook
from app.engines.training import Implausible, Locked, Refused
from app.schemas.training import (
    ActivityResult,
    HistoryEntry,
    SessionStart,
    TrainingOverview,
    TrainingResult,
    TrainingSession,
)

router = APIRouter(tags=["training"], responses=AUTH_RESPONSES)

Rules = Annotated[Rulebook, Depends(get_rulebook)]


def _error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


NOT_YOURS: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: _error("Not this player's dragon")
}


@router.get("/dragons/{dragon_id}/training", responses=NOT_YOURS)
async def training_overview(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession, rules: Rules
) -> TrainingOverview:
    """Level, XP and every activity, with whether it's unlocked yet."""
    try:
        return await training.overview(session, rules, user.id, dragon_id)
    except NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/dragons/{dragon_id}/training-sessions",
    status_code=status.HTTP_201_CREATED,
    responses={
        **NOT_YOURS,
        status.HTTP_403_FORBIDDEN: _error("The activity unlocks at a later stage"),
        status.HTTP_409_CONFLICT: _error("The dragon refuses (exhausted or too hungry)"),
        status.HTTP_422_UNPROCESSABLE_CONTENT: _error("Unknown activity"),
    },
)
async def start_training(
    dragon_id: UUID, body: SessionStart, user: AuthenticatedUser, session: DbSession, rules: Rules
) -> TrainingSession:
    """Start a session; the activity then reports its result to `/complete`."""
    try:
        return await training.start(session, rules, user.id, dragon_id, body.activity)
    except NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except training.UnknownActivity as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except Locked as exc:
        raise HTTPException(status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except Refused as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/training-sessions/{session_id}/complete",
    responses={
        status.HTTP_404_NOT_FOUND: _error("No such session for this player"),
        status.HTTP_409_CONFLICT: _error("Already finished, or expired"),
        status.HTTP_422_UNPROCESSABLE_CONTENT: _error("The duration isn't plausible"),
    },
)
async def complete_training(
    session_id: UUID,
    body: ActivityResult,
    user: AuthenticatedUser,
    session: DbSession,
    rules: Rules,
) -> TrainingResult:
    """Report the activity's result (once): XP, stat gains, level-ups and unlocks."""
    try:
        return await training.finish(session, rules, user.id, session_id, body)
    except training.SessionNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except training.SessionClosed as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except Implausible as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.get("/dragons/{dragon_id}/history", responses=NOT_YOURS)
async def training_history(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession
) -> list[HistoryEntry]:
    """Finished training sessions, oldest first, with the stats after each."""
    try:
        return await training.history(session, user.id, dragon_id)
    except NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
