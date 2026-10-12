"""User read models (responses only — never contain password_hash / two_factor_secret / OTP data).

* :class:`UserProfile` — the CONTRACT shape returned by ``/auth/login``, ``/auth/me`` …
* :class:`UserResponse` — admin view (``/user/get-one``, ``/user/get-all``): profile + extra columns.

Build them with ``service.user_profile.build_user_profile`` / ``load_user_profile(s)``.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict, Field

from dto.common import BaseSchema


class PermissionSummary(BaseSchema):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str
    alias: str | None = None
    privileges: list[str] = Field(default_factory=list)


class GroupSummary(BaseSchema):
    model_config = ConfigDict(extra="ignore")

    id: str
    name: str


class UserProfile(BaseSchema):
    model_config = ConfigDict(extra="ignore")

    id: str
    username: str
    fullname: str | None = None
    email: str
    phone: str | None = None
    status: str
    email_verified: bool = False
    two_factor_enabled: bool = False
    role: str | None = None
    permission_id: str | None = None
    permission: PermissionSummary | None = None
    group_id: str | None = None
    group: GroupSummary | None = None
    last_login_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class UserResponse(UserProfile):
    """Admin/detail view of a user."""

    about: str | None = None
    image: str | None = None
    multi_login: bool = True
    expired_at: datetime | None = None
    two_factor_method: str | None = None
    auth_provider: str | None = None
    settings: dict[str, Any] | None = None
    personalization: dict[str, Any] | None = None
    additional: dict[str, Any] | None = None
    created_by: str | None = None
