from fastapi import APIRouter

from app.auth import AUTH_RESPONSES, AuthenticatedUser, CurrentUser

router = APIRouter(tags=["account"], responses=AUTH_RESPONSES)


@router.get("/me")
async def read_me(user: AuthenticatedUser) -> CurrentUser:
    """The signed-in user, as seen by the API. Used to check the auth round trip."""
    return user
