from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import require_active_user_id
from app.core.dependencies import user_service
from app.schemas.user_account import (
    LoginAvailabilityResponse,
    UserAccount,
    UserAccountSignInRequest,
    UserAccountUpdateRequest,
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/login-availability", response_model=LoginAvailabilityResponse)
def check_login_availability(
    login: str = Query(min_length=3, max_length=64),
    email: str | None = Query(default=None, min_length=5, max_length=255),
) -> LoginAvailabilityResponse:
    return user_service.check_login_availability(login, email)


@router.post("/sign-in", response_model=UserAccount)
def sign_in(payload: UserAccountSignInRequest) -> UserAccount:
    return user_service.sign_in(payload)


@router.get("/me", response_model=UserAccount)
def get_current_user(user_id: Annotated[str, Depends(require_active_user_id)]) -> UserAccount:
    return user_service.get_user(user_id)


@router.put("/me", response_model=UserAccount)
def update_current_user(
    payload: UserAccountUpdateRequest,
    user_id: Annotated[str, Depends(require_active_user_id)],
) -> UserAccount:
    return user_service.update_user(user_id, payload)
