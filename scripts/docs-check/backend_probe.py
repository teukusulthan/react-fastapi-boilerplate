"""Backend facts for scripts/docs-check (run with the backend venv, cwd = apps/backend).

Reads a JSON request on stdin::

    {"imports": [{"module": "core.deps", "names": ["UsersRepo"]}, ...]}

and prints one JSON document on stdout::

    {
      "routes": [["GET", "/health/live"], ...],   # every route, all optional routers enabled
      "settings": ["APP_NAME", ...],                # Settings fields (without the BE_ prefix)
      "imports": [{"module": ..., "name": ..., "error": null | "..."}]
    }

It never connects to MongoDB, Redis or Postgres: the app is built with ``create_app()`` and only
its route table is read (the lifespan never runs).
"""

from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[2] / "apps" / "backend"
sys.path.insert(0, str(BACKEND_DIR))

# Isolate from the developer's .env / shell, and enable every optional router.
for _key in [k for k in os.environ if k.startswith("BE_")]:
    del os.environ[_key]
os.environ.update(
    {
        "BE_ENV_FILE": "/nonexistent/.env.docs-check",
        "BE_ENVIRONMENT": "test",
        "BE_JWT_SECRET": "docs-check-only-secret-0123456789abcdef0123456789",
        "BE_AUTH_PROVIDER": "local",
        "BE_GOOGLE_CLIENT_ID": "docs-check.apps.googleusercontent.com",
        "BE_GOOGLE_CLIENT_SECRET": "docs-check-google-secret",
        "BE_DOCS_ENABLED": "false",
        "BE_LOG_LEVEL": "ERROR",
        "BE_ACCESS_LOG": "false",
    }
)

SKIP_METHODS = {"HEAD", "OPTIONS"}


def _routes() -> list[list[str]]:
    """Routes of the real app (``create_app``) with every optional router enabled.

    Two public sources are merged: the OpenAPI schema of the built app (what is served) and the
    ``APIRoute`` entries of every registry router (also catches ``include_in_schema=False``).
    """
    from fastapi.routing import APIRoute

    from core.app_factory import create_app
    from core.config import Settings
    from router import load_router, select_routers

    settings = Settings(_env_file=None)  # type: ignore[call-arg]
    app = create_app(settings)
    out: set[tuple[str, str]] = set()
    for path, operations in app.openapi().get("paths", {}).items():
        for method in operations:
            if method.upper() not in SKIP_METHODS and method != "parameters":
                out.add((method.upper(), path))
    for spec in select_routers(settings):
        for route in load_router(spec).routes:
            if isinstance(route, APIRoute):
                out.update((method, route.path) for method in route.methods - SKIP_METHODS)
    return [list(r) for r in sorted(out, key=lambda r: (r[1], r[0]))]


def _settings_fields() -> list[str]:
    from core.config import Settings

    return sorted(Settings.model_fields)


def _check_import(module: str, name: str) -> str | None:
    try:
        mod = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001  # reported, not raised
        return f"cannot import module {module!r}: {type(exc).__name__}: {exc}"
    if name == "*" or hasattr(mod, name):
        return None
    try:
        importlib.import_module(f"{module}.{name}")
    except ModuleNotFoundError:
        return f"{module!r} has no attribute or submodule {name!r}"
    except Exception as exc:  # noqa: BLE001
        return f"cannot import {module}.{name}: {type(exc).__name__}: {exc}"
    return None


def main() -> int:
    raw = sys.stdin.read()
    request = json.loads(raw) if raw.strip() else {}
    imports = [
        {"module": item["module"], "name": name, "error": _check_import(item["module"], name)}
        for item in request.get("imports", [])
        for name in item["names"]
    ]
    result = {"routes": _routes(), "settings": _settings_fields(), "imports": imports}
    sys.stdout.write(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
