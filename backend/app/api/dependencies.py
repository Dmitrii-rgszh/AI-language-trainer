from typing import Annotated

from fastapi import Depends, Header, HTTPException

from app.core.dependencies import profile_service
from app.schemas.profile import UserProfile


def require_active_user_id(x_user_id: Annotated[str | None, Header(alias="X-User-Id")] = None) -> str:
    if not x_user_id:
        raise HTTPException(status_code=404, detail="Active user is not selected.")

    return x_user_id


def require_profile(user_id: Annotated[str, Depends(require_active_user_id)]) -> UserProfile:
    profile = profile_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile is not initialized.")

    return profile
