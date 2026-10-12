"""Upload DTOs.

``POST /upload/upload-file`` is ``multipart/form-data``; :class:`UploadFileForm`
is bound with ``Annotated[UploadFileForm, Form()]`` so the file part and the
metadata fields are validated together (camelCase field names, unknown fields
-> 422). ``created_by`` is never accepted from the client — it comes from the
access token.
"""

from __future__ import annotations

import re
from datetime import datetime
from typing import Annotated

from fastapi import UploadFile
from pydantic import ConfigDict, Field, StringConstraints, field_validator

from dto.common import BaseSchema, FindDTO

FILE_FIELD = "file"
DEFAULT_FOLDER = "general"
MAX_TAGS = 20

ExternalRef = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=64)]
_TAG = re.compile(r"[A-Za-z0-9_.:-]{1,50}")


class UploadFileForm(BaseSchema):
    """Multipart form of ``POST /upload/upload-file`` (file part name: ``file``)."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    file: UploadFile
    folder: str = Field(
        default=DEFAULT_FOLDER,
        max_length=200,
        description="Logical folder: 1-5 segments of [A-Za-z0-9_-] separated by '/'",
    )
    filename: str | None = Field(
        default=None, max_length=255, description="Display name override (the extension is taken from the content)"
    )
    tags: str | None = Field(default=None, max_length=2000, description="Comma-separated tags")
    widget_id: ExternalRef | None = None
    dashboard_id: ExternalRef | None = None
    workspace_id: ExternalRef | None = None
    connection_id: ExternalRef | None = None
    extract_file: bool = Field(default=False, description="Publish a Kafka extraction event after storing")
    rescale_file: bool = Field(default=False, description="Images only: downscale (format is preserved)")
    scale_factor: float | None = Field(
        default=None, gt=0, le=1, description="With rescaleFile: multiply both sides by this factor"
    )

    @field_validator("tags")
    @classmethod
    def _tags(cls, value: str | None) -> str | None:
        if value is None:
            return None
        tags = [t.strip() for t in value.split(",") if t.strip()]
        if len(tags) > MAX_TAGS:
            raise ValueError(f"at most {MAX_TAGS} tags")
        bad = [t for t in tags if not _TAG.fullmatch(t)]
        if bad:
            raise ValueError("tags may only contain letters, digits and _ . : - (max 50 chars each)")
        return ",".join(dict.fromkeys(tags))

    @property
    def tag_list(self) -> list[str]:
        return self.tags.split(",") if self.tags else []


class FindUploadDTO(FindDTO):
    """``POST /upload/get-all`` body (whitelists: ``db.schema.UPLOADS``)."""


class UploadResponse(BaseSchema):
    id: str
    object_key: str
    filename: str
    mime_type: str | None = None
    filesize: int | None = None
    folder: str | None = None
    tags: list[str] = Field(default_factory=list)
    widget_id: str | None = None
    dashboard_id: str | None = None
    workspace_id: str | None = None
    connection_id: str | None = None
    created_by: str | None = None
    created_at: datetime
    updated_at: datetime
    # Only on get-one/upload-file: short-lived presigned download URL (served as an attachment).
    download_url: str | None = None
