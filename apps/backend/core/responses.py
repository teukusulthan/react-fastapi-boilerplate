"""Response envelope models and helpers.

Success::

    {"metaData": {"status": true, "responseCode": 200, "message": "Success",
                  "executionTime": 5, "requestId": "...", "pagination": null},
     "data": ...}

Errors use :class:`ErrorResponse` (built by the global handlers in ``core.errors``).

Usage in a route (always declare ``response_model`` — it is what turns storage
dicts into camelCase DTOs and drops fields such as ``password_hash``)::

    @router.get("/get-one", response_model=ApiResponse[UserResponse])
    def get_one(id: IdParam, service: UserServiceDep):
        return ok(service.get(id))
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from pydantic import Field

from core.context import get_execution_time_ms, get_request_id
from dto.common import BaseSchema

T = TypeVar("T")


class Pagination(BaseSchema):
    page: int
    size: int
    total_elements: int
    total_pages: int

    @classmethod
    def build(cls, page: int, size: int, total: int) -> Pagination:
        return cls(page=page, size=size, total_elements=total, total_pages=math.ceil(total / size) if size > 0 else 0)


class MetaData(BaseSchema):
    status: bool = True
    response_code: int = 200
    message: str = "Success"
    execution_time: int = Field(default_factory=get_execution_time_ms)
    request_id: str | None = Field(default_factory=get_request_id)
    pagination: Pagination | None = None


class ErrorMetaData(BaseSchema):
    status: bool = False
    response_code: int = 500
    message: str = "Internal server error"
    error_code: str = "INTERNAL_ERROR"
    execution_time: int = Field(default_factory=get_execution_time_ms)
    request_id: str | None = Field(default_factory=get_request_id)


class ApiResponse(BaseSchema, Generic[T]):
    meta_data: MetaData = Field(default_factory=MetaData)
    data: T


class ErrorResponse(BaseSchema):
    meta_data: ErrorMetaData
    data: Any = None


def ok(data: Any = None, message: str = "Success", *, status_code: int = 200) -> ApiResponse[Any]:
    """Success envelope. Pair ``status_code`` with the route decorator's ``status_code``."""
    return ApiResponse[Any](meta_data=MetaData(response_code=status_code, message=message), data=data)


def created(data: Any = None, message: str = "Created") -> ApiResponse[Any]:
    """201 envelope — declare ``status_code=201`` on the route decorator as well."""
    return ok(data, message, status_code=201)


def paginated(
    items: Sequence[Any],
    page: int,
    size: int,
    total: int,
    message: str = "Success",
) -> ApiResponse[Any]:
    """List envelope for ``POST /x/get-all``; ``data`` is the item array."""
    return ApiResponse[Any](
        meta_data=MetaData(message=message, pagination=Pagination.build(page, size, total)),
        data=list(items),
    )


def error_payload(
    status_code: int,
    message: str,
    error_code: str,
    data: Any = None,
) -> dict[str, Any]:
    """JSON-ready error envelope (used by exception handlers and middleware)."""
    return ErrorResponse(
        meta_data=ErrorMetaData(response_code=status_code, message=message, error_code=error_code),
        data=data,
    ).model_dump(mode="json")
