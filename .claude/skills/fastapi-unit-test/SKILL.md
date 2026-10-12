---
name: unit-test
description: "Backend (apps/backend) tests with pytest: shared fixtures in tests/conftest.py (make_settings, mongomock-backed database, fakeredis, make_app/app/client, user_factory, admin_headers/user_headers/internal_headers, login), per-package app_routers overrides, tests/modules/conftest.py provider parametrization (Mongo + real Postgres via TEST_POSTGRES_DSN, @pytest.mark.integration), fake S3 via dependency_overrides, MemoryEmailSender outbox for auth flows, pure-function tests (core.security, db.query, DTOs). Use when writing or fixing backend tests or test fixtures."
---

# unit-test — Backend testing (pytest)

## Use this skill when

- Adding tests for a new endpoint/service/helper in `apps/backend`
- Writing RBAC, validation, conflict or envelope assertions
- Running the suite locally or in CI, including the Postgres variant

## Layout & commands

```
apps/backend/tests/
  conftest.py        shared fixtures (no external services: mongomock + fakeredis)
  core/              settings, app factory, errors/envelope, deps, middleware, rate limit, security
  db/                query builder, Mongo repo/translator, Postgres translator + integration
  auth/              auth flows (conftest mounts auth routers + captures email)
  modules/           user/group/permission/role/upload/seed/RBAC (conftest parametrizes providers)
```

| Command | Where |
|---|---|
| `npm run test` | repo root (Nx: backend pytest + web vitest) |
| `npm run ci` | repo root: lint, format-check, typecheck, test, build |
| `.venv/bin/python -m pytest` | `apps/backend` |
| `.venv/bin/python -m pytest tests/modules/test_users.py -k conflict -x` | focused run |
| `TEST_POSTGRES_DSN=postgresql://postgres@127.0.0.1:5432/app_test .venv/bin/python -m pytest -m integration` | Postgres provider (tests apply `migrations/supabase/*.sql` themselves) |
| `.venv/bin/ruff check . && .venv/bin/ruff format --check .` | lint (tests included) |

Config: `apps/backend/pyproject.toml` (`--import-mode=importlib`, `pythonpath=["."]`, marker `integration`).
Test files may share basenames; no `__init__.py` needed. Dev deps: `requirements-dev.txt` (pytest, pytest-cov,
ruff, mongomock, fakeredis).

## Fixtures you get (from `tests/conftest.py`)

| Fixture | Gives |
|---|---|
| `make_settings(**overrides)` / `settings` | `Settings` built without any `.env` (all `BE_*` env vars scrubbed) |
| `database`, `mongo_client`, `redis_client` | `MongoDatabase` on mongomock (indexes ensured), fakeredis |
| `users_repo`, `permissions_repo`, `groups_repo`, `roles_repo`, `uploads_repo` | repositories |
| `app_routers` | routers mounted by `app` (default `[HEALTH]`) — **override it** |
| `make_app(app_settings=None, routers=None)`, `app`, `client` | `create_app(...)` with injected DB/Redis; `TestClient` with lifespan |
| `permission_factory(**f)`, `user_factory(*, password=..., permission=None, **f)` | inserted records (users active + verified) |
| `admin_permission`, `user_permission`, `admin_user`, `regular_user` | seeded principals |
| `login(user)` → `AuthSession(pair, headers, cookies)`, `auth_headers(user)` | issued tokens |
| `admin_headers`, `user_headers`, `internal_headers` | ready-made auth headers |

bcrypt cost is 4 in tests; `get_settings` cache is cleared around each test.

## Canonical API test

```python
# tests/modules/test_notes.py  (example — create it with your module)
import pytest
from router import HEALTH, RouterSpec

@pytest.fixture
def app_routers():
    return [HEALTH, RouterSpec("note", "router.note")]

def test_note_crud(client, admin_headers, user_headers):
    r = client.post("/note/add", json={"title": "Hello"}, headers=admin_headers)
    assert r.status_code == 201
    body = r.json()
    assert body["metaData"]["responseCode"] == 201 and body["data"]["title"] == "Hello"
    assert client.post("/note/get-all", json={}, headers=user_headers).json()["metaData"]["pagination"]["totalElements"] == 1

def test_rejects_unknown_filter(client, admin_headers):
    r = client.post("/note/get-all", json={"filters": [{"field": "secret", "operator": "is", "value": {"is": "x"}}]},
                    headers=admin_headers)
    assert r.status_code == 422 and r.json()["metaData"]["errorCode"] == "VALIDATION_ERROR"
```

Tests placed in `tests/modules/` automatically run against both providers; put module tests there and override
`app_routers` in the test file (the package conftest mounts the five built-in modules).

## Rules

### MUST
- Assert the envelope: status code, `metaData.status`, `metaData.errorCode` on errors, `data` shape (camelCase keys).
- Cover per endpoint: happy path, 401 (no headers), 403 (wrong role / internal token where users are required),
  404, 409 (duplicates), 422 (bad body, unknown field, bad filter).
- Assert secrets never appear (`passwordHash`, `twoFactorSecret`) — see `tests/auth/helpers.py::assert_no_secrets`.
- Replace external services through `app.dependency_overrides` (fake S3: `with_storage` / `fake_storage` in
  `tests/modules/conftest.py`; email: `outbox` fixture in `tests/auth/conftest.py`).
- Build alternative configurations with `make_settings(...)` + `make_app(...)` (e.g. `AUTH_PROVIDER="supabase"`).
- Mark real-service tests `@pytest.mark.integration` and skip unless `TEST_POSTGRES_DSN` is set.

### MUST NOT
- Don't hit real MongoDB/Redis/S3/SMTP in default tests, don't read `apps/backend/.env`.
- Don't `from conftest import ...` (importlib mode) — use fixtures; `user_factory(password="...")` if you need the password.
- Don't use `get_settings()` to configure an app under test — pass settings to `make_app`.
- No `time.sleep` for token expiry — build tokens with `create_token(..., ttl=...)` or manipulate claims.

## Checklist

- [ ] Test file under the right package (`tests/modules/` for API modules)
- [ ] `app_routers` override mounts your router
- [ ] Success + 401/403/404/409/422 cases; envelope + camelCase asserted
- [ ] Passes on mongo; with `TEST_POSTGRES_DSN` also on postgres
- [ ] `ruff check .` and `ruff format --check .` clean

## Common mistakes

| Mistake | Fix |
|---|---|
| 404 for every route in a new test file | `app_routers` not overridden → your router isn't mounted |
| `assert r.json()["detail"]` | errors are `{"metaData": {...}, "data": ...}` — no `detail` |
| Comparing snake_case keys in responses | API is camelCase (`createdAt`, `totalElements`) |
| Test passes on mongomock, fails on Postgres | don't rely on Mongo-only semantics; ids must be uuids |
| Upload test without storage override | use `fake_storage` (else 503 `CONFIGURATION_ERROR`) |

References: [references/fastapi-testing.md](references/fastapi-testing.md) (API/integration patterns) ·
[references/test-unit.md](references/test-unit.md) (pure-function tests)
