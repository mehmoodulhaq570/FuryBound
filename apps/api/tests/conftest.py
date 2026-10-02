import asyncio
import json
import os
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.auth import TokenVerifier, get_token_verifier
from app.config import Settings
from app.db.session import create_engine
from app.engines.game_data import get_game_data
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


DRAGONS_JSON = Path(__file__).resolve().parents[3] / "data" / "build" / "dragons.json"


def _database_ready(url: str) -> str | None:
    """None if the seeded database answers, else the reason it doesn't."""

    async def probe() -> None:
        engine = create_engine(url)
        try:
            async with engine.connect() as conn:
                await conn.execute(text("select 1 from species limit 1"))
        finally:
            await engine.dispose()

    try:
        asyncio.run(asyncio.wait_for(probe(), timeout=5))
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    return None


@pytest.fixture(scope="session")
def database_url() -> str:
    """The local Supabase database, seeded from the catalog (`pnpm db:start`).

    Skips database tests when it isn't running, except on CI (where CI=true),
    so they can't be silently skipped there.
    """
    url = Settings().database_url
    problem = _database_ready(url)
    if problem:
        message = f"Seeded database not reachable ({problem}). Run `pnpm db:start`."
        if os.environ.get("CI"):
            pytest.fail(message)
        pytest.skip(message)
    return url


@pytest.fixture
def db_client(database_url: str) -> Iterator[TestClient]:
    app = create_app(Settings(app_env="test", database_url=database_url))
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="session")
def catalog() -> list[dict[str, Any]]:
    """The build output the database was seeded from."""
    entries: list[dict[str, Any]] = json.loads(DRAGONS_JSON.read_text(encoding="utf-8"))
    return entries


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


def auth_headers(make_token: MakeToken, user_id: UUID) -> dict[str, str]:
    return {"Authorization": f"Bearer {make_token(sub=user_id)}"}


def first_answers() -> dict[str, str]:
    """A complete, valid set of quiz answers."""
    return {q.id: q.options[0].id for q in get_game_data().quiz.questions}


async def _sql(url: str, statement: str, **params: object) -> None:
    engine = create_engine(url)
    try:
        async with engine.begin() as conn:
            await conn.execute(text(statement), params)
    finally:
        await engine.dispose()


async def _rows(url: str, statement: str, **params: object) -> list[Any]:
    """The first column of every row a query returns."""
    engine = create_engine(url)
    try:
        async with engine.connect() as conn:
            return list((await conn.execute(text(statement), params)).scalars())
    finally:
        await engine.dispose()


@pytest.fixture
def player(database_url: str) -> Iterator[UUID]:
    """A throwaway account (its profile comes from a trigger); deleted with all its data."""
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
