import time
from collections.abc import Callable, Iterator
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient

from app.auth import TokenVerifier, get_token_verifier
from app.config import Settings
from app.main import create_app

ISSUER = "http://supabase.test/auth/v1"
AUDIENCE = "authenticated"
HS_SECRET = "test-secret-that-is-at-least-32-bytes-long"


class StaticJWKS:
    """Stands in for PyJWKClient: always returns the same public key."""

    def __init__(self, public_key: Any) -> None:
        self._key = jwt.PyJWK.from_dict(
            {**jwt.algorithms.ECAlgorithm.to_jwk(public_key, as_dict=True), "alg": "ES256"}
        )

    def get_signing_key_from_jwt(self, token: str) -> jwt.PyJWK:
        return self._key


@pytest.fixture(scope="session")
def ec_private_key() -> ec.EllipticCurvePrivateKey:
    return ec.generate_private_key(ec.SECP256R1())


@pytest.fixture
def verifier(ec_private_key: ec.EllipticCurvePrivateKey) -> TokenVerifier:
    return TokenVerifier(
        issuer=ISSUER,
        audience=AUDIENCE,
        jwks=StaticJWKS(ec_private_key.public_key()),
        jwt_secret=HS_SECRET,
    )


@pytest.fixture
def client(verifier: TokenVerifier) -> Iterator[TestClient]:
    app = create_app(Settings(app_env="test"))
    app.dependency_overrides[get_token_verifier] = lambda: verifier
    with TestClient(app) as test_client:
        yield test_client


MakeToken = Callable[..., str]


@pytest.fixture
def make_token(ec_private_key: ec.EllipticCurvePrivateKey) -> MakeToken:
    def _make(
        *,
        sub: UUID | None = None,
        alg: str = "ES256",
        expires_in: int = 3600,
        **overrides: Any,
    ) -> str:
        now = int(time.time())
        claims: dict[str, Any] = {
            "sub": str(sub or uuid4()),
            "email": "hiccup@berk.test",
            "role": "authenticated",
            "aud": AUDIENCE,
            "iss": ISSUER,
            "iat": now,
            "exp": now + expires_in,
            **overrides,
        }
        key: Any = HS_SECRET if alg == "HS256" else ec_private_key
        return jwt.encode(claims, key, algorithm=alg)

    return _make
