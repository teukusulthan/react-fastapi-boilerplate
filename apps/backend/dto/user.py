"""User DTOs.

Inputs are strict (``extra="forbid"``): unknown or privileged fields are rejected
with 422 instead of being silently mass-assigned. ``Update*`` DTOs have only
optional fields and are applied with PATCH semantics: only the fields present in
the request body (``model_fields_set`` -> ``to_storage(exclude_unset=True)``)
change; an explicit ``null`` clears a nullable field and is rejected (422) for
required columns.

Responses reuse the foundation read models (``dto.user_profile``), which never
contain ``password_hash`` / ``two_factor_secret``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import ConfigDict, EmailStr, Field, StringConstraints, field_validator

from dto.common import BaseSchema, FindDTO
from dto.user_profile import UserProfile, UserResponse

__all__ = [
    "CheckAvailabilityResponse",
    "CreateUserDTO",
    "FindUserDTO",
    "ResetPasswordDTO",
    "UpdateProfileDTO",
    "UpdateUserDTO",
    "UserProfile",
    "UserResponse",
    "UserStatus",
]

UserStatus = Literal["pending", "active", "blocked", "deleted"]

Username = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=50, pattern=r"^[A-Za-z0-9._-]+$"),
]
Fullname = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Phone = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^\+?[0-9]{6,20}$")]
# Policy (min length) is enforced by the service with BE_PASSWORD_MIN_LENGTH; 72 bytes is bcrypt's limit.
Password = Annotated[str, StringConstraints(min_length=1, max_length=72)]
EntityId = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
About = Annotated[str, StringConstraints(max_length=1000)]
ImageRef = Annotated[str, StringConstraints(strip_whitespace=True, max_length=2048)]
JsonObject = dict[str, Any]

STRICT = ConfigDict(extra="forbid")


def _normalize_email(value: Any) -> Any:
    return value.strip().lower() if isinstance(value, str) else value


def _not_null(value: Any) -> Any:
    # Field validators only run for values the client sent, so this rejects an explicit ``null``.
    if value is None:
        raise ValueError("cannot be null")
    return value


# ------------------------------------------------------------------ admin
class CreateUserDTO(BaseSchema):
    """``POST /user/add`` (admin)."""

    model_config = STRICT

    username: Username
    fullname: Fullname
    email: EmailStr
    phone: Phone | None = None
    password: Password | None = Field(
        default=None, description="Required with BE_AUTH_PROVIDER=local; not accepted with supabase"
    )
    permission_id: EntityId | None = None
    group_id: EntityId | None = None
    status: UserStatus = "active"
    email_verified: bool = False
    multi_login: bool = True
    expired_at: datetime | None = None
    about: About | None = None
    image: ImageRef | None = None
    settings: JsonObject | None = None
    personalization: JsonObject | None = None
    additional: JsonObject | None = None

    _email = field_validator("email", mode="before")(_normalize_email)


class UpdateUserDTO(BaseSchema):
    """``PUT /user/update`` (admin). PATCH semantics; passwords change via ``/user/reset-password``."""

    model_config = STRICT

    id: EntityId
    username: Username | None = None
    fullname: Fullname | None = None
    email: EmailStr | None = None
    phone: Phone | None = None
    permission_id: EntityId | None = None
    group_id: EntityId | None = None
    status: UserStatus | None = None
    email_verified: bool | None = None
    multi_login: bool | None = None
    expired_at: datetime | None = None
    about: About | None = None
    image: ImageRef | None = None
    settings: JsonObject | None = None
    personalization: JsonObject | None = None
    additional: JsonObject | None = None

    _email = field_validator("email", mode="before")(_normalize_email)
    _required = field_validator("username", "email", "status", "email_verified", "multi_login")(_not_null)


class ResetPasswordDTO(BaseSchema):
    """``POST /user/reset-password`` (admin): set a new password and revoke the user's sessions."""

    model_config = STRICT

    id: EntityId
    new_password: Password


class FindUserDTO(FindDTO):
    """``POST /user/get-all`` body (whitelists: ``db.schema.USERS``)."""


class CheckAvailabilityResponse(BaseSchema):
    """``GET /user/check-{email,username,phone}``: ``exists`` = already taken."""

    field: str
    exists: bool
    available: bool


# --------------------------------------------------------------- self-service
class UpdateProfileDTO(BaseSchema):
    """``PUT /user/settings/update-profile``: the caller's own profile, whitelisted fields only.

    Role / permission / group / status / email / username / password are NOT
    accepted here (``extra="forbid"`` -> 422 if sent).
    """

    model_config = STRICT

    fullname: Fullname | None = None
    phone: Phone | None = None
    about: About | None = None
    image: ImageRef | None = None
    settings: JsonObject | None = None
    personalization: JsonObject | None = None
