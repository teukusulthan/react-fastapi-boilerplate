"""File uploads to S3-compatible storage + metadata rows in the ``uploads`` entity.

Pipeline for ``POST /upload/upload-file`` (the router has already enforced the
request-body cap while streaming, so oversized bodies never reach this code):

1. exact size check (``BE_UPLOAD_MAX_SIZE_MB``; empty files -> 422),
2. content type from **magic bytes** (libmagic), refined by the extension only
   within the same family (text/plain -> text/csv, zip -> OOXML, OLE -> MS Office),
   then checked against ``BE_UPLOAD_ALLOWED_TYPES``; ``application/octet-stream``
   is never accepted and active content (HTML/SVG/XML/JS) only if listed explicitly,
3. sanitized object key ``{BE_UPLOAD_KEY_PREFIX}/{folder}/{uuid}-{safe_name}``
   whose extension always matches the detected type,
4. optional image downscale (format preserved, EXIF orientation applied),
5. boto3 managed transfer (single PUT below 8 MiB, multipart above) with
   ``Content-Disposition: attachment`` so browsers never render uploads inline,
6. metadata row (``created_by`` = caller); the object is removed again if the row fails,
7. optional Kafka extraction event (best effort, logged on failure).

The spooled request file (Starlette spools parts > 1 MiB to disk) is streamed to
S3; the whole file is never held in memory.
"""

from __future__ import annotations

import mimetypes
import re
import tempfile
import unicodedata
from collections.abc import Callable
from typing import IO, Annotated, Any

from fastapi import Depends
from loguru import logger

from core.config import Settings
from core.deps import CurrentUser, SettingsDep, UploadsRepo
from core.errors import AppError, ConfigurationError, ErrorCode, NotFoundError, ServiceUnavailableError, ValidationError
from db.base import Condition, Op, Repository
from dto.common import FindDTO
from dto.upload import UploadFileForm
from service import CrudService
from util.helper import new_id
from util.kafka import publish
from util.s3 import S3Storage, get_s3_storage

SNIFF_BYTES = 8192
MULTIPART_THRESHOLD = 8 * 1024 * 1024
MULTIPART_CHUNK = 8 * 1024 * 1024
SPOOL_MAX_BYTES = 8 * 1024 * 1024
MAX_FOLDER_DEPTH = 5
MAX_STEM_LENGTH = 100

NEVER_ALLOWED = frozenset({"application/octet-stream", "application/x-empty", "inode/x-empty"})
ACTIVE_CONTENT = frozenset(
    {
        "text/html",
        "application/xhtml+xml",
        "image/svg+xml",
        "text/xml",
        "application/xml",
        "text/javascript",
        "application/javascript",
    }
)
_TEXT_REFINEMENTS = frozenset({"text/csv", "application/json", "text/markdown", "text/tab-separated-values"})
_ZIP_REFINEMENTS = frozenset(
    {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    }
)
_OLE_DETECTED = frozenset({"application/x-ole-storage", "application/CDFV2", "application/vnd.ms-office"})
_OLE_REFINEMENTS = frozenset({"application/msword", "application/vnd.ms-excel", "application/vnd.ms-powerpoint"})
_CANONICAL_EXT = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/csv": ".csv",
    "application/json": ".json",
    "application/zip": ".zip",
}
_EXIF_ORIENTATION = 0x0112
_RESIZABLE_FORMATS = frozenset({"JPEG", "PNG", "WEBP", "GIF", "BMP", "TIFF"})

_FOLDER_SEGMENT = re.compile(r"[A-Za-z0-9_-]{1,64}")
_UNSAFE_CHARS = re.compile(r"[^A-Za-z0-9._-]+")


class UnsupportedMediaTypeError(AppError):
    status_code = 415
    error_code = ErrorCode.UNSUPPORTED_MEDIA_TYPE
    default_message = "File type is not allowed"


class PayloadTooLargeError(AppError):
    status_code = 413
    error_code = ErrorCode.PAYLOAD_TOO_LARGE
    default_message = "File is too large"


