from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import require_active_user_id
from app.core.dependencies import user_service
from app.repositories.user_account_repository import UserIdentityConflictError
from app.schemas.user_account import UserAccount, UserAccountUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserAccount)
def get_current_user(user_id: Annotated[str, Depends(require_active_user_id)]) -> UserAccount:
    user = user_service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User is not initialized.")

    return user


@router.put("/me", response_model=UserAccount)
def update_current_user(
    payload: UserAccountUpdateRequest,
    user_id: Annotated[str, Depends(require_active_user_id)],
) -> UserAccount:
    try:
        return user_service.update_user(user_id, payload)
    except LookupError as error:
        raise HTTPException(status_code=404, detail="User is not initialized.") from error
    except UserIdentityConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
