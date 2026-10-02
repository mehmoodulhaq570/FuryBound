"""The signed-in player's discoveries (Plan.md §9.1, §10)."""

from fastapi import APIRouter

from app import discoveries
from app.auth import AUTH_RESPONSES, AuthenticatedUser
from app.db.session import DbSession
from app.schemas.discoveries import Discovery

router = APIRouter(tags=["dragon book"], responses=AUTH_RESPONSES)


@router.get("/discoveries")
async def my_discoveries(user: AuthenticatedUser, session: DbSession) -> list[Discovery]:
    """Every dragon the player has met, oldest first. Named dragons follow their species."""
    return await discoveries.list_for(session, user.id)
