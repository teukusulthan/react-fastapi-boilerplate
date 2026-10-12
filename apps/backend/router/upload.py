"""``/upload`` — authenticated users; owners see/delete their own files, superusers all.

``POST /upload/upload-file`` is ``multipart/form-data`` with the file in the
``file`` part (see ``dto.upload.UploadFileForm`` for the other form fields).
The request body is capped while it streams (:class:`UploadLimitRoute`), so an
oversized upload is rejected with 413 before it is spooled to disk.
"""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.routing import APIRoute
from starlette.types import Message

from core.deps import CurrentUserDep, require_auth
from core.responses import ApiResponse, created, ok, paginated
from dto.common import IdParam, MessageData
from dto.upload import FindUploadDTO, UploadFileForm, UploadResponse
from service.upload import UploadServiceDep

# Room for multipart boundaries + the small metadata fields on top of the file itself.
MULTIPART_OVERHEAD_BYTES = 256 * 1024


class UploadLimitRoute(APIRoute):
    """Reject request bodies larger than ``BE_UPLOAD_MAX_SIZE_MB`` (+ overhead) with 413.

    Checks ``Content-Length`` up front and counts streamed bytes (chunked
    uploads), aborting as soon as the limit is crossed. ``HTTPException`` is
    re-raised by FastAPI's body parser and rendered as ``PAYLOAD_TOO_LARGE``.
    """

    def get_route_handler(self) -> Callable[[Request], Coroutine[Any, Any, Response]]:
        handler = super().get_route_handler()

        async def limited_handler(request: Request) -> Response:
            limit = request.app.state.settings.upload_max_bytes + MULTIPART_OVERHEAD_BYTES
            declared = request.headers.get("content-length", "")
            if declared.isdigit() and int(declared) > limit:
                raise HTTPException(status_code=413, detail="Request body is too large")
            received = 0

            async def receive() -> Message:
                nonlocal received
                message = await request.receive()
                if message["type"] == "http.request":
                    received += len(message.get("body", b""))
                    if received > limit:
                        raise HTTPException(status_code=413, detail="Request body is too large")
                return message

            return await handler(Request(request.scope, receive))

        return limited_handler


router = APIRouter(
    prefix="/upload", tags=["upload"], dependencies=[Depends(require_auth)], route_class=UploadLimitRoute
)


@router.post("/upload-file", status_code=201, response_model=ApiResponse[UploadResponse])
def upload_file(
    form: Annotated[UploadFileForm, Form(media_type="multipart/form-data")],
    service: UploadServiceDep,
    user: CurrentUserDep,
):
    return created(service.upload(form, user), message="File uploaded")


@router.post("/get-all", response_model=ApiResponse[list[UploadResponse]])
def get_all(query: FindUploadDTO, service: UploadServiceDep, user: CurrentUserDep):
    items, total = service.list_for(query, user)
    return paginated(items, query.page, query.size, total)


@router.get("/get-one", response_model=ApiResponse[UploadResponse])
def get_one(id: IdParam, service: UploadServiceDep, user: CurrentUserDep):
    return ok(service.get_for(id, user))


@router.delete("/delete", response_model=ApiResponse[MessageData])
def delete(id: IdParam, service: UploadServiceDep, user: CurrentUserDep):
    service.delete_for(id, user)
    return ok(MessageData(message="File deleted"))
