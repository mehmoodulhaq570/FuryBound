"""Adopting and reading the player's dragon. Uses the local database."""

from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.engines.game_data import TRAITS, get_game_data

from .conftest import MakeToken, auth_headers, first_answers


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
