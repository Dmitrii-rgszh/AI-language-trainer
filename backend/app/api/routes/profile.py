from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_active_user_id
from app.core.dependencies import profile_service
from app.schemas.profile import ProfileUpdateRequest, UserProfile

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=UserProfile)
def get_profile(user_id: Annotated[str, Depends(require_active_user_id)]) -> UserProfile:
    profile = profile_service.get_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile is not initialized.")
    profile_service.ensure_runtime(profile)
    return profile


@router.put("", response_model=UserProfile)
def update_profile(
    payload: ProfileUpdateRequest,
    user_id: Annotated[str, Depends(require_active_user_id)],
) -> UserProfile:
    return profile_service.update_profile(user_id, payload)
