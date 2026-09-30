from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient

from tests.conftest import MakeToken


def _get_me(client: TestClient, token: str) -> tuple[int, dict[str, object]]:
    response = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    return response.status_code, response.json()


@pytest.mark.parametrize("alg", ["ES256", "HS256"])
def test_valid_token_returns_user(client: TestClient, make_token: MakeToken, alg: str) -> None:
    user_id = uuid4()

    status, body = _get_me(client, make_token(sub=user_id, alg=alg))

    assert status == 200
    assert body == {"id": str(user_id), "email": "hiccup@berk.test", "role": "authenticated"}


def test_missing_token_is_rejected(client: TestClient) -> None:
    response = client.get("/api/v1/me")

    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize(
    "overrides",
    [
        pytest.param({"expires_in": -60}, id="expired"),
        pytest.param({"aud": "anon"}, id="wrong-audience"),
        pytest.param({"iss": "http://evil.test/auth/v1"}, id="wrong-issuer"),
        pytest.param({"sub": "not-a-uuid"}, id="bad-subject"),
    ],
)
def test_bad_claims_are_rejected(
    client: TestClient, make_token: MakeToken, overrides: dict[str, object]
) -> None:
    status, _ = _get_me(client, make_token(**overrides))

    assert status == 401


def test_tampered_token_is_rejected(client: TestClient, make_token: MakeToken) -> None:
    header, payload, signature = make_token().split(".")
    tampered = f"{header}.{payload}.{signature[:-4]}AAAA"

    status, _ = _get_me(client, tampered)

    assert status == 401


def test_unsigned_token_is_rejected(client: TestClient) -> None:
    token = jwt.encode({"sub": str(uuid4()), "role": "authenticated"}, key="", algorithm="none")

    status, _ = _get_me(client, token)

    assert status == 401


def test_garbage_token_is_rejected(client: TestClient) -> None:
    status, _ = _get_me(client, "not.a.jwt")

    assert status == 401
