"""Talking to your dragon (Plan.md §9.8-9.9, §10). Signed-in players only."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app import chat
from app.ai.providers import LLMProvider, get_llm
from app.auth import AUTH_RESPONSES, AuthenticatedUser, ErrorResponse
from app.db.session import DbSession
from app.dragons import NoDragon, Rulebook, get_rulebook, mine, now
from app.schemas.chat import ChatMessage, ChatRequest, DragonMemory

router = APIRouter(tags=["chat"], responses=AUTH_RESPONSES)

Rules = Annotated[Rulebook, Depends(get_rulebook)]
LLM = Annotated[LLMProvider, Depends(get_llm)]


def _error(description: str) -> dict[str, Any]:
    return {"model": ErrorResponse, "description": description}


NOT_YOURS: dict[int | str, dict[str, Any]] = {
    status.HTTP_404_NOT_FOUND: _error("Not this player's dragon")
}


@router.post(
    "/dragons/{dragon_id}/chat",
    response_class=StreamingResponse,
    responses={
        200: {
            "content": {"text/event-stream": {}},
            "description": "Server-sent events: `delta` pieces of the reply, then one `done` "
            "with the checked, saved reply (it replaces the pieces).",
        },
        **NOT_YOURS,
        status.HTTP_422_UNPROCESSABLE_CONTENT: _error("Empty or longer than 500 characters"),
        status.HTTP_429_TOO_MANY_REQUESTS: _error("Daily message limit reached"),
    },
)
async def chat_with_dragon(
    dragon_id: UUID,
    body: ChatRequest,
    request: Request,
    user: AuthenticatedUser,
    session: DbSession,
    rules: Rules,
    llm: LLM,
) -> StreamingResponse:
    """Say something to your dragon; its reply streams back as it's written."""
    try:
        messages, name = await chat.prepare(
            session,
            rules,
            user.id,
            dragon_id,
            body.message,
            body.mode,
            request.app.state.settings.chat_daily_limit,
        )
    except NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except chat.InvalidMessage as exc:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from exc
    except chat.RateLimited as exc:
        raise HTTPException(status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    return StreamingResponse(
        chat.stream_reply(
            request.app.state.sessionmaker, llm, dragon_id, name, messages, body.mode
        ),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/dragons/{dragon_id}/messages", responses=NOT_YOURS)
async def chat_history(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession
) -> list[ChatMessage]:
    """The latest 50 messages, oldest first."""
    try:
        return await chat.history(session, user.id, dragon_id)
    except NoDragon as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/dragons/{dragon_id}/memory", responses=NOT_YOURS)
async def dragon_memory(
    dragon_id: UUID, user: AuthenticatedUser, session: DbSession
) -> DragonMemory:
    """What the dragon remembers from your time together (worked out from its diary)."""
    row = await mine(session, user.id, dragon_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"No dragon {dragon_id}")
    memory = await chat.memory_of(session, row, now())
    return DragonMemory(
        favourite_food=memory.favourite_food,
        favourite_activity=memory.favourite_activity,
        disliked_foods=list(memory.disliked_foods),
        refused_activities=list(memory.refused_activities),
        times_fed=memory.times_fed,
        times_played=memory.times_played,
        sessions_trained=memory.sessions_trained,
        days_together=memory.days_together,
        streak_days=memory.streak_days,
        lines=memory.lines(),
    )
