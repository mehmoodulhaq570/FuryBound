"""Quiz endpoints. GET /quiz needs no database; attempts are stored in the local one."""

import asyncio
from collections.abc import Iterator
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth import TokenVerifier, get_token_verifier
from app.config import Settings
from app.db.session import create_engine
from app.engines.game_data import TRAITS, get_game_data
from app.main import create_app

from .conftest import MakeToken


def _auth(make_token: MakeToken, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(sub=user_id)}"}


def _first_answers() -> dict[str, str]:
    return {q.id: q.options[0].id for q in get_game_data().quiz.questions}


async def _sql(url: str, statement: str, **params: object) -> None:
    engine = create_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text(statement), params)
    finally:
        await engine.dispose()


@pytest.fixture
def player(database_url: str) -> Iterator[UUID]:
    """A throwaway auth user (attempts reference auth.users); deleted with its attempts."""
    user_id = uuid4()
    asyncio.run(
        _sql(
            database_url,
            "insert into auth.users (id, email) values (:id, :email)",
            id=user_id,
            email=f"{user_id}@quiz.test",
        )
    )
    yield user_id
    asyncio.run(_sql(database_url, "delete from auth.users where id = :id", id=user_id))


@pytest.fixture
def quiz_client(database_url: str, verifier: TokenVerifier) -> Iterator[TestClient]:
    app = create_app(Settings(app_env="test", database_url=database_url))
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    with TestClient(app) as test_client:
        yield test_client


# ── GET /quiz ────────────────────────────────────────────────────────────────


def test_quiz_needs_sign_in(client: TestClient) -> None:
    assert client.get("/api/v1/quiz").status_code == 401


def test_quiz_hides_scores_and_keeps_every_option(
    client: TestClient, make_token: MakeToken
) -> None:
    body = client.get("/api/v1/quiz", headers=_auth(make_token, uuid4())).json()

    quiz = get_game_data().quiz
    assert body["version"] == quiz.version
    assert [q["id"] for q in body["questions"]] == [q.id for q in quiz.questions]
    for got, want in zip(body["questions"], quiz.questions, strict=True):
        assert sorted(o["id"] for o in got["options"]) == sorted(o.id for o in want.options)
        assert all(set(o) == {"id", "label"} for o in got["options"])


def test_option_order_is_stable_per_player_and_varies_between_players(
    client: TestClient, make_token: MakeToken
) -> None:
    def order(user_id: UUID) -> list[list[str]]:
        body = client.get("/api/v1/quiz", headers=_auth(make_token, user_id)).json()
        return [[o["id"] for o in q["options"]] for q in body["questions"]]

    alice = uuid4()
    assert order(alice) == order(alice)
    assert any(order(uuid4()) != order(alice) for _ in range(3))


# ── POST /quiz/attempts ──────────────────────────────────────────────────────


def test_attempt_is_scored_and_saved(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    response = quiz_client.post(
        "/api/v1/quiz/attempts",
        headers=_auth(make_token, player),
        json={"quiz_version": "quiz_v1", "answers": _first_answers()},
    )

    assert response.status_code == 201
    body = response.json()
    assert [t["id"] for t in body["traits"]] == list(TRAITS)
    assert all(0 <= t["score"] <= 100 for t in body["traits"])

    async def saved() -> int:
        engine = create_engine(database_url)
        try:
            async with engine.connect() as conn:
                result = await conn.execute(
                    text("select count(*) from quiz_attempts where id = :id and user_id = :u"),
                    {"id": body["id"], "u": player},
                )
                return int(result.scalar_one())
        finally:
            await engine.dispose()

    assert asyncio.run(saved()) == 1


def test_attempt_rejects_an_old_quiz_version(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    response = quiz_client.post(
        "/api/v1/quiz/attempts",
        headers=_auth(make_token, player),
        json={"quiz_version": "quiz_v0", "answers": _first_answers()},
    )
    assert response.status_code == 409


@pytest.mark.parametrize(
    "change",
    [
        pytest.param(lambda a: a.pop("q01_injured_dragon"), id="missing question"),
        pytest.param(lambda a: a.update(q01_injured_dragon="z"), id="unknown option"),
        pytest.param(lambda a: a.update(q99_made_up="a"), id="unknown question"),
    ],
)
def test_attempt_rejects_bad_answers(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, change: object
) -> None:
    answers = _first_answers()
    change(answers)  # type: ignore[operator]
    response = quiz_client.post(
        "/api/v1/quiz/attempts",
        headers=_auth(make_token, player),
        json={"quiz_version": "quiz_v1", "answers": answers},
    )
    assert response.status_code == 422
