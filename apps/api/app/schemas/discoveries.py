"""Response models for discoveries (Plan.md §9.1)."""

from datetime import datetime

from pydantic import BaseModel, Field


class Discovery(BaseModel):
    entity_kind: str = Field(examples=["species"])
    entity_id: str = Field(examples=["deadly_nadder"])
    via: str = Field(examples=["quiz"], description="How the player met it")
    discovered_at: datetime
