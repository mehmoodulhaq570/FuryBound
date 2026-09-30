from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["meta"])


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse()
