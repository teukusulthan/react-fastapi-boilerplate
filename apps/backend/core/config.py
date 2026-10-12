"""Application settings (pydantic-settings v2).

* Every env var is prefixed with ``BE_`` (``BE_MONGO_URI`` -> ``settings.MONGO_URI``).
* The env file is ``BE_ENV_FILE`` (default ``.env``), resolved against the current
  working directory first, then the backend directory. Real environment variables
  always win over the file.
* Nothing happens at import time: call :func:`get_settings` (cached) or build
  ``Settings(...)`` explicitly (tests, scripts).

List-valued settings accept either a comma-separated string or a JSON array.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Annotated, Any, Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict

from util.crypto import CryptoError, build_fernet, decode_aes_key

BACKEND_DIR = Path(__file__).resolve().parent.parent
ENV_PREFIX = "BE_"
MIN_SECRET_LENGTH = 32
# Placeholder prefix used by .env.example; refused when ENVIRONMENT=production.
PLACEHOLDER_SECRET_PREFIX = "change-me"  # noqa: S105  # a prefix we refuse, not a secret

CsvList = Annotated[list[str], NoDecode]


def _split_csv(value: Any) -> Any:
    if value is None:
        return []
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return []
        if text.startswith("["):
            return [str(item).strip() for item in json.loads(text) if str(item).strip()]
        return [item.strip() for item in text.split(",") if item.strip()]
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix=ENV_PREFIX,
        env_file=None,  # chosen at runtime by get_settings() via BE_ENV_FILE
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
        validate_default=True,
    )

    # ------------------------------------------------------------------ app
    APP_NAME: str = "App"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: Literal["development", "test", "staging", "production"] = "development"
    HOST: str = "0.0.0.0"  # noqa: S104  # container default; override per env
    PORT: int = Field(default=8020, ge=1, le=65535)
    WORKERS: int = Field(default=1, ge=1)
    RELOAD: bool = False
    ROOT_PATH: str = ""
    DOCS_ENABLED: bool = True
    # Max concurrent sync (def) routes/dependencies — anyio's default thread limiter.
    THREADPOOL_SIZE: int = Field(default=40, ge=1, le=1000)
    ENABLED_ROUTERS: CsvList = Field(default_factory=list)
    PUBLIC_WEB_URL: str = "http://localhost:3000"

    # -------------------------------------------------------------- logging
    LOG_LEVEL: Literal["TRACE", "DEBUG", "INFO", "SUCCESS", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_JSON: bool = False
    ACCESS_LOG: bool = True

    # ------------------------------------------------------------- database
    DB_PROVIDER: Literal["mongo", "supabase"] = "mongo"
    MONGO_URI: SecretStr = SecretStr("mongodb://localhost:27017")
    MONGO_DB: str = "app"
    MONGO_TIMEOUT_MS: int = Field(default=5000, ge=100)

    SUPABASE_URL: str | None = None
    SUPABASE_DB_URL: SecretStr | None = None  # postgresql://user:pass@host:5432/postgres
    SUPABASE_DB_SCHEMA: str = "public"
    SUPABASE_DB_POOL_MIN: int = Field(default=1, ge=0)
    SUPABASE_DB_POOL_MAX: int = Field(default=10, ge=1)
    SUPABASE_DB_TIMEOUT: float = Field(default=10.0, gt=0)
    SUPABASE_JWT_SECRET: SecretStr | None = None
    SUPABASE_JWKS_URL: str | None = None
    SUPABASE_JWT_AUDIENCE: str = "authenticated"
    SUPABASE_JWT_ISSUER: str | None = None

    # Table (Postgres) / collection (Mongo) names.
    TABLE_USERS: str = "users"
    TABLE_PERMISSIONS: str = "permissions"
    TABLE_GROUPS: str = "groups"
    TABLE_ROLES: str = "roles"
    TABLE_UPLOADS: str = "uploads"

    # ---------------------------------------------------------------- redis
    REDIS_URL: SecretStr | None = None  # wins over host/port/password/db when set
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: SecretStr | None = None
    REDIS_DB: int = Field(default=0, ge=0)
    REDIS_SSL: bool = False
    REDIS_KEY_PREFIX: str = "app"

    # ----------------------------------------------------------------- auth
    AUTH_PROVIDER: Literal["local", "supabase"] = "local"
    JWT_SECRET: SecretStr
    JWT_ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    JWT_ISSUER: str = "app"
    JWT_ACCESS_TTL: int = Field(default=900, ge=60)
    JWT_REFRESH_TTL: int = Field(default=604800, ge=300)
    JWT_LEEWAY: int = Field(default=10, ge=0, le=300)
    COOKIE_SECURE: bool = True
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    COOKIE_DOMAIN: str | None = None
    COOKIE_REFRESH_PATH: str = "/"
    INTERNAL_TOKEN: SecretStr | None = None
    SUPERUSER_ALIASES: CsvList = Field(default_factory=lambda: ["admin", "owner"])
    DEFAULT_PERMISSION_ALIAS: str = "user"
    PASSWORD_MIN_LENGTH: int = Field(default=8, ge=6, le=72)
    ACCOUNT_LOCK_MAX_ATTEMPTS: int = Field(default=5, ge=1)
    ACCOUNT_LOCK_SECONDS: int = Field(default=900, ge=1)
    OTP_LENGTH: int = Field(default=6, ge=4, le=10)
    OTP_TTL: int = Field(default=600, ge=30)
    OTP_MAX_ATTEMPTS: int = Field(default=5, ge=1)
    OTP_RESEND_COOLDOWN: int = Field(default=60, ge=0)
    TWO_FACTOR_SESSION_TTL: int = Field(default=300, ge=30)
    TOTP_ISSUER: str | None = None  # defaults to APP_NAME
    GOOGLE_CLIENT_ID: str | None = None
    GOOGLE_CLIENT_SECRET: SecretStr | None = None

    BOOTSTRAP_ADMIN_EMAIL: str | None = None
    BOOTSTRAP_ADMIN_PASSWORD: SecretStr | None = None
    BOOTSTRAP_ADMIN_USERNAME: str = "admin"
    BOOTSTRAP_ADMIN_FULLNAME: str = "Administrator"

    # ------------------------------------------------------------- http/cors
    CORS_ORIGINS: CsvList = Field(default_factory=lambda: ["http://localhost:3000"])
    TRUST_PROXY_HEADERS: bool = False
    PROXY_TRUSTED_HOPS: int = Field(default=1, ge=1, le=10)

    # ------------------------------------------------------------ rate limit
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_GLOBAL: int = Field(default=0, ge=0)  # requests/window per client; 0 = off
    RATE_LIMIT_WINDOW: int = Field(default=60, ge=1)
    RATE_LIMIT_AUTH: int = Field(default=10, ge=1)  # sensitive endpoints, per client/window
    RATE_LIMIT_AUTH_WINDOW: int = Field(default=60, ge=1)
    MAX_PAGE_SIZE: int = Field(default=100, ge=1, le=1000)

    # ------------------------------------------------------------ encryption
    DATA_ENCRYPTION_KEY: SecretStr | None = None  # Fernet key for secrets at rest
    ENC_ACTIVE: bool = False
    ENC_SECRET: SecretStr | None = None  # base64 32-byte AES-256-GCM key

    # ---------------------------------------------------------------- upload
    UPLOAD_MAX_SIZE_MB: int = Field(default=25, ge=1)
    UPLOAD_ALLOWED_TYPES: CsvList = Field(
        default_factory=lambda: [
            "image/jpeg",
            "image/png",
            "image/gif",
            "image/webp",
            "application/pdf",
            "text/plain",
            "text/csv",
            "application/json",
            "application/zip",
            "application/msword",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/vnd.ms-excel",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "application/vnd.ms-powerpoint",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        ]
    )
    UPLOAD_IMAGE_MAX_DIMENSION: int = Field(default=2048, ge=64)
    UPLOAD_KEY_PREFIX: str = "uploads"

    # -------------------------------------------------- S3 (AWS/MinIO/Supabase)
    S3_ENDPOINT_URL: str | None = None
    S3_REGION: str = "us-east-1"
    S3_ACCESS_KEY_ID: SecretStr | None = None
    S3_SECRET_ACCESS_KEY: SecretStr | None = None
    S3_BUCKET: str | None = None
    S3_FORCE_PATH_STYLE: bool = True
    S3_PRESIGN_TTL: int = Field(default=900, ge=1)

    # ----------------------------------------------------------------- kafka
    KAFKA_BOOTSTRAP_SERVERS: str | None = None
    KAFKA_CLIENT_ID: str | None = None
    KAFKA_TOPIC_FILE_EXTRACTION: str | None = None

    # ------------------------------------------------------------------ smtp
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: SecretStr | None = None
    SMTP_STARTTLS: bool = True
    SMTP_SSL: bool = False
    SMTP_FROM_EMAIL: str | None = None
    SMTP_FROM_NAME: str | None = None  # defaults to APP_NAME
    SMTP_TIMEOUT: float = Field(default=10.0, gt=0)

    # ----------------------------------------------------- email delivery
    # auto = smtp when SMTP is configured, else console (dev) / disabled (production)
    EMAIL_BACKEND: Literal["auto", "smtp", "console", "disabled"] = "auto"
    EMAIL_TEMPLATES_DIR: str | None = None  # default: <backend>/templates/email

    # --------------------------------------------- auth flows (local provider)
    REGISTRATION_ENABLED: bool = True
    # A pending (unverified) account older than this may be replaced by a new registration.
    REGISTRATION_PENDING_TTL: int = Field(default=86400, ge=300)
    EMAIL_VERIFY_TTL: int = Field(default=86400, ge=300)
    EMAIL_VERIFY_PATH: str = "/auth/verify-email"  # web route receiving ?token=
    WEB_LOGIN_PATH: str = "/auth/login"  # web sign-in route (links in emails)
    GOOGLE_AUTO_REGISTER: bool = False
    GOOGLE_ALLOWED_DOMAINS: CsvList = Field(default_factory=list)  # empty = any domain
    GOOGLE_HTTP_TIMEOUT: float = Field(default=10.0, gt=0)

    # ------------------------------------------------------------ validators
    @field_validator("GOOGLE_ALLOWED_DOMAINS", mode="before")
    @classmethod
    def _parse_domains(cls, value: Any) -> Any:
        return [item.lower().lstrip("@") for item in _split_csv(value)]

    @field_validator("EMAIL_TEMPLATES_DIR", mode="before")
    @classmethod
    def _blank_templates_dir(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def _email_checks(self) -> Settings:
        if self.EMAIL_BACKEND == "smtp" and not self.smtp_configured:
            raise ValueError("BE_EMAIL_BACKEND=smtp requires BE_SMTP_HOST and BE_SMTP_FROM_EMAIL")
        if self.EMAIL_BACKEND == "console" and self.is_production:
            raise ValueError("BE_EMAIL_BACKEND=console is not allowed in production (it logs one-time codes)")
        return self

    @field_validator("ENABLED_ROUTERS", "SUPERUSER_ALIASES", "CORS_ORIGINS", "UPLOAD_ALLOWED_TYPES", mode="before")
    @classmethod
    def _parse_csv(cls, value: Any) -> Any:
        return _split_csv(value)

    @field_validator("ENABLED_ROUTERS", "SUPERUSER_ALIASES")
    @classmethod
    def _lower(cls, value: list[str]) -> list[str]:
        return [item.lower() for item in value]

    @field_validator("CORS_ORIGINS")
    @classmethod
    def _no_wildcard_origin(cls, value: list[str]) -> list[str]:
        if "*" in value:
            raise ValueError("'*' is not allowed because credentials (cookies) are enabled; list explicit origins")
        return [origin.rstrip("/") for origin in value]

    @field_validator("JWT_SECRET")
    @classmethod
    def _jwt_secret_length(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value()) < MIN_SECRET_LENGTH:
            raise ValueError(f"must be at least {MIN_SECRET_LENGTH} characters (generate: openssl rand -hex 32)")
        return value

    @field_validator("INTERNAL_TOKEN")
    @classmethod
    def _internal_token_length(cls, value: SecretStr | None) -> SecretStr | None:
        if value is not None and not value.get_secret_value():
            return None
        if value is not None and len(value.get_secret_value()) < MIN_SECRET_LENGTH:
            raise ValueError(f"must be at least {MIN_SECRET_LENGTH} characters when set")
        return value

    @field_validator(
        "SUPABASE_URL",
        "SUPABASE_JWKS_URL",
        "SUPABASE_JWT_ISSUER",
        "GOOGLE_CLIENT_ID",
        "S3_ENDPOINT_URL",
        "S3_BUCKET",
        "KAFKA_BOOTSTRAP_SERVERS",
        "KAFKA_CLIENT_ID",
        "KAFKA_TOPIC_FILE_EXTRACTION",
        "SMTP_HOST",
        "SMTP_USERNAME",
        "SMTP_FROM_EMAIL",
        "SMTP_FROM_NAME",
        "TOTP_ISSUER",
        "COOKIE_DOMAIN",
        "BOOTSTRAP_ADMIN_EMAIL",
        mode="before",
    )
    @classmethod
    def _blank_to_none(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @field_validator(
        "SUPABASE_DB_URL",
        "SUPABASE_JWT_SECRET",
        "REDIS_URL",
        "REDIS_PASSWORD",
        "GOOGLE_CLIENT_SECRET",
        "BOOTSTRAP_ADMIN_PASSWORD",
        "DATA_ENCRYPTION_KEY",
        "ENC_SECRET",
        "S3_ACCESS_KEY_ID",
        "S3_SECRET_ACCESS_KEY",
        "SMTP_PASSWORD",
        "INTERNAL_TOKEN",
        mode="before",
    )
    @classmethod
    def _blank_secret_to_none(cls, value: Any) -> Any:
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def _cross_field_checks(self) -> Settings:
        errors: list[str] = []
        if self.ENC_ACTIVE:
            if self.ENC_SECRET is None:
                errors.append("BE_ENC_SECRET is required when BE_ENC_ACTIVE=true")
            else:
                try:
                    decode_aes_key(self.ENC_SECRET.get_secret_value())
                except CryptoError as exc:
                    errors.append(f"BE_ENC_SECRET: {exc}")
        if self.DATA_ENCRYPTION_KEY is not None:
            try:
                build_fernet(self.DATA_ENCRYPTION_KEY.get_secret_value())
            except CryptoError as exc:
                errors.append(f"BE_DATA_ENCRYPTION_KEY: {exc}")
        if self.DB_PROVIDER == "supabase" and self.SUPABASE_DB_URL is None:
            errors.append("BE_SUPABASE_DB_URL is required when BE_DB_PROVIDER=supabase")
        if self.AUTH_PROVIDER == "supabase" and not (self.SUPABASE_JWKS_URL or self.SUPABASE_JWT_SECRET):
            errors.append("BE_SUPABASE_JWKS_URL or BE_SUPABASE_JWT_SECRET is required when BE_AUTH_PROVIDER=supabase")
        if self.SUPABASE_DB_POOL_MIN > self.SUPABASE_DB_POOL_MAX:
            errors.append("BE_SUPABASE_DB_POOL_MIN must be <= BE_SUPABASE_DB_POOL_MAX")
        if self.COOKIE_SAMESITE == "none" and not self.COOKIE_SECURE:
            errors.append("BE_COOKIE_SAMESITE=none requires BE_COOKIE_SECURE=true")
        if self.is_production:
            if self.JWT_SECRET.get_secret_value().startswith(PLACEHOLDER_SECRET_PREFIX):
                errors.append("BE_JWT_SECRET still holds the .env.example placeholder")
            if not self.COOKIE_SECURE:
                errors.append("BE_COOKIE_SECURE must be true in production")
            if self.RELOAD:
                errors.append("BE_RELOAD must be false in production")
        if errors:
            raise ValueError("; ".join(errors))
        return self

    # ------------------------------------------------------------ helpers
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def redis_url(self) -> str:
        if self.REDIS_URL is not None:
            return self.REDIS_URL.get_secret_value()
        scheme = "rediss" if self.REDIS_SSL else "redis"
        auth = f":{self.REDIS_PASSWORD.get_secret_value()}@" if self.REDIS_PASSWORD else ""
        return f"{scheme}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    @property
    def google_configured(self) -> bool:
        return bool(self.GOOGLE_CLIENT_ID and self.GOOGLE_CLIENT_SECRET)

    @property
    def smtp_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_FROM_EMAIL)

    @property
    def s3_configured(self) -> bool:
        return bool(self.S3_BUCKET and self.S3_ACCESS_KEY_ID and self.S3_SECRET_ACCESS_KEY)

    @property
    def kafka_configured(self) -> bool:
        return bool(self.KAFKA_BOOTSTRAP_SERVERS)

    @property
    def internal_token_configured(self) -> bool:
        return self.INTERNAL_TOKEN is not None

    @property
    def upload_max_bytes(self) -> int:
        return self.UPLOAD_MAX_SIZE_MB * 1024 * 1024

    @property
    def totp_issuer(self) -> str:
        return self.TOTP_ISSUER or self.APP_NAME

    @property
    def smtp_from_name(self) -> str:
        return self.SMTP_FROM_NAME or self.APP_NAME

    def table_name(self, setting_key: str) -> str:
        """Resolve a configurable table/collection name, e.g. ``table_name("TABLE_USERS")``."""
        return str(getattr(self, setting_key))


def resolve_env_file(name: str | None = None) -> Path | None:
    """Locate the env file named by ``BE_ENV_FILE`` (or ``name``); ``None`` if absent."""
    candidate = Path(name or os.environ.get(f"{ENV_PREFIX}ENV_FILE") or ".env")
    if candidate.is_absolute():
        return candidate if candidate.is_file() else None
    for base in (Path.cwd(), BACKEND_DIR):
        path = base / candidate
        if path.is_file():
            return path
    return None


def load_settings(env_file: str | None = None, **overrides: Any) -> Settings:
    """Build a fresh ``Settings`` from the environment + env file (+ explicit overrides)."""
    path = resolve_env_file(env_file)
    return Settings(_env_file=path, **overrides)  # type: ignore[call-arg]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Process-wide settings, built lazily on first use. ``get_settings.cache_clear()`` in tests."""
    return load_settings()
