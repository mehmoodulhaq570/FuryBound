"""The AI layer without a real model: the Ollama client, prompts, reply checks, memory."""

import asyncio
import json
from datetime import UTC, date, datetime

import httpx
import pytest
from pydantic import BaseModel

from app.ai import prompts
from app.ai.providers import LLMError, Message, OllamaProvider
from app.engines.memory import Event, summarize

# ── Ollama client (with a fake network) ──────────────────────────────────────


def _ollama(handler: httpx.MockTransport) -> OllamaProvider:
    return OllamaProvider("http://ollama.test", "test-model", 5, transport=handler)


async def _collect(provider: OllamaProvider) -> str:
    pieces = [
        p
        async for p in provider.stream_chat(
            [Message(role="user", content="hi")], max_tokens=50, temperature=0.5
        )
    ]
    return "".join(pieces)


def test_ollama_streams_the_reply() -> None:
    sent: list[dict[str, object]] = []

    def handle(request: httpx.Request) -> httpx.Response:
        sent.append(json.loads(request.content))
        lines = [
            {"message": {"role": "assistant", "content": "*Ember "}, "done": False},
            {"message": {"role": "assistant", "content": "purrs.*"}, "done": False},
            {"message": {"role": "assistant", "content": ""}, "done": True},
        ]
        return httpx.Response(200, text="\n".join(json.dumps(line) for line in lines))

    assert asyncio.run(_collect(_ollama(httpx.MockTransport(handle)))) == "*Ember purrs.*"
    assert sent[0]["model"] == "test-model"
    assert sent[0]["stream"] is True
    assert sent[0]["options"] == {"num_predict": 50, "temperature": 0.5}
    assert sent[0]["think"] is False  # thinking models would otherwise use up the budget


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(404, text='{"error": "model not found"}'),
        httpx.Response(200, text=json.dumps({"error": "out of memory"})),
    ],
)
def test_ollama_errors_become_llm_errors(response: httpx.Response) -> None:
    with pytest.raises(LLMError):
        asyncio.run(_collect(_ollama(httpx.MockTransport(lambda _: response))))


