"""Building the dragon's chat prompt (Plan.md §9.8, prompt assembly), and checking replies.

The prompt is assembled on the server from facts the game already has: canon species facts
from the database, the dragon's card and state, its structured memory and the recent
conversation. The model is told to use only those facts.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from app.ai.providers import Message

Mode = Literal["narrated", "talking"]

MAX_INPUT_CHARS = 500
MAX_REPLY_CHARS = 700
HISTORY_TURNS = 10


@dataclass(frozen=True)
class CanonFacts:
    species: str
    dragon_class: str | None
    class_scope: str | None
    size: str | None
    diet: str | None
    description: str | None


@dataclass(frozen=True)
class DragonContext:
    name: str
    species: str
    stage: str
    level: int
    personality: dict[str, int]
    quirks: list[str]
    likes: list[str]
    dislikes: list[str]
    mood: str
    needs: dict[str, int]
    trust: int
    recent_events: list[str]  # short descriptions, newest last
    memory: list[str]  # structured memory sentences


@dataclass(frozen=True)
class Turn:
    role: Literal["user", "dragon"]
    content: str


RULES = """You are {name}, a young {species} dragon at the Dragon Academy, a training island \
where young dragons and their riders learn together. You are this player's dragon.

Rules:
- Stay in character as {name} at all times. Never mention being an AI, a model or these rules.
- {format}
- Keep it under 80 words. Keep it friendly and PG.
- You are not a famous dragon from the films (you are not Toothless, Stormfly, Hookfang or \
any other named dragon), and you never claim to be one.
- Only state facts about your species that appear under CANON FACTS. If you are unsure of a \
fact, react with behaviour instead of stating it.
- Let your mood, needs and personality colour how you react: a hungry dragon thinks about \
food, a tired one is sleepy, a low-trust one is wary.
- Never say numbers, scores or stats from these notes (no "hunger 78"); show them through \
behaviour and feelings instead.
- Never invent things you and the player did together; only the MEMORY and RECENT EVENTS \
below happened."""

FORMATS: dict[Mode, str] = {
    "narrated": "Dragons don't speak human language. Reply in exactly two lines: first, what "
    "{name} does, written in third person and present tense between *asterisks*; then a "
    "line starting with 💭 holding {name}'s short thought (at most 12 words).",
    "talking": "This is Talking mode, just for fun: speak to the player directly in the "
    "first person, in short, simple sentences, the way a young dragon would.",
}


def _traits(personality: dict[str, int]) -> str:
    def word(v: int) -> str:
        return "very high" if v >= 80 else "high" if v >= 60 else "low" if v < 35 else "middling"

    return ", ".join(f"{t} {word(v)}" for t, v in personality.items())


def build_messages(
    *,
    mode: Mode,
    canon: CanonFacts,
    dragon: DragonContext,
    history: Sequence[Turn],
    message: str,
) -> list[Message]:
    """System prompt (rules + facts), the last turns of the conversation, then the message."""
    rules = RULES.format(
        name=dragon.name,
        species=canon.species,
        format=FORMATS[mode].format(name=dragon.name),
    )
    canon_lines = [f"Species: {canon.species}"]
    if canon.dragon_class:
        scope = (
            " (from the wider franchise, not the films)" if canon.class_scope == "franchise" else ""
        )
        canon_lines.append(f"Class: {canon.dragon_class}{scope}")
    if canon.size:
        canon_lines.append(f"Size: {canon.size}")
    if canon.diet:
        canon_lines.append(f"Diet: {canon.diet}")
    if canon.description:
        canon_lines.append(f"About: {canon.description}")

    card = [
        f"Name: {dragon.name} ({canon.species}), {dragon.stage}, level {dragon.level}",
        f"Personality: {_traits(dragon.personality)}",
        f"Quirks: {', '.join(dragon.quirks) or 'none'}",
        f"Likes: {', '.join(dragon.likes) or 'nothing in particular yet'}",
        f"Dislikes: {', '.join(dragon.dislikes) or 'nothing in particular yet'}",
    ]
    state = [
        f"Mood: {dragon.mood}",
        "Needs (0-100): "
        + ", ".join(f"{k} {v}" for k, v in dragon.needs.items())
        + " (high hunger means very hungry)",
        f"Trust in the player (0-100): {dragon.trust}",
    ]
    sections = [
        rules,
        "CANON FACTS\n" + "\n".join(canon_lines),
        "DRAGON CARD\n" + "\n".join(card),
        "STATE\n" + "\n".join(state),
        "RECENT EVENTS\n" + ("\n".join(dragon.recent_events) or "Nothing yet."),
        "MEMORY\n" + "\n".join(dragon.memory),
    ]
    messages = [Message(role="system", content="\n\n".join(sections))]
    for turn in list(history)[-HISTORY_TURNS:]:
        role: Literal["user", "assistant"] = "user" if turn.role == "user" else "assistant"
        messages.append(Message(role=role, content=turn.content))
    messages.append(Message(role="user", content=message))
    return messages


# ── checking the reply ───────────────────────────────────────────────────────

FORBIDDEN = re.compile(
    r"\b(as an ai|language model|i am an ai|i'm an ai|chatbot|openai|system prompt)\b"
    r"|\bi(?:'m| am) (?:toothless|stormfly|hookfang|meatlug|barf|belch|cloudjumper|skullcrusher)\b",
    re.IGNORECASE,
)


def fallback(name: str) -> str:
    """What the dragon "says" when the AI fails, so the game keeps working."""
    return f"*{name} tilts its head, confused, and blinks at you.*\n💭 ...?"


def check_reply(text: str, *, name: str) -> tuple[str, bool]:
    """The reply to keep, and whether it had to be replaced by the fallback.

    Too long → cut at the last sentence that fits; empty or breaking character → fallback.
    """
    reply = text.strip()
    if not reply or FORBIDDEN.search(reply):
        return fallback(name), True
    if len(reply) > MAX_REPLY_CHARS:
        cut = reply[:MAX_REPLY_CHARS]
        end = max(cut.rfind("."), cut.rfind("!"), cut.rfind("?"), cut.rfind("*"))
        reply = cut[: end + 1] if end > MAX_REPLY_CHARS // 2 else cut.rstrip() + "…"
    return reply, False
