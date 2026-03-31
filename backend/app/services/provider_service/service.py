from __future__ import annotations

from fastapi import HTTPException

from app.providers.registry import ProviderRegistry
from app.repositories.provider_preference_repository import ProviderPreferenceRepository
from app.schemas.provider import ProviderPreference, ProviderPreferenceUpdateRequest, ProviderStatus, ProviderType


class ProviderService:
    def __init__(self, repository: ProviderPreferenceRepository, registry: ProviderRegistry) -> None:
        self._repository = repository
        self._registry = registry

    def get_statuses(self) -> list[ProviderStatus]:
        return self._registry.get_statuses()

    def list_preferences(self, user_id: str) -> list[ProviderPreference]:
        statuses = self._registry.get_statuses()
        stored_preferences = {
            preference.provider_type: preference
            for preference in self._repository.list_preferences(user_id)
        }

        preferences: list[ProviderPreference] = []
        for status in statuses:
            preference = stored_preferences.get(status.type.value)
            if preference:
                preferences.append(preference)
                continue

            preferences.append(
                ProviderPreference(
                    provider_type=status.type,
                    selected_provider=status.key,
                    enabled=status.status != "offline",
                    settings={},
                )
            )

        return preferences

    def update_preference(
        self,
        user_id: str,
        provider_type: ProviderType,
        payload: ProviderPreferenceUpdateRequest,
    ) -> ProviderPreference:
        allowed_provider_keys = {status.key for status in self._registry.get_statuses() if status.type == provider_type}
        if payload.selected_provider not in allowed_provider_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown provider '{payload.selected_provider}' for type '{provider_type.value}'.",
            )

        return self._repository.upsert_preference(user_id, provider_type, payload)