def test_ollama_unreachable_is_an_llm_error() -> None:
    def refuse(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused")

    with pytest.raises(LLMError, match="unreachable"):
        asyncio.run(_collect(_ollama(httpx.MockTransport(refuse))))


class Mood(BaseModel):
    mood: str


def test_ollama_json_replies_follow_the_schema() -> None:
    def handle(request: httpx.Request) -> httpx.Response:
        assert json.loads(request.content)["format"]["properties"] == {
            "mood": {"title": "Mood", "type": "string"}
        }
        return httpx.Response(200, json={"message": {"content": '{"mood": "happy"}'}})

    provider = _ollama(httpx.MockTransport(handle))
    result = asyncio.run(provider.generate_json([Message(role="user", content="?")], Mood))
    assert result == Mood(mood="happy")


# ── prompt ───────────────────────────────────────────────────────────────────

CANON = prompts.CanonFacts(
    species="Deadly Nadder",
    dragon_class="Tracker",
    class_scope="franchise",
    size="medium",
    diet=None,
    description="A vain, bird-like dragon with spines on its tail.",
)
DRAGON = prompts.DragonContext(
    name="Ember",
    species="Deadly Nadder",
    stage="Newborn",
    level=2,
    personality={"courage": 70, "curiosity": 30},
    quirks=["Hoards shiny things"],
    likes=["chicken"],
    dislikes=["eel"],
    mood="hungry",
    needs={"hunger": 80, "energy": 60, "happiness": 50},
    trust=22,
    recent_events=["Was fed eel."],
    memory=["Favourite food so far: chicken."],
)


def test_the_prompt_carries_rules_facts_card_state_and_memory() -> None:
    messages = prompts.build_messages(
        mode="narrated", canon=CANON, dragon=DRAGON, history=[], message="Hello!"
    )
    system = messages[0].content
    assert messages[0].role == "system"
    assert "You are Ember, a young Deadly Nadder" in system
    assert "💭" in system  # the narrated format
    assert "Class: Tracker (from the wider franchise, not the films)" in system
    assert "Mood: hungry" in system and "Trust in the player (0-100): 22" in system
    assert "Was fed eel." in system and "Favourite food so far: chicken." in system
    assert "courage high, curiosity low" in system
    assert messages[-1] == Message(role="user", content="Hello!")


def test_talking_mode_and_history() -> None:
    history = [prompts.Turn("user" if i % 2 == 0 else "dragon", f"turn {i}") for i in range(14)]
    messages = prompts.build_messages(
        mode="talking", canon=CANON, dragon=DRAGON, history=history, message="Bye"
    )
    assert "Talking mode" in messages[0].content and "💭" not in messages[0].content
    # Only the last 10 turns, as user/assistant, then the new message.
    assert [m.content for m in messages[1:-1]] == [f"turn {i}" for i in range(4, 14)]
    assert {m.role for m in messages[1:-1]} == {"user", "assistant"}


@pytest.mark.parametrize(
    "reply",
    ["", "   ", "As an AI language model, I can't.", "Hi! I'm Toothless, nice to meet you."],
)
def test_replies_that_break_character_use_the_fallback(reply: str) -> None:
    text, used_fallback = prompts.check_reply(reply, name="Ember")
    assert used_fallback and "Ember tilts its head" in text


def test_long_replies_are_cut_at_a_sentence() -> None:
    reply = "Ember flaps happily. " * 60
    text, used_fallback = prompts.check_reply(reply, name="Ember")
    assert not used_fallback
    assert len(text) <= prompts.MAX_REPLY_CHARS and text.endswith(".")


# ── structured memory ────────────────────────────────────────────────────────


def _at(day: int, hour: int = 12) -> datetime:
    return datetime(2026, 10, day, hour, tzinfo=UTC)


def test_memory_sums_up_the_diary() -> None:
    events = [
        Event("adopted", {"name": "Ember"}, _at(1)),
        Event("fed", {"food": "eel"}, _at(1)),
        Event("fed", {"food": "chicken"}, _at(2)),
        Event("fed", {"food": "chicken"}, _at(3)),
        Event("fed", {"food": "bread"}, _at(3)),
        Event("fed", {"food": "bread"}, _at(3)),
        Event("fed", {"food": "bread"}, _at(4)),
        Event("trained", {"activity": "flight", "score": 60}, _at(3)),
        Event("trained", {"activity": "speed", "score": 90}, _at(4)),
        Event("refused", {"activity": "speed"}, _at(4)),
        Event("played", {}, _at(4)),
    ]
    memory = summarize(events, likes=["chicken"], dislikes=["eel"], today=date(2026, 10, 4))
    # Bread was fed most, but chicken is the one it likes.
    assert memory.favourite_food == "chicken"
    assert memory.favourite_activity == "speed"
    assert memory.disliked_foods == ("eel",)
    assert memory.refused_activities == ("speed",)
    assert (memory.times_fed, memory.times_played, memory.sessions_trained) == (6, 1, 2)
    assert memory.days_together == 4
    assert memory.streak_days == 4
    assert "Looked after every day for 4 days in a row." in memory.lines()


def test_a_missed_day_breaks_the_streak_but_today_can_still_come() -> None:
    events = [Event("adopted", {}, _at(1)), Event("fed", {"food": "fish"}, _at(1))]
    events += [Event("played", {}, _at(3))]
    assert summarize(events, likes=[], dislikes=[], today=date(2026, 10, 4)).streak_days == 1
    assert summarize(events, likes=[], dislikes=[], today=date(2026, 10, 5)).streak_days == 0


def test_a_new_dragon_has_little_to_remember() -> None:
    memory = summarize(
        [Event("adopted", {}, _at(4))], likes=["fish"], dislikes=[], today=date(2026, 10, 4)
    )
    assert memory.favourite_food is None and memory.favourite_activity is None
    assert memory.lines() == ["Together for 1 day: fed 0 times, played 0 times, trained 0 times."]
