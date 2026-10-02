"""Adopting and reading the player's dragon. Uses the local database."""

import asyncio
from typing import Any
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.engines.game_data import TRAITS, get_game_data

from .conftest import MakeToken, _rows, _sql, auth_headers, first_answers


def _finished_attempt(
    client: TestClient, headers: dict[str, str], *, encounter: bool = True
) -> str:
    response = client.post(
        "/api/v1/quiz/attempts",
        headers=headers,
        json={"quiz_version": "quiz_v1", "answers": first_answers()},
    )
    attempt_id = str(response.json()["id"])
    if encounter:
        scenes = get_game_data().encounter.scenes
        response = client.post(
            f"/api/v1/quiz/attempts/{attempt_id}/encounter",
            headers=headers,
            json={
                "encounter_version": get_game_data().encounter.version,
                "first_contact": scenes.first_contact.options[0].id,
                "offering": scenes.offering.options[0].id,
                "startle": scenes.startle.options[0].id,
            },
        )
        assert response.status_code == 200
    return attempt_id


def test_dragons_need_sign_in(client: TestClient) -> None:
    assert client.get("/api/v1/dragons/me").status_code == 401


def test_adopt_the_dragon_that_chose_you(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    assert quiz_client.get("/api/v1/dragons/me", headers=headers).status_code == 404

    attempt_id = _finished_attempt(quiz_client, headers)
    top = quiz_client.get(f"/api/v1/quiz/attempts/{attempt_id}", headers=headers).json()["match"][
        "top"
    ]

    response = quiz_client.post(
        "/api/v1/dragons", headers=headers, json={"attempt_id": attempt_id, "name": " Ember "}
    )
    assert response.status_code == 201
    dragon = response.json()
    assert dragon["name"] == "Ember"
    assert dragon["species_id"] == top["species_id"]
    assert dragon["species_name"] == top["name"]
    assert dragon["compatibility"] == top["compatibility"]
    assert [t["id"] for t in dragon["personality"]] == list(TRAITS)
    assert {n["id"]: n["value"] for n in dragon["needs"]} == {
        "hunger": 30,
        "energy": 80,
        "happiness": 60,
    }
    assert dragon["trust"] == 20
    assert dragon["color_variant"] and dragon["color_hex"].startswith("#")
    assert dragon["level"] == 1 and dragon["stage"] == "newborn"
    assert 1 <= len(dragon["quirks"]) <= 2 and all(q["label"] for q in dragon["quirks"])

    # It's saved, and there's only ever one.
    assert quiz_client.get("/api/v1/dragons/me", headers=headers).json() == dragon
    second = _finished_attempt(quiz_client, headers)
    again = quiz_client.post(
        "/api/v1/dragons", headers=headers, json={"attempt_id": second, "name": "Spare"}
    )
    assert again.status_code == 409


def test_adoption_needs_a_finished_encounter(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    attempt_id = _finished_attempt(quiz_client, headers, encounter=False)
    response = quiz_client.post(
        "/api/v1/dragons", headers=headers, json={"attempt_id": attempt_id, "name": "Ember"}
    )
    assert response.status_code == 409


def test_cannot_adopt_from_someone_elses_attempt(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    attempt_id = _finished_attempt(quiz_client, auth_headers(make_token, player))
    response = quiz_client.post(
        "/api/v1/dragons",
        headers=auth_headers(make_token, uuid4()),
        json={"attempt_id": attempt_id, "name": "Ember"},
    )
    assert response.status_code == 404


@pytest.mark.parametrize("name", ["E", "R2D2", "Shit"])
def test_bad_names_are_refused_with_a_reason(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, name: str
) -> None:
    headers = auth_headers(make_token, player)
    attempt_id = _finished_attempt(quiz_client, headers)
    response = quiz_client.post(
        "/api/v1/dragons", headers=headers, json={"attempt_id": attempt_id, "name": name}
    )
    assert response.status_code == 422
    assert response.json()["detail"]
    assert quiz_client.get("/api/v1/dragons/me", headers=headers).status_code == 404


# ── care (Plan §9.6-9.7) ─────────────────────────────────────────────────────


def _adopted(client: TestClient, headers: dict[str, str]) -> dict[str, Any]:
    attempt_id = _finished_attempt(client, headers)
    response = client.post(
        "/api/v1/dragons", headers=headers, json={"attempt_id": attempt_id, "name": "Ember"}
    )
    assert response.status_code == 201
    dragon: dict[str, Any] = response.json()
    return dragon


def _needs(dragon: dict[str, Any]) -> dict[str, int]:
    return {n["id"]: n["value"] for n in dragon["needs"]}


def test_the_card_has_a_mood_a_thought_and_foods(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    dragon = _adopted(quiz_client, auth_headers(make_token, player))
    assert dragon["mood"]["id"] in {"hungry", "tired", "angry", "excited", "curious", "happy"}
    assert "Ember" in dragon["thought"]
    assert "fish" in dragon["foods"]


def test_feeding_changes_needs_and_is_logged(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    liked = dragon["likes"][0]

    response = quiz_client.post(
        f"/api/v1/dragons/{dragon['id']}/feed", headers=headers, json={"food": liked}
    )
    assert response.status_code == 200
    result = response.json()
    assert "Ember" in result["message"]
    fed = result["dragon"]
    assert _needs(fed)["hunger"] < _needs(dragon)["hunger"]
    assert _needs(fed)["happiness"] > _needs(dragon)["happiness"]
    assert fed["trust"] > dragon["trust"]
    # Saved: reading it back gives the same needs.
    assert _needs(quiz_client.get("/api/v1/dragons/me", headers=headers).json()) == _needs(fed)

    kinds = asyncio.run(
        _rows(
            database_url,
            "select kind from dragon_events where dragon_id = :id order by id",
            id=dragon["id"],
        )
    )
    assert kinds == ["adopted", "fed"]


def test_a_full_dragon_refuses_food(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    url = f"/api/v1/dragons/{dragon['id']}/feed"
    assert quiz_client.post(url, headers=headers, json={"food": "fish"}).status_code == 200

    refused = quiz_client.post(url, headers=headers, json={"food": "fish"})
    assert refused.status_code == 409
    assert "isn't hungry" in refused.json()["detail"]


def test_rest_and_play(quiz_client: TestClient, make_token: MakeToken, player: UUID) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    played = quiz_client.post(f"/api/v1/dragons/{dragon['id']}/play", headers=headers)
    assert played.status_code == 200
    assert _needs(played.json()["dragon"])["energy"] < _needs(dragon)["energy"]
    rested = quiz_client.post(f"/api/v1/dragons/{dragon['id']}/rest", headers=headers)
    assert rested.status_code == 200
    assert _needs(rested.json()["dragon"])["energy"] > _needs(played.json()["dragon"])["energy"]


def test_needs_drift_while_the_player_is_away(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    asyncio.run(
        _sql(
            database_url,
            "update player_dragons set needs_updated_at = now() - interval '11 hours'"
            " where id = :id",
            id=dragon["id"],
        )
    )
    later = quiz_client.get("/api/v1/dragons/me", headers=headers).json()
    assert _needs(later)["hunger"] == _needs(dragon)["hunger"] + 44
    assert _needs(later)["happiness"] == _needs(dragon)["happiness"] - 22
    assert later["mood"]["id"] == "hungry"


def test_care_errors(quiz_client: TestClient, make_token: MakeToken, player: UUID) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    url = f"/api/v1/dragons/{dragon['id']}"

    assert (
        quiz_client.post(f"{url}/feed", headers=headers, json={"food": "dragon_nip"}).status_code
        == 422
    )
    stranger = auth_headers(make_token, uuid4())
    assert quiz_client.post(f"{url}/play", headers=stranger).status_code == 404
