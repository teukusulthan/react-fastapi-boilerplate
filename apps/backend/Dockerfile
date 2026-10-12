# syntax=docker/dockerfile:1
# Production image for apps/backend (FastAPI on :8020).
#
#   docker build -t app-backend apps/backend
#   docker run --rm -p 8020:8020 --env-file apps/backend/.env app-backend
#
# Runtime tuning via env: WEB_CONCURRENCY (uvicorn workers, default 1). Client IPs behind
# a reverse proxy are resolved by the app (BE_TRUST_PROXY_HEADERS / BE_PROXY_TRUSTED_HOPS),
# so uvicorn's own proxy-header rewriting is off; the app also writes the access log.

ARG PYTHON_VERSION=3.12

# ---------------------------------------------------------------------------- build
FROM python:${PYTHON_VERSION}-slim AS build

COPY --from=ghcr.io/astral-sh/uv:0.12 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

RUN uv venv /opt/venv
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --python /opt/venv/bin/python -r /tmp/requirements.txt

# -------------------------------------------------------------------------- runtime
FROM python:${PYTHON_VERSION}-slim AS runtime

# libmagic1: required by python-magic (upload MIME sniffing).
RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --no-create-home --shell /usr/sbin/nologin app

ENV PATH=/opt/venv/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

COPY --from=build /opt/venv /opt/venv

WORKDIR /app
# Code stays root-owned (read-only for the app user).
COPY . .

USER app
EXPOSE 8020

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8020/health/live', timeout=4).status == 200 else 1)"]

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8020", "--no-access-log", "--no-proxy-headers"]
