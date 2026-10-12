"""``/group`` — reads: any authenticated principal; writes: superuser."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from core.deps import AdminUserDep, get_current_user
from core.responses import ApiResponse, created, ok, paginated
from dto.common import IdParam, MessageData
from dto.group import FindGroupDTO, GroupDTO, GroupResponse, UpdateGroupDTO
from service.group import GroupServiceDep

router = APIRouter(prefix="/group", tags=["group"], dependencies=[Depends(get_current_user)])


@router.post("/add", status_code=201, response_model=ApiResponse[GroupResponse])
def add(dto: GroupDTO, service: GroupServiceDep, admin: AdminUserDep):
    return created(service.create(dto.to_storage(exclude_unset=False), actor_id=admin.id))


@router.put("/update", response_model=ApiResponse[GroupResponse])
def update(dto: UpdateGroupDTO, service: GroupServiceDep, _: AdminUserDep):
    return ok(service.update(dto.id, dto.to_storage(exclude_unset=True, exclude={"id"})), message="Updated")


@router.delete("/delete", response_model=ApiResponse[MessageData])
def delete(id: IdParam, service: GroupServiceDep, _: AdminUserDep):
    service.delete(id)
    return ok(MessageData(message="Group deleted"))


@router.get("/get-one", response_model=ApiResponse[GroupResponse])
def get_one(id: IdParam, service: GroupServiceDep):
    return ok(service.get(id))


@router.post("/get-all", response_model=ApiResponse[list[GroupResponse]])
def get_all(query: FindGroupDTO, service: GroupServiceDep):
    items, total = service.list(query)
    return paginated(items, query.page, query.size, total)
