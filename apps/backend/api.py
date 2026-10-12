"""ASGI entrypoint.

    python api.py                      # host/port/workers/reload from BE_* settings
    uvicorn api:app --port 8020 --no-access-log --no-proxy-headers

Client IPs / X-Forwarded-For are handled by the app (``BE_TRUST_PROXY_HEADERS``),
so uvicorn's own proxy-header rewriting is disabled here.
"""

from core.app_factory import create_app
from core.config import get_settings

app = create_app()

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "api:app",
        host=settings.HOST,
        port=settings.PORT,
        workers=settings.WORKERS,
        reload=settings.RELOAD and settings.WORKERS == 1,
        access_log=False,
        proxy_headers=False,
        log_config=None,
    )
