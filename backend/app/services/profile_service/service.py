from app.repositories.profile_repository import ProfileRepository
from app.schemas.profile import ProfileUpdateRequest, UserProfile


class ProfileService:
    def __init__(self, repository: ProfileRepository, bootstrap_service=None) -> None:
        self._repository = repository
        self._bootstrap_service = bootstrap_service

    def get_profile(self) -> UserProfile | None:
        return self._repository.get_profile()

    def update_profile(self, payload: ProfileUpdateRequest) -> UserProfile:
        profile = self._repository.update_profile(payload)
        self.ensure_runtime(profile)
        return profile

    def ensure_runtime(self, profile: UserProfile) -> None:
        if self._bootstrap_service is None:
            return
        self._bootstrap_service.sync_profile_runtime(profile)
