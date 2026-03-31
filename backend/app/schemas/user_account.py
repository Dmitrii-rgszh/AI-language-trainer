from pydantic import Field

from .base import ApiModel


class UserAccount(ApiModel):
    id: str
    login: str
    email: str
    created_at: str
    updated_at: str


class UserAccountUpdateRequest(ApiModel):
    login: str = Field(min_length=3, max_length=64)
    email: str = Field(min_length=5, max_length=255)


class LoginAvailabilityResponse(ApiModel):
    login: str
    normalized_login: str
    available: bool
    status: str
    suggestions: list[str] = Field(default_factory=list)
