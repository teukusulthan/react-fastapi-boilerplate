"""Router registry — the ONLY place routers are wired into the app.

Each :class:`RouterSpec` names a module + attribute holding an ``APIRouter``.
Modules are imported lazily by ``include_routers`` (at app build time), in order.

Toggling: ``BE_ENABLED_ROUTERS`` is a comma list of exact names (empty = all).
Unknown names are a startup error. ``health`` is always mounted.

Strictness: a registered router that fails to import (or lacks the attribute)
fails app creation loudly. To build an app with a subset (tests, tools) pass
``routers=`` to ``create_app`` — e.g. ``create_app(settings, routers=[HEALTH])``.

Auth module contract (``router/auth.py``):
  * ``router``        — always mounted: ``/auth/me``, ``/auth/logout``, ``/auth/refresh``…
  * ``local_router``  — only when ``BE_AUTH_PROVIDER=local`` (login/register/OTP/2FA/passwords)
  * ``google_router`` — only when local auth AND Google OAuth is configured
"""

from __future__ import annotations

import importlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from fastapi import APIRouter
from loguru import logger

if TYPE_CHECKING:
    from fastapi import FastAPI

    from core.config import Settings


def _always(_: Settings) -> bool:
    return True


def _local_auth(settings: Settings) -> bool:
    return settings.AUTH_PROVIDER == "local"


def _google_auth(settings: Settings) -> bool:
    return settings.AUTH_PROVIDER == "local" and settings.google_configured


@dataclass(frozen=True)
class RouterSpec:
    name: str  # toggle name used in BE_ENABLED_ROUTERS
    module: str  # dotted module path
    attr: str = "router"
    enabled: Callable[[Settings], bool] = field(default=_always, compare=False)
    toggleable: bool = True  # False = always mounted (health)


HEALTH = RouterSpec("health", "router.health", toggleable=False)

ROUTERS: tuple[RouterSpec, ...] = (
    HEALTH,
    RouterSpec("auth", "router.auth"),
    RouterSpec("auth", "router.auth", attr="local_router", enabled=_local_auth),
    RouterSpec("auth", "router.auth", attr="google_router", enabled=_google_auth),
    RouterSpec("user", "router.user"),
    RouterSpec("group", "router.group"),
    RouterSpec("permission", "router.permission"),
    RouterSpec("role", "router.role"),
    RouterSpec("upload", "router.upload"),
)


def select_routers(settings: Settings, registry: Sequence[RouterSpec] = ROUTERS) -> list[RouterSpec]:
    wanted = set(settings.ENABLED_ROUTERS)
    known = {spec.name for spec in registry}
    unknown = sorted(wanted - known)
    if unknown:
        raise ValueError(
            f"Unknown router(s) in BE_ENABLED_ROUTERS: {', '.join(unknown)} (known: {', '.join(sorted(known))})"
        )
    return [
        spec
        for spec in registry
        if (not spec.toggleable or not wanted or spec.name in wanted) and spec.enabled(settings)
    ]


def load_router(spec: RouterSpec) -> APIRouter:
    module = importlib.import_module(spec.module)
    router = getattr(module, spec.attr, None)
    if not isinstance(router, APIRouter):
        raise ImportError(f"{spec.module}.{spec.attr} is missing or is not an APIRouter")
    return router


def include_routers(app: FastAPI, settings: Settings, registry: Sequence[RouterSpec] | None = None) -> list[RouterSpec]:
    mounted = select_routers(settings, ROUTERS if registry is None else registry)
    for spec in mounted:
        app.include_router(load_router(spec))
        logger.debug("Mounted router {}.{}", spec.module, spec.attr)
    return mounted
