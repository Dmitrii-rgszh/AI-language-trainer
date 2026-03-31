from fastapi import APIRouter, HTTPException

from app.core.dependencies import profile_service
from app.schemas.profile import ProfileUpdateRequest, UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserProfile)
def get_profile() -> UserProfile:
    profile = profile_service.get_profile()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile is not initialized.")
    profile_service.ensure_runtime(profile)
    return profile


@router.put("", response_model=UserProfile)
def update_profile(payload: ProfileUpdateRequest) -> UserProfile:
    return profile_service.update_profile(payload)
