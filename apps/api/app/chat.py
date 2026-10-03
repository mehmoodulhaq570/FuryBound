"""Chatting with your dragon (Plan.md §9.8): context, limits, streaming and saving the reply."""

import json
import time
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.ai import prompts
from app.ai.providers import LLMError, LLMProvider, Message
from app.db.models import ChatMessageRow, DragonEventRow, PlayerDragonRow, SpeciesRow
from app.dragons import NoDragon, Rulebook, mine, now, state
from app.engines.memory import Event, MemorySummary, summarize
from app.schemas.chat import ChatMessage, StreamDelta, StreamDone

MAX_TOKENS = 150  # about 100 words: room for the 80-word target, but no essays
TEMPERATURE = 0.8
RECENT_EVENTS = 3


class InvalidMessage(ValueError):
    pass


class RateLimited(Exception):
    pass


def describe(event: Event) -> str | None:
    """A short line about an event, for the prompt (None for events not worth mentioning)."""
    p = event.payload
    match event.kind:
        case "adopted":
            return f"Was adopted and named {p.get('name', '')} by the player."
        case "fed":
            return f"Was fed {p.get('food', 'something')}."
        case "rested":
            return "Had a rest."
        case "played":
            return "Played with the player."
        case "trained":
            return f"Trained at {p.get('activity', '?')} (score {p.get('score', '?')}/100)."
        case "refused":
            return f"Refused to train at {p.get('activity', '?')}."
        case "level_up":
            return f"Reached level {p.get('level', '?')}."
    return None


async def _events(session: AsyncSession, dragon_id: UUID) -> list[Event]:
    rows = await session.scalars(
        select(DragonEventRow)
        .where(DragonEventRow.dragon_id == dragon_id)
        .order_by(DragonEventRow.created_at, DragonEventRow.id)
    )
    return [Event(r.kind, r.payload, r.created_at) for r in rows]


async def memory_of(session: AsyncSession, row: PlayerDragonRow, at: datetime) -> MemorySummary:
    """The dragon's structured memory (tier 1), from its diary."""
    events = await _events(session, row.id)
    return summarize(events, likes=row.likes, dislikes=row.dislikes, today=at.date())


async def _context(
    session: AsyncSession, book: Rulebook, row: PlayerDragonRow, at: datetime
) -> tuple[prompts.CanonFacts, prompts.DragonContext]:
    species = await session.get(SpeciesRow, row.species_id)
    canon = prompts.CanonFacts(
        species=species.name if species else row.species_id.replace("_", " ").title(),
        dragon_class=species.class_ if species else None,
        class_scope=species.class_scope if species else None,
        size=species.size if species else None,
        diet=species.diet if species else None,
        description=species.description if species else None,
    )
    needs, mood = await state(session, book, row, at)
    events = await _events(session, row.id)
    memory = summarize(events, likes=row.likes, dislikes=row.dislikes, today=at.date())
    recent = [line for e in events if (line := describe(e))][-RECENT_EVENTS:]
    quirk_labels = {q.id: q.label for q in book.adoption.quirks}
    dragon = prompts.DragonContext(
        name=row.name,
        species=canon.species,
        stage=book.progression.stage(row.stage).label,
        level=row.level,
        personality=row.personality,
        quirks=[quirk_labels.get(q, q) for q in row.quirks],
        likes=row.likes,
        dislikes=row.dislikes,
        mood=mood,
        needs={str(k): v for k, v in needs.items()},
        trust=row.trust,
        recent_events=recent,
        memory=memory.lines(),
    )
    return canon, dragon


def _message(row: ChatMessageRow) -> ChatMessage:
    return ChatMessage(
        id=row.id,
        role=row.role,
        content=row.content,
        mode=row.mode,
        created_at=row.created_at,
    )


