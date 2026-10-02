"""The player's dragon (Plan.md §9.5-9.7, §10). Signed-in players only."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app import dragons, quiz
from app.auth import AUTH_RESPONSES, AuthenticatedUser, ErrorResponse
from app.db.session import DbSession
from app.dragons import Rulebook, get_rulebook
from app.engines.adoption import InvalidName
from app.engines.care import Action, Refused
from app.schemas.dragons import CareResult, DragonAdopt, FeedRequest, PlayerDragon

router = APIRouter(tags=["dragons"], responses=AUTH_RESPONSES)

Rules = Annotated[Rulebook, Depends(get_rulebook)]


def _error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


CARE_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: _error("Not this player's dragon"),
    status.HTTP_409_CONFLICT: _error("The dragon won't right now (the detail says why)"),
}


@router.post(
    "/dragons",
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_404_NOT_FOUND: _error("No such attempt for this player"),
        status.HTTP_409_CONFLICT: _error("Encounter not finished, or already has a dragon"),
        status.HTTP_422_UNPROCESSABLE_CONTENT: _error("The name isn't allowed"),
    },
)
async def adopt_dragon(
    body: DragonAdopt, user: AuthenticatedUser, session: DbSession, rules: Rules
) -> PlayerDragon:
    """Adopt the dragon that chose you (the attempt's top match) and give it a name."""
    try:
        return await dragons.adopt(session, rules, user.id, body)
    except InvalidName as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except quiz.AttemptNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except quiz.AttemptConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get(
    "/dragons/me",
    responses={status.HTTP_404_NOT_FOUND: _error("No dragon adopted yet")},
)
async def my_dragon(user: AuthenticatedUser, session: DbSession, rules: Rules) -> PlayerDragon:
    """The signed-in player's dragon card, with needs as of now, mood and an idle thought."""
    try:
        return await dragons.get_mine(session, rules, user.id)
    except dragons.NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


async def _care(
    session: DbSession,
    rules: Rulebook,
    user: AuthenticatedUser,
    dragon_id: UUID,
    action: Action,
    food: str | None = None,
) -> CareResult:
    try:
        return await dragons.look_after(session, rules, user.id, dragon_id, action, food)
    except dragons.NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except dragons.InvalidFood as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except Refused as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.post(
    "/dragons/{dragon_id}/feed",
    responses={**CARE_ERRORS, status.HTTP_422_UNPROCESSABLE_CONTENT: _error("Unknown food")},
)
async def feed_dragon(
    dragon_id: UUID, body: FeedRequest, user: AuthenticatedUser, session: DbSession, rules: Rules
) -> CareResult:
    """Offer a food. Liked foods please it more; disliked ones cost happiness and trust."""
    return await _care(session, rules, user, dragon_id, "feed", body.food)


@router.post("/dragons/{dragon_id}/rest", responses=CARE_ERRORS)
async def rest_dragon(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession, rules: Rules
) -> CareResult:
    """Let it sleep: energy recovers."""
    return await _care(session, rules, user, dragon_id, "rest")


@router.post("/dragons/{dragon_id}/play", responses=CARE_ERRORS)
async def play_with_dragon(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession, rules: Rules
) -> CareResult:
    """Play together: happier and a little more trusting, but it costs energy."""
    return await _care(session, rules, user, dragon_id, "play")
