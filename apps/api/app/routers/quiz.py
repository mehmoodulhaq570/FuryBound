"""Personality quiz endpoints (Plan.md §9.2, §10). Signed-in players only."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from app import quiz
from app.auth import AUTH_RESPONSES, AuthenticatedUser, ErrorResponse
from app.db.session import DbSession
from app.engines.game_data import GameData, get_game_data
from app.engines.matching import Calibration, get_calibration
from app.schemas.quiz import (
    Encounter,
    EncounterChoices,
    Quiz,
    QuizAttempt,
    QuizAttemptCreate,
    QuizAttemptDetail,
)

router = APIRouter(tags=["quiz"], responses=AUTH_RESPONSES)

Game = Annotated[GameData, Depends(get_game_data)]
Calibrated = Annotated[Calibration, Depends(get_calibration)]

NOT_FOUND: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "No such attempt for this player",
    },
}

ATTEMPT_ERRORS: dict[int | str, dict[str, Any]] = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "The quiz version is no longer the active one",
    },
    status.HTTP_422_UNPROCESSABLE_CONTENT: {
        "model": ErrorResponse,
        "description": "A question is unanswered, unknown or has an unknown option",
    },
}


@router.get("/quiz")
async def get_quiz(user: AuthenticatedUser, data: Game) -> Quiz:
    """The active quiz: questions and options (no scores), options shuffled for this player."""
    return quiz.player_quiz(data, user.id)


@router.post("/quiz/attempts", status_code=status.HTTP_201_CREATED, responses=ATTEMPT_ERRORS)
async def create_quiz_attempt(
    body: QuizAttemptCreate, user: AuthenticatedUser, session: DbSession, data: Game
) -> QuizAttempt:
    """Score a finished quiz and save it. The encounter (next step) completes the attempt."""
    if body.quiz_version != data.quiz.version:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            detail=f"Quiz {body.quiz_version} is no longer active; reload to get "
            f"{data.quiz.version}",
        )
    try:
        return await quiz.create_attempt(session, data, user.id, body.answers)
    except quiz.InvalidAnswers as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc


@router.get("/quiz/attempts/{attempt_id}", responses=NOT_FOUND)
async def get_quiz_attempt(
    attempt_id: UUID, user: AuthenticatedUser, session: DbSession, data: Game
) -> QuizAttemptDetail:
    """One of the player's attempts: trait scores, and the match once the encounter is done."""
    try:
        return await quiz.get_attempt(session, data, user.id, attempt_id)
    except quiz.AttemptNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/encounter")
async def get_encounter(user: AuthenticatedUser, data: Game) -> Encounter:
    """The three encounter scenes (no hints about what each option means), options shuffled."""
    return quiz.player_encounter(data, user.id)


@router.post(
    "/quiz/attempts/{attempt_id}/encounter",
    responses={
        **NOT_FOUND,
        status.HTTP_409_CONFLICT: {
            "model": ErrorResponse,
            "description": "Already complete, or the quiz or encounter version has changed",
        },
        status.HTTP_422_UNPROCESSABLE_CONTENT: {
            "model": ErrorResponse,
            "description": "An unknown option",
        },
    },
)
async def complete_encounter(
    attempt_id: UUID,
    body: EncounterChoices,
    user: AuthenticatedUser,
    session: DbSession,
    data: Game,
    calibration: Calibrated,
) -> QuizAttemptDetail:
    """Submit the encounter choices: the dragons are ranked and the attempt is finished, once."""
    try:
        return await quiz.complete_encounter(session, data, calibration, user.id, attempt_id, body)
    except quiz.AttemptNotFound as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except quiz.AttemptConflict as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except quiz.InvalidAnswers as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
