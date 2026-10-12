"""Per-request context (request id + start time) stored in contextvars.

Set by :class:`core.middleware.RequestContextMiddleware`; read by the response
envelope helpers. Context vars propagate into FastAPI's threadpool, so sync
routes/services see the same values.
"""

from __future__ import annotations

import time
from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)
_started_at: ContextVar[float | None] = ContextVar("request_started_at", default=None)
_max_page_size: ContextVar[int | None] = ContextVar("max_page_size", default=None)


def set_request_context(request_id: str, started_at: float | None = None) -> tuple[object, object]:
    """Bind the context for the current request; returns tokens for :func:`reset_request_context`."""
    return (
        _request_id.set(request_id),
        _started_at.set(time.perf_counter() if started_at is None else started_at),
    )


def reset_request_context(tokens: tuple[object, object]) -> None:
    rid_token, start_token = tokens
    _request_id.reset(rid_token)  # type: ignore[arg-type]
    _started_at.reset(start_token)  # type: ignore[arg-type]


def get_request_id() -> str | None:
    return _request_id.get()


def get_execution_time_ms() -> int:
    """Milliseconds since the request started (0 outside a request)."""
    started = _started_at.get()
    if started is None:
        return 0
    return int((time.perf_counter() - started) * 1000)


def set_max_page_size(limit: int) -> object:
    """Bind the serving app's ``MAX_PAGE_SIZE`` for the current request; returns a reset token."""
    return _max_page_size.set(limit)


def reset_max_page_size(token: object) -> None:
    _max_page_size.reset(token)  # type: ignore[arg-type]


def get_max_page_size() -> int | None:
    """``MAX_PAGE_SIZE`` of the app serving this request (``None`` outside a request)."""
    return _max_page_size.get()
