from functools import lru_cache
from typing import Annotated, Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: Literal["local", "test", "production"] = "local"
    log_level: str = "INFO"

    # Comma-separated in the environment, e.g. "http://localhost:3000,https://example.com"
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    # Supabase. Defaults match `supabase start`.
    supabase_url: str = "http://127.0.0.1:54321"
    # Only needed if the project still signs tokens with the legacy HS256 shared secret.
    # Asymmetric keys (ES256/RS256) are verified against the project's JWKS instead.
    supabase_jwt_secret: str | None = None
    supabase_jwt_audience: str = "authenticated"

    # Used from Phase 1 onwards.
    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:54322/postgres"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def supabase_issuer(self) -> str:
        return f"{self.supabase_url.rstrip('/')}/auth/v1"

    @property
    def supabase_jwks_url(self) -> str:
        return f"{self.supabase_issuer}/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
