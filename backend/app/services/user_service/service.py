from app.core.errors import ConflictError, NotFoundError
from app.repositories.user_account_repository import UserAccountRepository, UserIdentityConflictError
from app.schemas.user_account import LoginAvailabilityResponse, UserAccount, UserAccountUpdateRequest


class UserService:
    def __init__(self, repository: UserAccountRepository) -> None:
        self._repository = repository

    def get_user(self, user_id: str) -> UserAccount:
        user = self._repository.get_user(user_id)
        if not user:
            raise NotFoundError("User is not initialized.")

        return user

    def check_login_availability(self, login: str, email: str | None = None) -> LoginAvailabilityResponse:
        return self._repository.check_login_availability(login, email)

    def update_user(self, user_id: str, payload: UserAccountUpdateRequest) -> UserAccount:
        try:
            return self._repository.update_user(user_id, payload)
        except LookupError as error:
            raise NotFoundError("User is not initialized.") from error
        except UserIdentityConflictError as error:
            raise ConflictError(str(error)) from error
