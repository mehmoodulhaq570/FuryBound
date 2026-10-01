"""Personality quiz endpoints (Plan.md §9.2, §10). Signed-in players only."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status

from app import quiz
from app.auth import AUTH_RESPONSES, AuthenticatedUser, ErrorResponse
from app.db.session import DbSession
from app.engines.game_data import GameData, get_game_data
from app.schemas.quiz import Quiz, QuizAttempt, QuizAttemptCreate

router = APIRouter(tags=["quiz"], responses=AUTH_RESPONSES)

Game = Annotated[GameData, Depends(get_game_data)]

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
