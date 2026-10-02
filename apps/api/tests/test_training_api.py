"""Training sessions through the API. Uses the local database."""

import asyncio
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from .conftest import MakeToken, _rows, _sql, auth_headers
from .test_dragons import _adopted


def _start(client: TestClient, headers: dict[str, str], dragon_id: str, activity: str) -> Any:
    return client.post(
        f"/api/v1/dragons/{dragon_id}/training-sessions",
        headers=headers,
        json={"activity": activity},
    )


def _backdate(database_url: str, session_id: str, seconds: int) -> None:
    """Pretend the session started earlier, so a realistic duration fits inside it."""
    asyncio.run(
        _sql(
            database_url,
            "update training_sessions set started_at = now() - make_interval(secs => :s)"
            " where id = :id",
            s=seconds,
            id=session_id,
        )
    )


def test_overview_lists_activities_with_their_locks(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    body = quiz_client.get(f"/api/v1/dragons/{dragon['id']}/training", headers=headers).json()
    assert body["level"] == 1 and body["stage"]["id"] == "newborn"
    assert {a["id"]: a["unlocked"] for a in body["activities"]} == {
        "flight": True,
        "speed": True,
        "accuracy": False,
        "memory": False,
        "obedience": False,
    }


def test_a_session_is_scored_once(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)

    started = _start(quiz_client, headers, dragon["id"], "flight")
    assert started.status_code == 201
    session_id = started.json()["id"]
    _backdate(database_url, session_id, 20)

    url = f"/api/v1/training-sessions/{session_id}/complete"
    done = quiz_client.post(url, headers=headers, json={"score": 85, "duration_ms": 15_000})
    assert done.status_code == 200
    result = done.json()
    assert result["xp_gained"] > 0
    assert {c["id"] for c in result["stat_changes"]} == {"agility", "speed"}
    assert result["dragon"]["xp"] == result["xp_gained"]
    energy = {n["id"]: n["value"] for n in result["dragon"]["needs"]}["energy"]
    assert energy < {n["id"]: n["value"] for n in dragon["needs"]}["energy"]

    again = quiz_client.post(url, headers=headers, json={"score": 100, "duration_ms": 15_000})
    assert again.status_code == 409

    history = quiz_client.get(f"/api/v1/dragons/{dragon['id']}/history", headers=headers).json()
    assert [(h["activity"], h["score"]) for h in history] == [("flight", 85)]
    assert history[0]["stats_after"]["agility"] == next(
        c["value"] for c in result["stat_changes"] if c["id"] == "agility"
    )


def test_an_implausible_attempt_is_rejected(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    session_id = _start(quiz_client, headers, dragon["id"], "flight").json()["id"]
    # The session started a moment ago, so a 60-second attempt can't be real.
    response = quiz_client.post(
        f"/api/v1/training-sessions/{session_id}/complete",
        headers=headers,
        json={"score": 100, "duration_ms": 60_000},
    )
    assert response.status_code == 422


def test_locked_activities_wait_for_their_stage(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    response = _start(quiz_client, headers, dragon["id"], "accuracy")
    assert response.status_code == 403
    assert "Young" in response.json()["detail"]


def test_an_exhausted_dragon_refuses_and_remembers_it(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    asyncio.run(
        _sql(
            database_url,
            """update player_dragons set needs = '{"hunger": 30, "energy": 5, "happiness": 60}',
               needs_updated_at = now() where id = :id""",
            id=dragon["id"],
        )
    )
    response = _start(quiz_client, headers, dragon["id"], "flight")
    assert response.status_code == 409
    assert "exhausted" in response.json()["detail"]
    kinds = asyncio.run(
        _rows(database_url, "select kind from dragon_events where dragon_id = :id", id=dragon["id"])
    )
    assert "refused" in kinds


def test_training_errors(quiz_client: TestClient, make_token: MakeToken, player: UUID) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    assert _start(quiz_client, headers, dragon["id"], "juggling").status_code == 422

    stranger = auth_headers(make_token, uuid4())
    assert _start(quiz_client, stranger, dragon["id"], "flight").status_code == 404
    session_id = _start(quiz_client, headers, dragon["id"], "flight").json()["id"]
    response = quiz_client.post(
        f"/api/v1/training-sessions/{session_id}/complete",
        headers=stranger,
        json={"score": 50, "duration_ms": 5000},
    )
    assert response.status_code == 404
