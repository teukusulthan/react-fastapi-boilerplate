# API & integration testing patterns

Companion to [../SKILL.md](../SKILL.md). All fixtures referenced exist in `apps/backend/tests/conftest.py`,
`apps/backend/tests/modules/conftest.py` or `apps/backend/tests/auth/conftest.py`.

## Contents
- Mounting routers
- Requests: headers, cookies, query, multipart
- Settings variants
- Overriding dependencies
- Provider parametrization (Mongo + Postgres)
- RBAC matrix

## Mounting routers

```python
from router import HEALTH, ROUTERS, RouterSpec

@pytest.fixture
def app_routers():
    return [HEALTH, *[s for s in ROUTERS if s.name in ("auth", "user")]]   # built-in routers
    # or: [HEALTH, RouterSpec("note", "router.note")]                         # your new module
```

## Requests

```python
client.get("/group/get-one", params={"id": gid}, headers=user_headers)
client.post("/group/get-all", json={"search": "alp", "page": 1, "size": 5}, headers=user_headers)
client.delete("/group/delete", params={"id": gid}, headers=admin_headers)

session = login(regular_user)                       # cookies instead of bearer header
client.cookies.update(session.cookies)
client.get("/auth/me")

client.post("/upload/upload-file", files={"file": ("a.png", png_bytes, "image/png")},
            data={"folder": "reports", "tags": "a,b"}, headers=user_headers)   # needs fake_storage
```

## Settings variants

```python
def test_supabase_mode(make_settings, make_app):
    app = make_app(make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET="x" * 40))
    with TestClient(app) as c:
        assert c.post("/auth/login", json={}).status_code == 404   # local_router not mounted
```

Auth tests use `make_client(make_settings(...))` from `tests/auth/conftest.py`, which also wires the in-memory
email `outbox` (`util.email.MemoryEmailSender`: `.outbox` list, `.last(address, template=)`, `.to(address)`);
read codes with `tests/auth/helpers.py::code_from(outbox.last("jane@example.com"))`.

## Overriding dependencies

```python
from service.upload import get_storage_factory
app.dependency_overrides[get_storage_factory] = lambda: lambda: storage   # what with_storage() does
from service.auth.deps import get_email_sender
app.dependency_overrides[get_email_sender] = lambda: outbox               # what tests/auth/conftest.py does
```

Prefer overriding the narrowest provider (`get_*` in the service module) over monkeypatching internals.

## Provider parametrization

`tests/modules/conftest.py` overrides `database` with params `mongo` and — only when `TEST_POSTGRES_DSN` is set —
`postgres` (marked `integration`). The Postgres DB is migrated once per session (`DROP` + every
`migrations/supabase/*.sql`) and truncated per test. Your module tests in `tests/modules/` inherit this for free;
if you add a table, add it to `APP_TABLES` there and ship its migration.

Repository-level Postgres tests: `tests/db/test_supabase_integration.py` (module-level
`pytestmark = [pytest.mark.integration, pytest.mark.skipif(not DSN, ...)]`).

## RBAC matrix

`tests/modules/test_rbac.py` asserts the expected status for each principal (anonymous, user, admin, internal)
on **every mounted module route** and fails if a route is missing from the matrix — add rows for new routes.

## Assertion helpers worth copying

```python
def details(resp):                      # 422/409 field errors -> {field: message}
    return {d["field"]: d["message"] for d in resp.json()["data"]}
```
