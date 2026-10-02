"""Quiz endpoints. GET /quiz needs no database; attempts are stored in the local one."""

import asyncio
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db.session import create_engine
from app.engines.game_data import TRAITS, get_game_data

from .conftest import MakeToken
from .conftest import auth_headers as _auth
from .conftest import first_answers as _first_answers

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


# ── encounter ────────────────────────────────────────────────────────────────


def _choices(**overrides: str) -> dict[str, str]:
    scenes = get_game_data().encounter.scenes
    return {
        "encounter_version": get_game_data().encounter.version,
        "first_contact": scenes.first_contact.options[0].id,
        "offering": scenes.offering.options[0].id,
        "startle": scenes.startle.options[0].id,
        **overrides,
    }


def _new_attempt(client: TestClient, headers: dict[str, str]) -> str:
    response = client.post(
        "/api/v1/quiz/attempts",
        headers=headers,
        json={"quiz_version": "quiz_v1", "answers": _first_answers()},
    )
    assert response.status_code == 201
    return str(response.json()["id"])


def test_encounter_needs_sign_in(client: TestClient) -> None:
    assert client.get("/api/v1/encounter").status_code == 401


def test_encounter_hides_what_options_mean(client: TestClient, make_token: MakeToken) -> None:
    body = client.get("/api/v1/encounter", headers=_auth(make_token, uuid4())).json()

    encounter = get_game_data().encounter
    assert body["version"] == encounter.version
    assert [s["id"] for s in body["scenes"]] == ["first_contact", "offering", "startle"]
    for scene in body["scenes"]:
        want = getattr(encounter.scenes, scene["id"])
        assert scene["prompt"] == want.prompt
        assert sorted(o["id"] for o in scene["options"]) == sorted(o.id for o in want.options)
        assert all(set(o) == {"id", "label"} for o in scene["options"])


def test_encounter_completes_the_attempt_once(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = _auth(make_token, player)
    attempt_id = _new_attempt(quiz_client, headers)
    url = f"/api/v1/quiz/attempts/{attempt_id}"

    assert quiz_client.get(url, headers=headers).json()["match"] is None

    response = quiz_client.post(f"{url}/encounter", headers=headers, json=_choices())
    assert response.status_code == 200
    match = response.json()["match"]
    profiles = {s.id for s in get_game_data().species}
    dragons = [match["top"], *match["runners_up"]]
    assert len(dragons) == 3
    assert len({d["species_id"] for d in dragons}) == 3
    assert all(d["species_id"] in profiles for d in dragons)
    assert all(60 <= d["compatibility"] <= 99 and d["explanation"] for d in dragons)
    assert match["top"]["compatibility"] >= match["runners_up"][0]["compatibility"]

    # The result is saved: reloading shows the same dragon, and it can't be rerolled.
    assert quiz_client.get(url, headers=headers).json()["match"] == match
    again = quiz_client.post(f"{url}/encounter", headers=headers, json=_choices())
    assert again.status_code == 409


def test_other_players_cannot_see_or_finish_an_attempt(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    attempt_id = _new_attempt(quiz_client, _auth(make_token, player))
    stranger = _auth(make_token, uuid4())
    url = f"/api/v1/quiz/attempts/{attempt_id}"

    assert quiz_client.get(url, headers=stranger).status_code == 404
    assert (
        quiz_client.post(f"{url}/encounter", headers=stranger, json=_choices()).status_code == 404
    )


@pytest.mark.parametrize(
    ("overrides", "status_code"),
    [
        pytest.param({"offering": "dragon_nip"}, 422, id="unknown option"),
        pytest.param({"encounter_version": "encounter_v0"}, 409, id="old encounter version"),
    ],
)
def test_encounter_rejects_bad_choices(
    quiz_client: TestClient,
    make_token: MakeToken,
    player: UUID,
    overrides: dict[str, str],
    status_code: int,
) -> None:
    headers = _auth(make_token, player)
    attempt_id = _new_attempt(quiz_client, headers)
    response = quiz_client.post(
        f"/api/v1/quiz/attempts/{attempt_id}/encounter",
        headers=headers,
        json=_choices(**overrides),
    )
    assert response.status_code == status_code
    # A rejected submission leaves the attempt open.
    assert (
        quiz_client.get(f"/api/v1/quiz/attempts/{attempt_id}", headers=headers).json()["match"]
        is None
    )
