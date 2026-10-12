"""Pure-ASGI middleware (no ``BaseHTTPMiddleware`` — bodies are streamed safely).

* :class:`RequestContextMiddleware` — ``X-Request-ID`` in/out, timing context,
  one access-log line per request, and a last-resort 500 envelope.
* :class:`PayloadEncryptionMiddleware` — optional AES-256-GCM request/response
  encryption (``BE_ENC_ACTIVE``). Request body ``{"payload": "<b64>"}`` is
  decrypted before routing; JSON responses are re-wrapped the same way.
"""

from __future__ import annotations

import json
import re
import time
import uuid
from collections.abc import Iterable

from loguru import logger
from starlette.datastructures import Headers, MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from core.context import reset_max_page_size, reset_request_context, set_max_page_size, set_request_context
from core.errors import ErrorCode, error_response
from util.crypto import CryptoError, aesgcm_decrypt, aesgcm_encrypt

REQUEST_ID_HEADER = "X-Request-ID"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._:-]{1,128}$")
# Paths that never get encrypted / are logged at DEBUG.
DEFAULT_EXEMPT_PREFIXES: tuple[str, ...] = ("/health", "/docs", "/redoc", "/openapi.json")
_BODY_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
MAX_ENCRYPTED_BODY_BYTES = 10 * 1024 * 1024


def _route_path(scope: Scope) -> str:
    path: str = scope.get("path", "")
    root = scope.get("root_path", "")
    if root and path.startswith(root):
        path = path[len(root) :] or "/"
    return path


def is_exempt_path(scope: Scope, prefixes: Iterable[str]) -> bool:
    path = _route_path(scope)
    return any(path == p or path.startswith(p.rstrip("/") + "/") for p in prefixes)


class RequestContextMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        access_log: bool = True,
        quiet_prefixes: Iterable[str] = ("/health",),
        max_page_size: int | None = None,
    ) -> None:
        self.app = app
        self.access_log = access_log
        self.max_page_size = max_page_size
        self.quiet_prefixes = tuple(quiet_prefixes)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = Headers(scope=scope).get(REQUEST_ID_HEADER)
        request_id = incoming if incoming and _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        started = time.perf_counter()
        tokens = set_request_context(request_id, started)
        size_token = set_max_page_size(self.max_page_size) if self.max_page_size is not None else None
        state = {"status": 500, "started": False}

        async def send_wrapper(message: Message) -> None:
            if message["type"] == "http.response.start":
                state["status"] = message["status"]
                state["started"] = True
                MutableHeaders(scope=message)[REQUEST_ID_HEADER] = request_id
            await send(message)

        try:
            with logger.contextualize(request_id=request_id):
                try:
                    await self.app(scope, receive, send_wrapper)
                except Exception as exc:
                    logger.opt(exception=exc).error("Unhandled exception: {}", type(exc).__name__)
                    if state["started"]:
                        raise
                    response = error_response(500, "Internal server error", ErrorCode.INTERNAL_ERROR)
                    await response(scope, receive, send_wrapper)
                finally:
                    if self.access_log:
                        duration_ms = (time.perf_counter() - started) * 1000
                        level = "DEBUG" if is_exempt_path(scope, self.quiet_prefixes) else "INFO"
                        client = scope.get("client")
                        logger.log(
                            level,
                            '{} "{} {}" {} {:.1f}ms',
                            client[0] if client else "-",
                            scope.get("method", "-"),
                            scope.get("path", "-"),
                            state["status"],
                            duration_ms,
                        )
        finally:
            reset_request_context(tokens)
            if size_token is not None:
                reset_max_page_size(size_token)


class PayloadEncryptionMiddleware:
    def __init__(self, app: ASGIApp, *, key: bytes, exempt_prefixes: Iterable[str] = DEFAULT_EXEMPT_PREFIXES) -> None:
        self.app = app
        self.key = key
        self.exempt_prefixes = tuple(exempt_prefixes)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or is_exempt_path(scope, self.exempt_prefixes):
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        content_type = headers.get("content-type", "")
        if scope["method"] in _BODY_METHODS and content_type.startswith("application/json"):
            body, too_large = await _read_body(receive, MAX_ENCRYPTED_BODY_BYTES)
            if too_large:
                await error_response(413, "Request body too large", ErrorCode.PAYLOAD_TOO_LARGE)(scope, receive, send)
                return
            if body.strip():
                try:
                    envelope = json.loads(body)
                    token = envelope["payload"] if isinstance(envelope, dict) else None
                    if not isinstance(token, str):
                        raise CryptoError("missing payload")
                    body = aesgcm_decrypt(self.key, token)
                except (ValueError, KeyError, CryptoError):
                    await error_response(400, "Invalid encrypted payload", ErrorCode.BAD_REQUEST)(scope, receive, send)
                    return
            scope = dict(scope)
            raw_headers = [(k, v) for k, v in scope["headers"] if k.lower() != b"content-length"]
            raw_headers.append((b"content-length", str(len(body)).encode("latin-1")))
            scope["headers"] = raw_headers
            receive = _replay_body(body, receive)

        await self.app(scope, receive, _EncryptingSend(send, self.key))


async def _read_body(receive: Receive, limit: int) -> tuple[bytes, bool]:
    chunks: list[bytes] = []
    size = 0
    more = True
    while more:
        message = await receive()
        if message["type"] == "http.disconnect":
            break
        chunk = message.get("body", b"")
        size += len(chunk)
        if size > limit:
            return b"", True
        chunks.append(chunk)
        more = message.get("more_body", False)
    return b"".join(chunks), False


def _replay_body(body: bytes, receive: Receive) -> Receive:
    sent = False

    async def replay() -> Message:
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": body, "more_body": False}
        return await receive()

    return replay


class _EncryptingSend:
    """Buffers a JSON response and re-emits it as ``{"payload": "<aes-gcm b64>"}``."""

    def __init__(self, send: Send, key: bytes) -> None:
        self.send = send
        self.key = key
        self.start: Message | None = None
        self.encrypt = False
        self.chunks: list[bytes] = []

    async def __call__(self, message: Message) -> None:
        if message["type"] == "http.response.start":
            content_type = Headers(raw=message.get("headers", [])).get("content-type", "")
            self.encrypt = content_type.startswith("application/json")
            if not self.encrypt:
                await self.send(message)
                return
            self.start = message
            return
        if message["type"] != "http.response.body" or not self.encrypt:
            await self.send(message)
            return
        self.chunks.append(message.get("body", b""))
        if message.get("more_body", False):
            return
        plaintext = b"".join(self.chunks)
        body = json.dumps({"payload": aesgcm_encrypt(self.key, plaintext)}).encode("utf-8")
        if self.start is None:  # body without start: protocol violation upstream
            return
        headers = MutableHeaders(scope=self.start)
        headers["content-length"] = str(len(body))
        await self.send(self.start)
        await self.send({"type": "http.response.body", "body": body, "more_body": False})
