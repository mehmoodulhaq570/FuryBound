"""The player's dragon (Plan.md §9.5, §10). Signed-in players only."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app import dragons, quiz
from app.auth import AUTH_RESPONSES, AuthenticatedUser, ErrorResponse
from app.db.session import DbSession
from app.engines.adoption import Adoption, InvalidName, get_adoption
from app.engines.game_data import GameData, get_game_data
from app.schemas.dragons import DragonAdopt, PlayerDragon

router = APIRouter(tags=["dragons"], responses=AUTH_RESPONSES)

Game = Annotated[GameData, Depends(get_game_data)]
Rules = Annotated[Adoption, Depends(get_adoption)]


def _error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


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
    body: DragonAdopt, user: AuthenticatedUser, session: DbSession, data: Game, rules: Rules
) -> PlayerDragon:
    """Adopt the dragon that chose you (the attempt's top match) and give it a name."""
    try:
        return await dragons.adopt(session, data, rules, user.id, body)
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
async def my_dragon(
    user: AuthenticatedUser, session: DbSession, data: Game, rules: Rules
) -> PlayerDragon:
    """The signed-in player's dragon card."""
    try:
        return await dragons.get_mine(session, data, rules, user.id)
    except dragons.NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
