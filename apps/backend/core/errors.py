"""Application error hierarchy + global exception handlers.

Raise these anywhere (services, deps, repositories); the handlers registered by
:func:`register_exception_handlers` turn them into the standard error envelope::

    raise NotFoundError("User not found")
    raise ConflictError("Email already registered", details=[{"field": "email", "message": "already exists"}])

Never catch-and-rethrow as HTTPException, and never put exception text from
third-party libraries into ``message`` (it is returned to the client).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.exceptions import HTTPException as StarletteHTTPException

from core.responses import error_payload


class ErrorCode:
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    CONFLICT = "CONFLICT"
    RATE_LIMITED = "RATE_LIMITED"
    BAD_REQUEST = "BAD_REQUEST"
    CONFIGURATION_ERROR = "CONFIGURATION_ERROR"
    SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    PAYLOAD_TOO_LARGE = "PAYLOAD_TOO_LARGE"
    UNSUPPORTED_MEDIA_TYPE = "UNSUPPORTED_MEDIA_TYPE"
    INTERNAL_ERROR = "INTERNAL_ERROR"


class AppError(Exception):
    """Base class: carries HTTP status, machine-readable code, safe message and details."""

    status_code: int = 500
    error_code: str = ErrorCode.INTERNAL_ERROR
    default_message: str = "Internal server error"

    def __init__(
        self,
        message: str | None = None,
        *,
        details: Any = None,
        error_code: str | None = None,
        status_code: int | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        self.message = message or self.default_message
        self.details = details
        if error_code is not None:
            self.error_code = error_code
        if status_code is not None:
            self.status_code = status_code
        self.headers = headers
        super().__init__(self.message)

    def __repr__(self) -> str:
        return f"{type(self).__name__}(status={self.status_code}, code={self.error_code}, message={self.message!r})"


class BadRequestError(AppError):
    status_code = 400
    error_code = ErrorCode.BAD_REQUEST
    default_message = "Bad request"


class AuthenticationError(AppError):
    status_code = 401
    error_code = ErrorCode.AUTHENTICATION_ERROR
    default_message = "Authentication required"

    def __init__(self, message: str | None = None, **kwargs: Any) -> None:
        kwargs.setdefault("headers", {"WWW-Authenticate": "Bearer"})
        super().__init__(message, **kwargs)


class PermissionDeniedError(AppError):
    status_code = 403
    error_code = ErrorCode.PERMISSION_ERROR
    default_message = "You do not have permission to perform this action"


class NotFoundError(AppError):
    status_code = 404
    error_code = ErrorCode.RESOURCE_NOT_FOUND
    default_message = "Resource not found"


class ConflictError(AppError):
    status_code = 409
    error_code = ErrorCode.CONFLICT
    default_message = "Resource already exists"


class ValidationError(AppError):
    """422 — ``details`` should be ``[{"field": ..., "message": ...}]``."""

    status_code = 422
    error_code = ErrorCode.VALIDATION_ERROR
    default_message = "Validation error"

    @classmethod
    def for_field(cls, field: str, message: str) -> ValidationError:
        return cls(message, details=[{"field": field, "message": message}])


class RateLimitedError(AppError):
    status_code = 429
    error_code = ErrorCode.RATE_LIMITED
    default_message = "Too many requests, please try again later"

    def __init__(self, message: str | None = None, *, retry_after: int | None = None, **kwargs: Any) -> None:
        if retry_after is not None:
            kwargs.setdefault("headers", {"Retry-After": str(max(int(retry_after), 1))})
        self.retry_after = retry_after
        super().__init__(message, **kwargs)


class ConfigurationError(AppError):
    """A feature was used that the deployment has not configured (SMTP, S3, …)."""

    status_code = 503
    error_code = ErrorCode.CONFIGURATION_ERROR
    default_message = "This feature is not configured"


class ServiceUnavailableError(AppError):
    """A backing service (database, Redis, …) is unreachable."""

    status_code = 503
    error_code = ErrorCode.SERVICE_UNAVAILABLE
    default_message = "Service temporarily unavailable"


_STATUS_TO_CODE: dict[int, str] = {
    400: ErrorCode.BAD_REQUEST,
    401: ErrorCode.AUTHENTICATION_ERROR,
    403: ErrorCode.PERMISSION_ERROR,
    404: ErrorCode.RESOURCE_NOT_FOUND,
    405: ErrorCode.METHOD_NOT_ALLOWED,
    409: ErrorCode.CONFLICT,
    413: ErrorCode.PAYLOAD_TOO_LARGE,
    415: ErrorCode.UNSUPPORTED_MEDIA_TYPE,
    422: ErrorCode.VALIDATION_ERROR,
    429: ErrorCode.RATE_LIMITED,
    503: ErrorCode.SERVICE_UNAVAILABLE,
}


def error_code_for_status(status_code: int) -> str:
    if status_code in _STATUS_TO_CODE:
        return _STATUS_TO_CODE[status_code]
    return ErrorCode.INTERNAL_ERROR if status_code >= 500 else ErrorCode.BAD_REQUEST


def error_response(
    status_code: int,
    message: str,
    error_code: str,
    data: Any = None,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=error_payload(status_code, message, error_code, data),
        headers=headers,
    )


def format_validation_errors(errors: Any) -> list[dict[str, str]]:
    """Pydantic/FastAPI error list -> ``[{"field": "email", "message": "..."}]``."""
    result: list[dict[str, str]] = []
    for err in errors:
        loc = [str(part) for part in err.get("loc", ())]
        if loc and loc[0] in {"body", "query", "path", "header", "cookie"}:
            loc = loc[1:]
        result.append({"field": ".".join(loc) or "body", "message": str(err.get("msg", "Invalid value"))})
    return result


async def _app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    if exc.status_code >= 500:
        logger.error("{} {}: {}", exc.status_code, exc.error_code, exc.message)
    else:
        logger.debug("{} {}: {}", exc.status_code, exc.error_code, exc.message)
    return error_response(exc.status_code, exc.message, exc.error_code, exc.details, exc.headers)


async def _request_validation_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return error_response(422, "Validation error", ErrorCode.VALIDATION_ERROR, format_validation_errors(exc.errors()))


async def _http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    status_code = exc.status_code
    if isinstance(exc.detail, str) and exc.detail:
        message = exc.detail
    else:
        try:
            message = HTTPStatus(status_code).phrase
        except ValueError:
            message = "Error"
    if status_code >= 500:
        message = "Internal server error"
    headers = dict(exc.headers) if exc.headers else None
    return error_response(status_code, message, error_code_for_status(status_code), None, headers)


async def _unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    logger.opt(exception=exc).error("Unhandled exception: {}", type(exc).__name__)
    return error_response(500, "Internal server error", ErrorCode.INTERNAL_ERROR)


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(AppError, _app_error_handler)  # type: ignore[arg-type]
    app.add_exception_handler(RequestValidationError, _request_validation_handler)  # type: ignore[arg-type]
    app.add_exception_handler(StarletteHTTPException, _http_exception_handler)  # type: ignore[arg-type]
    app.add_exception_handler(Exception, _unhandled_exception_handler)
