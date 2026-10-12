"""``/role`` — reference CRUD router (thin: parse -> service -> envelope).

RBAC: every route needs an authenticated principal (user or ``X-Internal-Token``);
writes additionally need a superuser (``AdminUserDep``).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.deps import AdminUserDep, get_current_user
from core.responses import ApiResponse, created, ok, paginated
from dto.common import IdParam, MessageData
from dto.role import FindRoleDTO, RoleDTO, RoleResponse, UpdateRoleDTO
from service.role import RoleServiceDep

router = APIRouter(prefix="/role", tags=["role"], dependencies=[Depends(get_current_user)])


@router.post("/add", status_code=201, response_model=ApiResponse[RoleResponse])
def add(dto: RoleDTO, service: RoleServiceDep, admin: AdminUserDep):
    return created(service.create(dto.to_storage(exclude_unset=False), actor_id=admin.id))


@router.put("/update", response_model=ApiResponse[RoleResponse])
def update(dto: UpdateRoleDTO, service: RoleServiceDep, _: AdminUserDep):
    return ok(service.update(dto.id, dto.to_storage(exclude_unset=True, exclude={"id"})), message="Updated")


@router.delete("/delete", response_model=ApiResponse[MessageData])
def delete(id: IdParam, service: RoleServiceDep, _: AdminUserDep):
    service.delete(id)
    return ok(MessageData(message="Role deleted"))


@router.get("/get-one", response_model=ApiResponse[RoleResponse])
def get_one(id: IdParam, service: RoleServiceDep):
    return ok(service.get(id))


@router.post("/get-all", response_model=ApiResponse[list[RoleResponse]])
def get_all(query: FindRoleDTO, service: RoleServiceDep):
    items, total = service.list(query)
    return paginated(items, query.page, query.size, total)
