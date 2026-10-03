"""Chatting with your dragon through the API, with a fake AI. Uses the local database."""

import asyncio
import json
from collections.abc import Iterator
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.providers import FakeProvider, get_llm
from app.auth import TokenVerifier, get_token_verifier
from app.config import Settings
from app.main import create_app

from .conftest import MakeToken, _rows, auth_headers
from .test_dragons import _adopted


@pytest.fixture
def fake() -> FakeProvider:
    return FakeProvider(["*Ember sniffs your hand.*\n💭 Snack?"])


@pytest.fixture
def chat_client(
    database_url: str, verifier: TokenVerifier, fake: FakeProvider
) -> Iterator[TestClient]:
    app = create_app(Settings(app_env="test", database_url=database_url, chat_daily_limit=3))
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    app.dependency_overrides[get_llm] = lambda: fake
    with TestClient(app) as client:
        yield client


def _events(response: Any) -> list[dict[str, Any]]:
    return [
        json.loads(line.removeprefix("data: "))
        for line in response.text.splitlines()
        if line.startswith("data: ")
    ]


def _say(
    client: TestClient, headers: dict[str, str], dragon_id: str, text: str, **extra: Any
) -> Any:
    return client.post(
        f"/api/v1/dragons/{dragon_id}/chat", headers=headers, json={"message": text, **extra}
    )


def test_the_reply_streams_and_is_saved(
    chat_client: TestClient,
    make_token: MakeToken,
    player: UUID,
    fake: FakeProvider,
    database_url: str,
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(chat_client, headers)

    response = _say(chat_client, headers, dragon["id"], "  Hello Ember!  ")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    events = _events(response)
    assert {e["type"] for e in events[:-1]} == {"delta"}
    done = events[-1]
    assert done["type"] == "done" and done["fallback"] is False
    assert done["message"]["content"] == "*Ember sniffs your hand.*\n💭 Snack?"
    assert "".join(e["text"] for e in events[:-1]).strip() == done["message"]["content"]

    history = chat_client.get(f"/api/v1/dragons/{dragon['id']}/messages", headers=headers).json()
    assert [(m["role"], m["content"]) for m in history] == [
        ("user", "Hello Ember!"),
        ("dragon", "*Ember sniffs your hand.*\n💭 Snack?"),
    ]
    kinds = asyncio.run(
        _rows(database_url, "select kind from dragon_events where dragon_id = :id", id=dragon["id"])
    )
    assert "chatted" in kinds


def test_the_prompt_knows_the_dragon_and_the_conversation(
    chat_client: TestClient, make_token: MakeToken, player: UUID, fake: FakeProvider
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(chat_client, headers)
    chat_client.post(f"/api/v1/dragons/{dragon['id']}/feed", headers=headers, json={"food": "fish"})
    _say(chat_client, headers, dragon["id"], "First")
    _say(chat_client, headers, dragon["id"], "Second", mode="talking")

    system, *turns = fake.calls[-1]
    assert f"You are Ember, a young {dragon['species_name']}" in system.content
    assert "Talking mode" in system.content
    assert "Was fed fish." in system.content
    assert [(m.role, m.content) for m in turns] == [
        ("user", "First"),
        ("assistant", "*Ember sniffs your hand.*\n💭 Snack?"),
        ("user", "Second"),
    ]


def test_when_the_ai_fails_the_dragon_still_answers(
    chat_client: TestClient, make_token: MakeToken, player: UUID, fake: FakeProvider
) -> None:
    fake.fail = True
    headers = auth_headers(make_token, player)
    dragon = _adopted(chat_client, headers)
    done = _events(_say(chat_client, headers, dragon["id"], "Hello?"))[-1]
    assert done["fallback"] is True
    assert "tilts its head" in done["message"]["content"]


def test_messages_are_checked_and_limited(
    chat_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(chat_client, headers)
    assert _say(chat_client, headers, dragon["id"], "   ").status_code == 422
    assert _say(chat_client, headers, dragon["id"], "x" * 501).status_code == 422

    for _ in range(3):  # the test app allows 3 a day
        assert _say(chat_client, headers, dragon["id"], "Hi").status_code == 200
    limited = _say(chat_client, headers, dragon["id"], "Hi")
    assert limited.status_code == 429
    assert "Come back tomorrow" in limited.json()["detail"]


def test_strangers_cant_chat_or_read(
    chat_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    dragon = _adopted(chat_client, auth_headers(make_token, player))
    stranger = auth_headers(make_token, uuid4())
    assert _say(chat_client, stranger, dragon["id"], "Hi").status_code == 404
    url = f"/api/v1/dragons/{dragon['id']}"
    assert chat_client.get(f"{url}/messages", headers=stranger).status_code == 404
    assert chat_client.get(f"{url}/memory", headers=stranger).status_code == 404


def test_memory_from_the_diary(
    chat_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(chat_client, headers)
    liked = dragon["likes"][0]
    chat_client.post(f"/api/v1/dragons/{dragon['id']}/feed", headers=headers, json={"food": liked})
    memory = chat_client.get(f"/api/v1/dragons/{dragon['id']}/memory", headers=headers).json()
    assert memory["favourite_food"] == liked
    assert memory["times_fed"] == 1 and memory["days_together"] == 1
    assert f"Favourite food so far: {liked}." in memory["lines"]