# --------------------------------------------------------------- pure helpers
def sanitize_folder(folder: str) -> str:
    """``"reports/2024"`` -> same; rejects traversal, empty or exotic segments (422)."""
    segments = folder.replace("\\", "/").strip().strip("/").split("/")
    if not segments or len(segments) > MAX_FOLDER_DEPTH or not all(_FOLDER_SEGMENT.fullmatch(s) for s in segments):
        raise ValidationError.for_field(
            "folder", f"Folder must be 1-{MAX_FOLDER_DEPTH} segments of letters, digits, '_' or '-' separated by '/'"
        )
    return "/".join(segments)


def safe_stem(name: str | None) -> str:
    """Path-free ASCII stem of a client filename (``"../../a b.PHP.jpg"`` -> ``"a-b.PHP"``)."""
    base = (name or "").replace("\x00", "").replace("\\", "/").rsplit("/", 1)[-1]
    stem = base.rsplit(".", 1)[0] if "." in base.strip(".") else base
    ascii_stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii")
    cleaned = _UNSAFE_CHARS.sub("-", ascii_stem).strip(".-_")
    cleaned = re.sub(r"\.{2,}", ".", cleaned)[:MAX_STEM_LENGTH].strip(".-_")
    return cleaned or "file"


def extension_for(mime: str, client_name: str | None) -> str:
    """Keep the client's extension only when it maps to the detected type; else the canonical one."""
    base = (client_name or "").rsplit("/", 1)[-1]
    if "." in base:
        ext = "." + base.rsplit(".", 1)[1].lower()
        if mimetypes.guess_type(f"x{ext}")[0] == mime and re.fullmatch(r"\.[a-z0-9]{1,10}", ext):
            return ext
    return _CANONICAL_EXT.get(mime) or mimetypes.guess_extension(mime) or ".bin"


def detect_mime(head: bytes, client_name: str | None) -> str:
    """Content type from magic bytes; the filename may only refine within the same family."""
    try:
        import magic
    except ImportError as exc:  # libmagic missing (install libmagic1 / file)
        raise ConfigurationError("File type detection is not available (libmagic is not installed)") from exc
    detected = str(magic.from_buffer(head, mime=True))
    guessed = mimetypes.guess_type(client_name or "")[0]
    if guessed and (
        (detected == "text/plain" and guessed in _TEXT_REFINEMENTS)
        or (detected == "application/zip" and guessed in _ZIP_REFINEMENTS)
        or (detected in _OLE_DETECTED and guessed in _OLE_REFINEMENTS)
    ):
        return guessed
    return detected


def check_allowed(mime: str, settings: Settings) -> None:
    allowed = {t.lower() for t in settings.UPLOAD_ALLOWED_TYPES}
    if mime.lower() in NEVER_ALLOWED or mime.lower() not in allowed:
        raise UnsupportedMediaTypeError(f"File type '{mime}' is not allowed")
    if mime.lower() in ACTIVE_CONTENT:
        logger.warning("Accepting active-content upload type {} (explicitly allowed by settings)", mime)


def file_size(fileobj: IO[bytes]) -> int:
    fileobj.seek(0, 2)
    size = fileobj.tell()
    fileobj.seek(0)
    return size


