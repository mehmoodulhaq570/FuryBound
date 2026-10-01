from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.config import Settings, get_settings
from app.db.session import create_engine, create_sessionmaker
from app.log import configure_logging, request_logging_middleware
from app.routers import canon, health, me, quiz

API_PREFIX = "/api/v1"


def _operation_id(route: APIRoute) -> str:
    # Stable, readable operation IDs in the OpenAPI schema (and generated TS types).
    return route.name


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json=settings.app_env == "production")

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        # Connections open lazily, so the app starts even if the database is down;
        # /health keeps working and database routes fail until it's back.
        engine = create_engine(settings.database_url)
        app.state.sessionmaker = create_sessionmaker(engine)
        yield
        await engine.dispose()

    app = FastAPI(
        lifespan=lifespan,
        title="Dragon Academy API",
        version="0.1.0",
        openapi_url=f"{API_PREFIX}/openapi.json",
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=None,
        generate_unique_id_function=_operation_id,
    )

    app.middleware("http")(request_logging_middleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["Authorization", "Content-Type"],
        expose_headers=["x-request-id"],
    )

    api = APIRouter(prefix=API_PREFIX)
    api.include_router(health.router)
    api.include_router(me.router)
    api.include_router(canon.router)
    api.include_router(quiz.router)
    app.include_router(api)

    return app


app = create_app()
