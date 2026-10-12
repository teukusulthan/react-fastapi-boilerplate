"""``/user`` — user administration (superuser) + the caller's own profile.

Every route requires an authenticated *user* (internal-token calls -> 403).
Admin routes take ``AdminUserDep``; ``PUT /settings/update-profile`` is
self-service with a whitelisted DTO. There is deliberately no ``/user/{username}``
catch-all (use ``GET /user/get-by-username?username=``).
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.deps import AdminUserDep, CurrentUserDep, require_auth
from core.responses import ApiResponse, created, ok, paginated
from dto.common import IdParam, MessageData
from dto.user import (
    CheckAvailabilityResponse,
    CreateUserDTO,
    FindUserDTO,
    ResetPasswordDTO,
    UpdateProfileDTO,
    UpdateUserDTO,
    UserResponse,
)
from service.user import UserServiceDep

router = APIRouter(prefix="/user", tags=["user"], dependencies=[Depends(require_auth)])

LookupValue = Annotated[str, Query(min_length=1, max_length=254)]


# ------------------------------------------------------------------ admin
@router.post("/add", status_code=201, response_model=ApiResponse[UserResponse])
def add(dto: CreateUserDTO, service: UserServiceDep, admin: AdminUserDep):
    return created(service.create_user(dto, admin))


@router.put("/update", response_model=ApiResponse[UserResponse])
def update(dto: UpdateUserDTO, service: UserServiceDep, admin: AdminUserDep):
    return ok(service.update_user(dto, admin), message="Updated")


@router.delete("/delete", response_model=ApiResponse[MessageData])
def delete(id: IdParam, service: UserServiceDep, admin: AdminUserDep):
    service.delete_user(id, admin)
    return ok(MessageData(message="User deleted"))


@router.get("/get-one", response_model=ApiResponse[UserResponse])
def get_one(id: IdParam, service: UserServiceDep, _: AdminUserDep):
    return ok(service.get_user(id))


@router.get("/get-by-username", response_model=ApiResponse[UserResponse])
def get_by_username(username: LookupValue, service: UserServiceDep, _: AdminUserDep):
    return ok(service.get_by_username(username))


@router.post("/get-all", response_model=ApiResponse[list[UserResponse]])
def get_all(query: FindUserDTO, service: UserServiceDep, _: AdminUserDep):
    items, total = service.list_users(query)
    return paginated(items, query.page, query.size, total)


@router.post("/reset-password", response_model=ApiResponse[MessageData])
def reset_password(dto: ResetPasswordDTO, service: UserServiceDep, admin: AdminUserDep):
    """Set a user's password (admin) and revoke every session/token of that user."""
    return ok(service.reset_password(dto, admin))


@router.get("/check-email", response_model=ApiResponse[CheckAvailabilityResponse])
def check_email(email: LookupValue, service: UserServiceDep, _: AdminUserDep):
    return ok(service.check_availability("email", email))


@router.get("/check-username", response_model=ApiResponse[CheckAvailabilityResponse])
def check_username(username: LookupValue, service: UserServiceDep, _: AdminUserDep):
    return ok(service.check_availability("username", username))


@router.get("/check-phone", response_model=ApiResponse[CheckAvailabilityResponse])
def check_phone(phone: LookupValue, service: UserServiceDep, _: AdminUserDep):
    return ok(service.check_availability("phone", phone))


# ----------------------------------------------------------- self-service
@router.put("/settings/update-profile", response_model=ApiResponse[UserResponse])
def update_profile(dto: UpdateProfileDTO, service: UserServiceDep, user: CurrentUserDep):
    """Update the caller's own profile (fullname, phone, about, image, settings, personalization)."""
    return ok(service.update_profile(user, dto), message="Updated")
