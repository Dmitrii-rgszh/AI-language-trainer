from app.core.errors import ConflictError, NotFoundError
from app.repositories.user_account_repository import (
    UserAccountRepository,
    UserAuthenticationError,
    UserIdentityConflictError,
)
from app.schemas.user_account import (
    LoginAvailabilityResponse,
    UserAccount,
    UserAccountSignInRequest,
    UserAccountUpdateRequest,
)


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

    def sign_in(self, payload: UserAccountSignInRequest) -> UserAccount:
        try:
            return self._repository.sign_in(payload.login, payload.email)
        except UserAuthenticationError as error:
            raise NotFoundError("Account not found for this login and email.") from error

    def update_user(self, user_id: str, payload: UserAccountUpdateRequest) -> UserAccount:
        try:
            return self._repository.update_user(user_id, payload)
        except LookupError as error:
            raise NotFoundError("User is not initialized.") from error
        except UserIdentityConflictError as error:
            raise ConflictError(str(error)) from error