async def history(
    session: AsyncSession, user_id: UUID, dragon_id: UUID, limit: int = 50
) -> list[ChatMessage]:
    """The latest messages, oldest first."""
    if await mine(session, user_id, dragon_id) is None:
        raise NoDragon(f"No dragon {dragon_id}")
    rows = await session.scalars(
        select(ChatMessageRow)
        .where(ChatMessageRow.dragon_id == dragon_id)
        .order_by(ChatMessageRow.id.desc())
        .limit(limit)
    )
    return [_message(r) for r in reversed(list(rows))]


async def prepare(
    session: AsyncSession,
    book: Rulebook,
    user_id: UUID,
    dragon_id: UUID,
    text: str,
    mode: prompts.Mode,
    daily_limit: int,
) -> tuple[list[Message], str]:
    """Check and save the player's message; return the prompt and the dragon's name.

    Raises NoDragon, InvalidMessage or RateLimited.
    """
    text = text.strip()
    if not text:
        raise InvalidMessage("Say something first")
    if len(text) > prompts.MAX_INPUT_CHARS:
        raise InvalidMessage(f"Messages are at most {prompts.MAX_INPUT_CHARS} characters")
    row = await mine(session, user_id, dragon_id)
    if row is None:
        raise NoDragon(f"No dragon {dragon_id}")

    at = now()
    midnight = datetime(at.year, at.month, at.day, tzinfo=UTC)
    sent_today = await session.scalar(
        select(func.count())
        .select_from(ChatMessageRow)
        .where(
            ChatMessageRow.dragon_id == dragon_id,
            ChatMessageRow.role == "user",
            ChatMessageRow.created_at >= midnight,
        )
    )
    if (sent_today or 0) >= daily_limit:
        raise RateLimited(f"{row.name} needs a break from talking. Come back tomorrow!")

    earlier = await session.scalars(
        select(ChatMessageRow)
        .where(ChatMessageRow.dragon_id == dragon_id)
        .order_by(ChatMessageRow.id.desc())
        .limit(prompts.HISTORY_TURNS)
    )
    turns = [prompts.Turn(r.role, r.content) for r in reversed(list(earlier))]  # type: ignore[arg-type]
    canon, dragon = await _context(session, book, row, at)
    messages = prompts.build_messages(
        mode=mode, canon=canon, dragon=dragon, history=turns, message=text
    )

    session.add(ChatMessageRow(dragon_id=dragon_id, role="user", content=text, mode=mode))
    await session.commit()
    return messages, row.name


def _sse(event: StreamDelta | StreamDone) -> str:
    return f"data: {json.dumps(event.model_dump(mode='json'), ensure_ascii=False)}\n\n"


async def stream_reply(
    sessions: async_sessionmaker[AsyncSession],
    llm: LLMProvider,
    dragon_id: UUID,
    name: str,
    messages: list[Message],
    mode: prompts.Mode,
) -> AsyncIterator[str]:
    """Server-sent events: the reply as it's generated, then the checked, saved reply.

    If the model fails part-way, the dragon's stock reply is used, so the game keeps working.
    """
    started = time.monotonic()
    pieces: list[str] = []
    error: str | None = None
    try:
        async for piece in llm.stream_chat(
            messages, max_tokens=MAX_TOKENS, temperature=TEMPERATURE
        ):
            pieces.append(piece)
            yield _sse(StreamDelta(text=piece))
    except LLMError as exc:
        error = str(exc)

    if error:
        reply, used_fallback = prompts.fallback(name), True
    else:
        reply, used_fallback = prompts.check_reply("".join(pieces), name=name)
    meta = {
        "provider": llm.name,
        "ms": round((time.monotonic() - started) * 1000),
        "fallback": used_fallback,
        **({"error": error[:300]} if error else {}),
    }
    # The request's own database session may already be closed while streaming.
    async with sessions() as session:
        row = ChatMessageRow(
            dragon_id=dragon_id, role="dragon", content=reply, mode=mode, meta=meta
        )
        session.add(row)
        session.add(DragonEventRow(dragon_id=dragon_id, kind="chatted", payload={"mode": mode}))
        await session.commit()
        await session.refresh(row)
        yield _sse(StreamDone(message=_message(row), fallback=used_fallback))
