from fastapi import APIRouter

from app.api.dependencies import require_profile
from app.core.dependencies import provider_service
from app.schemas.provider import (
    ProviderPreference,
    ProviderPreferenceUpdateRequest,
    ProviderStatus,
    ProviderType,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("/status", response_model=list[ProviderStatus])
def get_provider_statuses() -> list[ProviderStatus]:
    return provider_service.get_statuses()


@router.get("/preferences", response_model=list[ProviderPreference])
def get_provider_preferences() -> list[ProviderPreference]:
    return provider_service.list_preferences(require_profile().id)


@router.put("/preferences/{provider_type}", response_model=ProviderPreference)
def update_provider_preference(
    provider_type: ProviderType,
    payload: ProviderPreferenceUpdateRequest,
) -> ProviderPreference:
    return provider_service.update_preference(require_profile().id, provider_type, payload)
