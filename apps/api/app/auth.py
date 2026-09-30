"""Supabase JWT verification.

The browser signs in with Supabase Auth and sends the access token as
`Authorization: Bearer <jwt>`. We verify it locally: asymmetric tokens against the
project's JWKS (cached), legacy HS256 tokens against the shared secret if configured.
"""

from functools import lru_cache
from typing import Annotated, Any, Protocol
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

from app.config import get_settings

ASYMMETRIC_ALGORITHMS = ["ES256", "RS256", "EdDSA"]


class CurrentUser(BaseModel):
    id: UUID
    email: str | None = None
    role: str


class ErrorResponse(BaseModel):
    detail: str


# Add to protected routes (`responses=AUTH_RESPONSES`) so the 401 shows up in the
# OpenAPI schema and the generated frontend types.
AUTH_RESPONSES: dict[int | str, dict[str, Any]] = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": ErrorResponse,
        "description": "Missing or invalid token",
    }
}


class SigningKeySource(Protocol):
    def get_signing_key_from_jwt(self, token: str) -> Any: ...


class InvalidToken(Exception):
    pass


class TokenVerifier:
    def __init__(
        self,
        *,
        issuer: str,
        audience: str,
        jwks: SigningKeySource,
        jwt_secret: str | None = None,
    ) -> None:
        self._issuer = issuer
        self._audience = audience
        self._jwks = jwks
        self._jwt_secret = jwt_secret

    def verify(self, token: str) -> CurrentUser:
        try:
            alg = jwt.get_unverified_header(token).get("alg")
            if alg == "HS256":
                if not self._jwt_secret:
                    raise InvalidToken("HS256 tokens are not accepted without a JWT secret")
                key: Any = self._jwt_secret
                algorithms = ["HS256"]
            elif alg in ASYMMETRIC_ALGORITHMS:
                key = self._jwks.get_signing_key_from_jwt(token).key
                algorithms = ASYMMETRIC_ALGORITHMS
            else:
                raise InvalidToken(f"Unsupported algorithm: {alg}")

            claims = jwt.decode(
                token,
                key,
                algorithms=algorithms,
                audience=self._audience,
                issuer=self._issuer,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
        except jwt.PyJWTError as exc:
            raise InvalidToken(str(exc)) from exc

        try:
            return CurrentUser(id=claims["sub"], email=claims.get("email"), role=claims["role"])
        except (KeyError, ValueError) as exc:
            raise InvalidToken("Token is missing required user claims") from exc


@lru_cache
def get_token_verifier() -> TokenVerifier:
    settings = get_settings()
    return TokenVerifier(
        issuer=settings.supabase_issuer,
        audience=settings.supabase_jwt_audience,
        jwks=jwt.PyJWKClient(settings.supabase_jwks_url, cache_keys=True, lifespan=600),
        jwt_secret=settings.supabase_jwt_secret,
    )


_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    verifier: Annotated[TokenVerifier, Depends(get_token_verifier)],
) -> CurrentUser:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        # The JWKS lookup may do blocking network I/O on a cache miss.
        return await run_in_threadpool(verifier.verify, credentials.credentials)
    except InvalidToken as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


AuthenticatedUser = Annotated[CurrentUser, Depends(get_current_user)]
