from app.repositories.user_account_repository import UserAccountRepository
from app.schemas.user_account import LoginAvailabilityResponse, UserAccount, UserAccountUpdateRequest


class UserService:
    def __init__(self, repository: UserAccountRepository) -> None:
        self._repository = repository

    def get_user(self, user_id: str) -> UserAccount | None:
        return self._repository.get_user(user_id)

    def check_login_availability(self, login: str, email: str | None = None) -> LoginAvailabilityResponse:
        return self._repository.check_login_availability(login, email)

    def update_user(self, user_id: str, payload: UserAccountUpdateRequest) -> UserAccount:
        return self._repository.update_user(user_id, payload)
