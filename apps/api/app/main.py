from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.routing import APIRoute

from app.config import Settings, get_settings
from app.log import configure_logging, request_logging_middleware
from app.routers import health, me

API_PREFIX = "/api/v1"


def _operation_id(route: APIRoute) -> str:
    # Stable, readable operation IDs in the OpenAPI schema (and generated TS types).
    return route.name


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(level=settings.log_level, json=settings.app_env == "production")

    app = FastAPI(
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
    app.include_router(api)

    return app


app = create_app()
