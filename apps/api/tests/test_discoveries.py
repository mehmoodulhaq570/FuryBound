"""Discoveries for the Dragon Book's Academy mode. Uses the local database."""

from uuid import UUID

from fastapi.testclient import TestClient

from .conftest import MakeToken, auth_headers
from .test_dragons import _finished_attempt


def test_discoveries_need_sign_in(client: TestClient) -> None:
    assert client.get("/api/v1/discoveries").status_code == 401


def test_the_three_in_the_reveal_are_discovered(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    assert quiz_client.get("/api/v1/discoveries", headers=headers).json() == []

    attempt_id = _finished_attempt(quiz_client, headers)
    match = quiz_client.get(f"/api/v1/quiz/attempts/{attempt_id}", headers=headers).json()["match"]
    met = {d["species_id"] for d in [match["top"], *match["runners_up"]]}

    found = quiz_client.get("/api/v1/discoveries", headers=headers).json()
    assert {d["entity_id"] for d in found} == met
    assert all(d["entity_kind"] == "species" and d["via"] == "quiz" for d in found)


def test_meeting_a_dragon_again_keeps_the_first_date(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    headers = auth_headers(make_token, player)
    _finished_attempt(quiz_client, headers)
    first = quiz_client.get("/api/v1/discoveries", headers=headers).json()

    _finished_attempt(quiz_client, headers)  # same answers, so the same three dragons
    assert quiz_client.get("/api/v1/discoveries", headers=headers).json() == first