def resize_image(fileobj: IO[bytes], *, scale_factor: float | None, max_dimension: int) -> IO[bytes] | None:
    """Downscale an image, keeping its format. ``None`` = nothing to do (already small / animated)."""
    from PIL import Image, ImageOps, UnidentifiedImageError

    fileobj.seek(0)
    try:
        with Image.open(fileobj) as original:
            fmt = original.format
            if fmt not in _RESIZABLE_FORMATS:
                raise ValidationError.for_field("rescaleFile", f"Images of format {fmt} cannot be rescaled")
            if getattr(original, "n_frames", 1) > 1:
                logger.info("Skipping rescale of an animated {} image", fmt)
                return None
            rotated = original.getexif().get(_EXIF_ORIENTATION, 1) not in (None, 1)
            image = ImageOps.exif_transpose(original) if rotated else original
            width, height = image.size
            factor = scale_factor or 1.0
            target_w, target_h = width * factor, height * factor
            longest = max(target_w, target_h)
            if longest > max_dimension:
                target_w, target_h = target_w * max_dimension / longest, target_h * max_dimension / longest
            size = (max(1, round(target_w)), max(1, round(target_h)))
            if size == (width, height) and not rotated:
                return None
            resized = image.resize(size, Image.Resampling.LANCZOS) if size != (width, height) else image
            if fmt == "JPEG" and resized.mode not in ("RGB", "L", "CMYK"):
                resized = resized.convert("RGB")
            out = tempfile.SpooledTemporaryFile(max_size=SPOOL_MAX_BYTES)  # noqa: SIM115  # returned to caller
            options: dict[str, Any] = {"format": fmt}
            if fmt in ("JPEG", "WEBP"):
                options["quality"] = 90
            if fmt in ("JPEG", "PNG"):
                options["optimize"] = True
            resized.save(out, **options)
            out.seek(0)
            return out
    except (UnidentifiedImageError, Image.DecompressionBombError, OSError, ValueError) as exc:
        raise ValidationError.for_field("file", "Image could not be processed") from exc
    finally:
        fileobj.seek(0)


# ------------------------------------------------------------------ service
StorageFactory = Callable[[], S3Storage]


