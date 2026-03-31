from fastapi import HTTPException

from app.core.dependencies import profile_service
from app.schemas.profile import UserProfile


def require_profile() -> UserProfile:
    profile = profile_service.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile is not initialized.")

    return profile
