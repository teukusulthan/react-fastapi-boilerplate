"""S3-compatible object storage (AWS S3, MinIO, Supabase Storage's S3 endpoint).

The boto3 client is created lazily on first use and cached per configuration.
Supabase Storage: ``BE_S3_ENDPOINT_URL=https://<ref>.supabase.co/storage/v1/s3``,
``BE_S3_REGION=<project region>``, keys from Storage -> S3 Connection,
``BE_S3_FORCE_PATH_STYLE=true``.

Raises ``ConfigurationError`` (503) when used without ``BE_S3_*`` configured.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import IO, TYPE_CHECKING, Any

from core.errors import ConfigurationError

if TYPE_CHECKING:
    from core.config import Settings

_lock = threading.Lock()
_cache: dict[tuple[Any, ...], S3Storage] = {}


@dataclass(frozen=True)
class S3Storage:
    client: Any  # botocore.client.S3
    bucket: str
    presign_ttl: int

    def put_object(
        self, key: str, body: bytes | IO[bytes], content_type: str, *, metadata: dict[str, str] | None = None
    ) -> None:
        extra: dict[str, Any] = {"ContentType": content_type}
        if metadata:
            extra["Metadata"] = metadata
        self.client.put_object(Bucket=self.bucket, Key=key, Body=body, **extra)

    def upload_fileobj(
        self,
        key: str,
        fileobj: IO[bytes],
        content_type: str,
        *,
        content_disposition: str | None = None,
        metadata: dict[str, str] | None = None,
        transfer_config: Any = None,
    ) -> None:
        """Stream ``fileobj`` to ``key`` (boto3 managed transfer: multipart above the config threshold).

        ``transfer_config`` is a ``boto3.s3.transfer.TransferConfig`` (``None`` = boto3 defaults).
        """
        extra: dict[str, Any] = {"ContentType": content_type}
        if content_disposition:
            extra["ContentDisposition"] = content_disposition
        if metadata:
            extra["Metadata"] = metadata
        kwargs: dict[str, Any] = {"ExtraArgs": extra}
        if transfer_config is not None:
            kwargs["Config"] = transfer_config
        self.client.upload_fileobj(fileobj, self.bucket, key, **kwargs)

    def get_object(self, key: str) -> bytes:
        response = self.client.get_object(Bucket=self.bucket, Key=key)
        return response["Body"].read()

    def delete_object(self, key: str) -> None:
        self.client.delete_object(Bucket=self.bucket, Key=key)

    def presigned_get_url(self, key: str, *, expires_in: int | None = None, filename: str | None = None) -> str:
        params: dict[str, Any] = {"Bucket": self.bucket, "Key": key}
        if filename:
            safe = filename.replace('"', "")
            params["ResponseContentDisposition"] = f'attachment; filename="{safe}"'
        return self.client.generate_presigned_url("get_object", Params=params, ExpiresIn=expires_in or self.presign_ttl)


def get_s3_storage(settings: Settings) -> S3Storage:
    access_key, secret_key, bucket = settings.S3_ACCESS_KEY_ID, settings.S3_SECRET_ACCESS_KEY, settings.S3_BUCKET
    if not settings.s3_configured or access_key is None or secret_key is None or bucket is None:
        raise ConfigurationError("File storage is not configured")
    key = (
        settings.S3_ENDPOINT_URL,
        settings.S3_REGION,
        access_key.get_secret_value(),
        secret_key.get_secret_value(),
        bucket,
        settings.S3_FORCE_PATH_STYLE,
        settings.S3_PRESIGN_TTL,
    )
    storage = _cache.get(key)
    if storage is not None:
        return storage
    with _lock:
        storage = _cache.get(key)
        if storage is None:
            import boto3
            from botocore.config import Config

            client = boto3.client(
                "s3",
                endpoint_url=settings.S3_ENDPOINT_URL,
                region_name=settings.S3_REGION,
                aws_access_key_id=key[2],
                aws_secret_access_key=key[3],
                config=Config(
                    signature_version="s3v4",
                    s3={"addressing_style": "path" if settings.S3_FORCE_PATH_STYLE else "auto"},
                    retries={"max_attempts": 3, "mode": "standard"},
                    connect_timeout=5,
                    read_timeout=60,
                ),
            )
            storage = S3Storage(client=client, bucket=bucket, presign_ttl=settings.S3_PRESIGN_TTL)
            _cache[key] = storage
    return storage