class UploadService(CrudService):
    not_found_message = "File not found"

    def __init__(self, uploads: Repository, settings: Settings, storage: StorageFactory) -> None:
        super().__init__(uploads)
        self.settings = settings
        self._storage_factory = storage

    def storage(self) -> S3Storage:
        return self._storage_factory()  # ConfigurationError (503) when S3 is not configured

    # ------------------------------------------------------------- reads
    def _owned(self, id: str, actor: CurrentUser) -> dict[str, Any]:
        record = self.get(id)
        if not actor.is_superuser and record.get("created_by") != actor.id:
            raise NotFoundError(self.not_found_message)  # don't reveal other users' files
        return record

    def _with_download_url(self, record: dict[str, Any]) -> dict[str, Any]:
        try:
            url = self.storage().presigned_get_url(record["object_key"], filename=record.get("filename"))
        except ConfigurationError:
            url = None
        return {**record, "download_url": url}

    def get_for(self, id: str, actor: CurrentUser) -> dict[str, Any]:
        return self._with_download_url(self._owned(id, actor))

    def list_for(self, query: FindDTO, actor: CurrentUser) -> tuple[list[dict[str, Any]], int]:
        scope = () if actor.is_superuser else (Condition("created_by", Op.EQ, actor.id),)
        return self.list(query, extra_where=scope)

    # ------------------------------------------------------------ writes
    def upload(self, form: UploadFileForm, actor: CurrentUser) -> dict[str, Any]:
        settings = self.settings
        topic = settings.KAFKA_TOPIC_FILE_EXTRACTION
        if form.extract_file and not (settings.kafka_configured and topic):
            raise ConfigurationError("File extraction queue is not configured")
        folder = sanitize_folder(form.folder)
        source = form.file.file
        size = file_size(source)
        if size == 0:
            raise ValidationError.for_field("file", "File is empty")
        if size > settings.upload_max_bytes:
            raise PayloadTooLargeError(f"File exceeds the {settings.UPLOAD_MAX_SIZE_MB} MB limit")

        mime = detect_mime(source.read(SNIFF_BYTES), form.file.filename)
        source.seek(0)
        check_allowed(mime, settings)
        storage = self.storage()  # fail with 503 before doing any work if S3 is not configured

        body: IO[bytes] = source
        if form.rescale_file:
            if not mime.startswith("image/"):
                raise ValidationError.for_field("rescaleFile", "Only images can be rescaled")
            resized = resize_image(
                source, scale_factor=form.scale_factor, max_dimension=settings.UPLOAD_IMAGE_MAX_DIMENSION
            )
            if resized is not None:
                body = resized
                size = file_size(resized)

        upload_id = new_id()
        display_name = f"{safe_stem(form.filename or form.file.filename)}{extension_for(mime, form.file.filename)}"
        prefix = settings.UPLOAD_KEY_PREFIX.strip("/")
        object_key = "/".join(p for p in (prefix, folder, f"{upload_id}-{display_name}") if p)

        try:
            self._put(storage, object_key, body, mime, display_name, upload_id, actor.id)
            try:
                record = self.repo.insert(
                    {
                        "id": upload_id,
                        "bucket": storage.bucket,
                        "object_key": object_key,
                        "filename": display_name,
                        "mime_type": mime,
                        "filesize": size,
                        "folder": folder,
                        "tags": form.tag_list,
                        "widget_id": form.widget_id,
                        "dashboard_id": form.dashboard_id,
                        "workspace_id": form.workspace_id,
                        "connection_id": form.connection_id,
                        "created_by": actor.id,
                    }
                )
            except Exception:
                self._delete_object(storage, object_key, missing_ok=True)
                raise
        finally:
            if body is not source:
                body.close()

        logger.info("Upload {} stored ({} bytes, {}) by {}", upload_id, size, mime, actor.id)
        if form.extract_file:
            self._publish_extraction(record)
        return self._with_download_url(record)

    def delete_for(self, id: str, actor: CurrentUser) -> None:
        record = self._owned(id, actor)
        self._delete_object(self.storage(), record["object_key"])
        self.delete(record["id"])
        logger.info("Upload {} deleted by {}", id, actor.id)

    # ----------------------------------------------------------- plumbing
    def _put(
        self, storage: S3Storage, key: str, body: IO[bytes], mime: str, filename: str, upload_id: str, actor_id: str
    ) -> None:
        from boto3.s3.transfer import TransferConfig
        from botocore.exceptions import BotoCoreError, ClientError

        config = TransferConfig(
            multipart_threshold=MULTIPART_THRESHOLD, multipart_chunksize=MULTIPART_CHUNK, max_concurrency=4
        )
        body.seek(0)
        try:
            storage.upload_fileobj(
                key,
                body,
                mime,
                content_disposition=f'attachment; filename="{filename}"',
                metadata={"upload-id": upload_id, "created-by": actor_id},
                transfer_config=config,
            )
        except (BotoCoreError, ClientError) as exc:
            logger.error("S3 upload of {} failed: {}", key, exc)
            raise ServiceUnavailableError("File storage is unavailable") from exc

    def _delete_object(self, storage: S3Storage, key: str, *, missing_ok: bool = False) -> None:
        from botocore.exceptions import BotoCoreError, ClientError

        try:
            storage.delete_object(key)  # S3 DeleteObject is idempotent (no error for missing keys)
        except (BotoCoreError, ClientError) as exc:
            logger.error("S3 delete of {} failed: {}", key, exc)
            if not missing_ok:
                raise ServiceUnavailableError("File storage is unavailable") from exc

    def _publish_extraction(self, record: dict[str, Any]) -> None:
        event = {
            "uploadId": record["id"],
            "bucket": record["bucket"],
            "objectKey": record["object_key"],
            "filename": record["filename"],
            "mimeType": record["mime_type"],
            "filesize": record["filesize"],
            "folder": record["folder"],
            "tags": record["tags"],
            "createdBy": record["created_by"],
        }
        try:
            publish(self.settings, self.settings.KAFKA_TOPIC_FILE_EXTRACTION, event, key=record["id"])
        except Exception as exc:  # noqa: BLE001  # the file is stored; extraction is best effort
            logger.error("Could not queue upload {} for extraction: {}", record["id"], exc)


# ------------------------------------------------------------------- deps
def get_storage_factory(settings: SettingsDep) -> StorageFactory:
    """Lazy S3 access (override in tests with ``app.dependency_overrides``)."""
    return lambda: get_s3_storage(settings)


def get_upload_service(
    uploads: UploadsRepo,
    settings: SettingsDep,
    storage: Annotated[StorageFactory, Depends(get_storage_factory)],
) -> UploadService:
    return UploadService(uploads, settings, storage)


UploadServiceDep = Annotated[UploadService, Depends(get_upload_service)]
