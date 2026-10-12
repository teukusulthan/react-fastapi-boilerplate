"""Loguru configuration (call :func:`setup_logging` once, from the app factory).

* ``{}``-style formatting only: ``logger.info("user {} created", user_id)``.
* Every record carries ``extra.request_id`` (bound by the request middleware).
* stdlib logging (uvicorn, pymongo, psycopg, botocore…) is routed into loguru.
* ``BE_LOG_JSON=true`` emits one JSON object per line (for log shippers).
"""

from __future__ import annotations

import inspect
import logging
import sys
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from core.config import Settings

_TEXT_FORMAT = (
    "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | "
    "<magenta>{extra[request_id]}</magenta> | <cyan>{name}:{line}</cyan> - <level>{message}</level>"
)

# Chatty third-party loggers capped at WARNING.
_NOISY_LOGGERS = (
    "httpx",
    "httpcore",
    "pymongo",
    "botocore",
    "boto3",
    "s3transfer",
    "urllib3",
    "kafka",
    "psycopg.pool",
    "watchfiles",
)


class InterceptHandler(logging.Handler):
    """Forward stdlib ``logging`` records to loguru."""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
        frame, depth = inspect.currentframe(), 0
        while frame is not None and (depth == 0 or frame.f_code.co_filename == logging.__file__):
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(settings: Settings) -> None:
    """(Re)configure loguru sinks. Idempotent."""
    logger.remove()
    logger.configure(extra={"request_id": "-"})
    if settings.LOG_JSON:
        logger.add(sys.stderr, level=settings.LOG_LEVEL, serialize=True, backtrace=False, diagnose=False)
    else:
        logger.add(
            sys.stderr,
            level=settings.LOG_LEVEL,
            format=_TEXT_FORMAT,
            backtrace=False,
            diagnose=not settings.is_production,
        )

    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    for name in ("uvicorn", "uvicorn.error", "fastapi"):
        std = logging.getLogger(name)
        std.handlers = [InterceptHandler()]
        std.propagate = False
    # Our middleware writes the access log; silence uvicorn's duplicate.
    access = logging.getLogger("uvicorn.access")
    access.handlers = []
    access.propagate = False
    for name in _NOISY_LOGGERS:
        logging.getLogger(name).setLevel(logging.WARNING)
