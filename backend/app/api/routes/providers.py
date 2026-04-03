from fastapi import APIRouter, Depends

from app.api.dependencies import require_profile
from app.core.dependencies import provider_service
from app.schemas.provider import (
    ProviderPreference,
    ProviderPreferenceUpdateRequest,
    ProviderStatus,
    ProviderType,
)
from app.schemas.profile import UserProfile

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/status", response_model=list[ProviderStatus])
def get_provider_statuses() -> list[ProviderStatus]:
    return provider_service.get_statuses()


@router.get("/preferences", response_model=list[ProviderPreference])
def get_provider_preferences(profile: UserProfile = Depends(require_profile)) -> list[ProviderPreference]:
    return provider_service.list_preferences(profile.id)


@router.put("/preferences/{provider_type}", response_model=ProviderPreference)
def update_provider_preference(
    provider_type: ProviderType,
    payload: ProviderPreferenceUpdateRequest,
    profile: UserProfile = Depends(require_profile),
) -> ProviderPreference:
    return provider_service.update_preference(profile.id, provider_type, payload)
