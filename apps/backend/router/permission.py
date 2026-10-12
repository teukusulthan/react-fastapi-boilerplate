"""``/permission`` — reads: any authenticated principal; writes: superuser."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.deps import AdminUserDep, get_current_user
from core.responses import ApiResponse, created, ok, paginated
from dto.common import IdParam, MessageData
from dto.permission import (
    FindPermissionDTO,
    PermissionDTO,
    PermissionResponse,
    UpdatePermissionDTO,
    UpdatePrivilegesDTO,
)
from service.permission import PermissionServiceDep

router = APIRouter(prefix="/permission", tags=["permission"], dependencies=[Depends(get_current_user)])


@router.post("/add", status_code=201, response_model=ApiResponse[PermissionResponse])
def add(dto: PermissionDTO, service: PermissionServiceDep, admin: AdminUserDep):
    return created(service.create_permission(dto, admin))


@router.put("/update", response_model=ApiResponse[PermissionResponse])
def update(dto: UpdatePermissionDTO, service: PermissionServiceDep, admin: AdminUserDep):
    return ok(service.update_permission(dto, admin), message="Updated")


@router.put("/update-partial", response_model=ApiResponse[PermissionResponse])
def update_partial(dto: UpdatePrivilegesDTO, service: PermissionServiceDep, _: AdminUserDep):
    """Add and/or remove individual privileges without resending the whole list."""
    return ok(service.update_privileges(dto), message="Updated")


@router.delete("/delete", response_model=ApiResponse[MessageData])
def delete(id: IdParam, service: PermissionServiceDep, _: AdminUserDep):
    service.delete_permission(id)
    return ok(MessageData(message="Permission deleted"))


@router.get("/get-one", response_model=ApiResponse[PermissionResponse])
def get_one(id: IdParam, service: PermissionServiceDep):
    return ok(service.get(id))


@router.post("/get-all", response_model=ApiResponse[list[PermissionResponse]])
def get_all(query: FindPermissionDTO, service: PermissionServiceDep):
    items, total = service.list(query)
    return paginated(items, query.page, query.size, total)
