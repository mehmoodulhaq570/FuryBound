"""Persistent mission rewards, ownership and unlocks against the seeded database."""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from typing import Any
from uuid import UUID, uuid4

from fastapi.testclient import TestClient

from .conftest import MakeToken, _rows, _sql, auth_headers
from .test_dragons import _adopted
from .test_training_api import _backdate


def _choice(
    client: TestClient, headers: dict[str, str], dragon_id: str, run_id: str, choice: str
) -> Any:
    return client.post(
        f"/api/v1/dragons/{dragon_id}/adventure/{run_id}/choice",
        headers=headers,
        json={"choice": choice},
    )


def _complete(client: TestClient, headers: dict[str, str], session_id: str, url: str) -> None:
    _backdate(url, session_id, 25)
    response = client.post(
        f"/api/v1/training-sessions/{session_id}/complete",
        headers=headers,
        json={"score": 85, "duration_ms": 22000},
    )
    assert response.status_code == 200, response.text


def test_experience_needs_auth(client: TestClient) -> None:
    assert client.get(f"/api/v1/dragons/{uuid4()}/experience").status_code == 401


def test_unlocks_are_earned_and_decoration_survives_reload(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    root = f"/api/v1/dragons/{dragon['id']}"
    before = quiz_client.get(f"{root}/experience", headers=headers).json()
    assert not any(a["earned"] for a in before["achievements"])
    assert before["milestone"]["level"] == 5
    assert before["journal"][0]["text"].endswith("began your story together.")
    assert (
        quiz_client.post(
            f"{root}/decoration", headers=headers, json={"decoration": "beacon"}
        ).status_code
        == 409
    )
    sess = quiz_client.post(
        f"{root}/training-sessions", headers=headers, json={"activity": "flight"}
    ).json()["id"]
    _complete(quiz_client, headers, sess, database_url)
    after = quiz_client.get(f"{root}/experience", headers=headers).json()
    badges = {a["id"]: a for a in after["achievements"]}
    assert badges["first_flight"]["earned"] and badges["ace"]["earned"]
    assert after["milestone"]["xp_remaining"] < before["milestone"]["xp_remaining"]
    assert (
        quiz_client.post(
            f"{root}/decoration", headers=headers, json={"decoration": "pennant"}
        ).status_code
        == 200
    )
    assert quiz_client.get(f"{root}/experience", headers=headers).json()["decoration"] == "pennant"


def test_rescue_resumes_requires_its_flight_and_rewards_once(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    root = f"/api/v1/dragons/{dragon['id']}"
    run = quiz_client.post(f"{root}/adventure", headers=headers).json()
    assert quiz_client.post(f"{root}/adventure", headers=headers).json()["id"] == run["id"]
    # An out-of-order choice cannot jump directly to rewards.
    assert _choice(quiz_client, headers, dragon["id"], run["id"], "lift").status_code == 409
    flight = _choice(quiz_client, headers, dragon["id"], run["id"], "gentle").json()
    assert flight["node"] == "flight" and flight["training_session_id"]
    assert _choice(quiz_client, headers, dragon["id"], run["id"], "untie").status_code == 409
    # Completing unrelated training doesn't unlock the mission's rescue node.
    other = quiz_client.post(
        f"{root}/training-sessions", headers=headers, json={"activity": "speed"}
    ).json()["id"]
    _complete(quiz_client, headers, other, database_url)
    not_ready = _choice(quiz_client, headers, dragon["id"], run["id"], "continue").json()
    assert not_ready["node"] == "flight" and not not_ready["flight_finished"]
    _complete(quiz_client, headers, flight["training_session_id"], database_url)
    assert quiz_client.get(f"{root}/experience", headers=headers).json()["adventure"][
        "flight_finished"
    ]
    rescued = _choice(quiz_client, headers, dragon["id"], run["id"], "continue")
    assert rescued.json()["node"] == "rescue"
    done = _choice(quiz_client, headers, dragon["id"], run["id"], "untie")
    assert done.status_code == 200, done.text
    assert done.json()["node"] == "complete" and done.json()["xp_reward"] == 80
    current = quiz_client.get("/api/v1/dragons/me", headers=headers).json()
    assert _choice(quiz_client, headers, dragon["id"], run["id"], "untie").status_code == 409
    resumed = quiz_client.post(f"{root}/adventure", headers=headers).json()
    assert resumed["node"] == "complete"
    same = quiz_client.get("/api/v1/dragons/me", headers=headers).json()
    assert (same["level"], same["xp"], same["trust"]) == (
        current["level"],
        current["xp"],
        current["trust"],
    )
    exp = quiz_client.get(f"{root}/experience", headers=headers).json()
    assert any(a["id"] == "rescue" and a["earned"] for a in exp["achievements"])
    assert any("Scuttleclaw" in e["text"] for e in exp["journal"])
    discoveries = quiz_client.get("/api/v1/discoveries", headers=headers).json()
    assert any(d["entity_id"] == "scuttleclaw" for d in discoveries)


def test_expired_mission_flight_gets_a_fresh_session(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    run = quiz_client.post(f"/api/v1/dragons/{dragon['id']}/adventure", headers=headers).json()
    flight = _choice(quiz_client, headers, dragon["id"], run["id"], "clever").json()
    _backdate(database_url, flight["training_session_id"], 31 * 60)
    fresh = _choice(quiz_client, headers, dragon["id"], run["id"], "continue").json()
    assert fresh["training_session_id"] != flight["training_session_id"]
    assert fresh["node"] == "flight" and not fresh["flight_finished"]


def test_other_players_cannot_read_choose_or_decorate(
    quiz_client: TestClient, make_token: MakeToken, player: UUID
) -> None:
    owner = auth_headers(make_token, player)
    other = auth_headers(make_token, uuid4())
    dragon = _adopted(quiz_client, owner)
    root = f"/api/v1/dragons/{dragon['id']}"
    run = quiz_client.post(f"{root}/adventure", headers=owner).json()
    assert quiz_client.get(f"{root}/experience", headers=other).status_code == 404
    assert quiz_client.post(f"{root}/adventure", headers=other).status_code == 404
    assert _choice(quiz_client, other, dragon["id"], run["id"], "bold").status_code == 404
    assert (
        quiz_client.post(
            f"{root}/decoration", headers=other, json={"decoration": "camp"}
        ).status_code
        == 404
    )


def test_exhausted_dragon_keeps_mission_at_approach(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    root = f"/api/v1/dragons/{dragon['id']}"
    run = quiz_client.post(f"{root}/adventure", headers=headers).json()
    asyncio.run(
        _sql(
            database_url,
            'update player_dragons set needs = \'{"hunger": 30,"energy": 0,"happiness": 60}\','
            " needs_updated_at = now() where id = :id",
            id=dragon["id"],
        )
    )
    assert _choice(quiz_client, headers, dragon["id"], run["id"], "bold").status_code == 409
    assert (
        quiz_client.get(f"{root}/experience", headers=headers).json()["adventure"]["node"]
        == "approach"
    )


def test_island_collection_resumes_and_concurrent_reward_is_once(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    dragon = _adopted(quiz_client, headers)
    root = f"/api/v1/dragons/{dragon['id']}"
    assert quiz_client.get(f"{root}/island", headers=headers).json()["treasures"] == []
    for treasure in ["shell", "ribbon"]:
        assert quiz_client.post(f"{root}/treasures/{treasure}", headers=headers).status_code == 200
    asyncio.run(
        _sql(database_url, "update player_dragons set xp = 90 where id = :id", id=dragon["id"])
    )
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(
            pool.map(
                lambda _: quiz_client.post(f"{root}/treasures/scale", headers=headers), range(2)
            )
        )
    assert all(r.status_code == 200 for r in responses)
    state = quiz_client.get(f"{root}/island", headers=headers).json()
    assert state["treasures"] == ["ribbon", "scale", "shell"]
    assert state["lookout_unlocked"] and state["xp_reward"] == 40
    current = quiz_client.get("/api/v1/dragons/me", headers=headers).json()
    assert (current["level"], current["xp"]) == (2, 30)
    assert asyncio.run(
        _rows(
            database_url,
            "select count(*) from dragon_events where dragon_id = :id and kind = 'island_explored'",
            id=dragon["id"],
        )
    ) == [1]
    journal = quiz_client.get(f"{root}/experience", headers=headers).json()["journal"]
    assert any("hilltop lookout" in entry["text"] for entry in journal)


def test_island_layout_ownership_validation_and_persistence(
    quiz_client: TestClient, make_token: MakeToken, player: UUID, database_url: str
) -> None:
    headers = auth_headers(make_token, player)
    other = auth_headers(make_token, uuid4())
    dragon = _adopted(quiz_client, headers)
    root = f"/api/v1/dragons/{dragon['id']}"
    for path in ["island", "treasures/shell", "habitat-layout"]:
        request = quiz_client.get if path == "island" else quiz_client.post
        body: dict[str, Any] = {} if path != "habitat-layout" else {"json": {"positions": {}}}
        assert request(f"{root}/{path}", headers=other, **body).status_code == 404
        assert request(f"{root}/{path}", **body).status_code == 401
    assert quiz_client.post(f"{root}/treasures/invented", headers=headers).status_code == 409
    layout = {"positions": {"lanterns": {"x": 18, "y": 65}}}
    assert (
        quiz_client.post(f"{root}/habitat-layout", headers=headers, json=layout).status_code == 409
    )
    training = quiz_client.post(
        f"{root}/training-sessions", headers=headers, json={"activity": "flight"}
    ).json()
    _complete(quiz_client, headers, training["id"], database_url)
    assert (
        quiz_client.post(f"{root}/habitat-layout", headers=headers, json=layout).status_code == 200
    )
    assert quiz_client.get(f"{root}/island", headers=headers).json()["layout"] == layout
    for invalid in [
        {"positions": {"lanterns": {"x": 999, "y": 65}}},
        {"positions": {"unknown": {"x": 18, "y": 65}}},
    ]:
        assert (
            quiz_client.post(f"{root}/habitat-layout", headers=headers, json=invalid).status_code
            == 422
        )
