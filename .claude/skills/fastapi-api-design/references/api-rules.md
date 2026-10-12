# API & Architecture Rules (detailed)

Companion to [../SKILL.md](../SKILL.md). Everything here is verified against `apps/backend`.

## 1. Layering (mandatory)

```
router/<module>.py   HTTP only: verb, path, DTO in, envelope out, auth deps
dto/<module>.py      Pydantic models (pure validation, no I/O)
service/<module>.py  business rules; receives repositories via constructor; raises AppError
db/                  provider-agnostic repositories (Mongo or Supabase/Postgres)
core/                settings, errors, envelope, deps/RBAC, security, middleware, logging
util/                stateless helpers + optional clients (s3, kafka, email, crypto)
```

- Routers never import `pymongo`/`psycopg`, never touch `Repository` directly except through a service
  (exception: tiny read-only helpers such as `/auth/me` using `load_user_profile`).
- Services never import FastAPI `Request`/`Response` and never build envelopes.
- Services are built per request by a `Depends` provider (`get_group_service` → `GroupServiceDep`);
  no module-level service instances, no global DB clients.

## 2. Router module contract

```python
# router/<module>.py
router = APIRouter(prefix="/<module>", tags=["<module>"], dependencies=[Depends(require_auth)])
```

- Export an `APIRouter` named `router` (the auth module also exports `local_router` and `google_router`).
- Add `RouterSpec("<module>", "router.<module>")` to `ROUTERS` in `router/__init__.py`.
  `BE_ENABLED_ROUTERS=user,group` mounts exactly those (+ `health`); unknown names or a router that fails
  to import abort startup (strict on purpose). There is no per-endpoint schema gating.
- Choose the router-wide dependency deliberately:
  - `require_auth` — signed-in users only (internal token → 403) — e.g. `router/user.py`, `router/upload.py`
  - `get_current_user` — users **or** `X-Internal-Token` callers — e.g. `router/group.py`, `router/permission.py`
  - nothing — public (e.g. `router/health.py`, `local_router` in `router/auth.py`, which uses rate limits)
- Static routes before parameterised ones (there are no path params in house style anyway).

## 3. DTO rules (`dto/common.py`)

| Need | Use |
|---|---|
| Base class | `BaseSchema` (alias generator `to_camel`, `validate_by_name` + `validate_by_alias`, `serialize_by_alias`) |
| Reject unknown keys | `model_config = ConfigDict(extra="forbid")` on request DTOs |
| Storage dict | `dto.to_storage(exclude_unset=..., exclude={...})` → snake_case |
| `?id=` | `id: IdParam` (`Annotated[str, Query(min_length=1, max_length=64)]`) |
| Simple message payload | `MessageData(message="...")` |
| List body | `class FindXDTO(FindDTO): pass` — never add free-form filters |
| Emails | `EmailStr`, normalised lower-case (see `dto/auth.py::_normalise_email`) |
| Constrained strings | `Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]` (see `dto/group.py`) |

Response models (`XResponse`) list exactly the fields the client may see; storage-only/secret fields are
simply absent, and the route's `response_model` drops them. User-shaped responses come from
`dto/user_profile.py` (`UserProfile`, `UserResponse`) built by `service/user_profile.py`.

## 4. Status codes

200 ok · 201 created (`/add`, `/register`, `/upload/upload-file`) · 400 bad request (e.g. wrong current
password on change-password / 2FA disable — deliberately not 401) · 401 unauthenticated · 403 forbidden ·
404 not found (also used to hide other users' records) · 409 conflict (unique violation, still-referenced
record, lockout guard) · 413/415 upload limits · 422 validation · 429 rate-limited · 503 not configured /
backing service down · 500 internal (generic message).

## 5. Error handling

- Raise from `core.errors`; the handlers from `register_exception_handlers()` (called by
  `core/app_factory.py::create_app`) render the envelope. FastAPI `HTTPException`s are also converted
  (status → `errorCode` via `error_code_for_status`), but prefer the typed classes.
- `details` → envelope `data`; use `[{"field": "<camelCase>", "message": "..."}]`.
- Generic auth errors: `AuthenticationError("Invalid credentials")` for unknown user / wrong password /
  locked account alike (no account enumeration).
- Repositories raise `ConflictError` (409) on unique violations and `ValidationError` (422) on Postgres
  FK/CHECK violations; `ValueError` from a repository means a programming bug (unknown/null field) → 500.

## 6. Templates

Full module recipe (DTO + entity + service + router + test): the `fastapi-crud-collection` skill; real
modules to mirror: `dto/group.py`, `service/group.py`, `router/group.py`.

Owner-scoped list (pattern from `service/upload.py`):

```python
def list_for(self, query: FindDTO, actor: CurrentUser):
    scope = () if actor.is_superuser else (Condition("created_by", Op.EQ, actor.id),)
    return self.list(query, extra_where=scope)
```

Rate-limited public endpoint (pattern from `router/auth.py`):

```python
@local_router.post("/login", response_model=ApiResponse[LoginOutcome],
                   dependencies=[Depends(rate_limit("auth:login"))])
```

## 7. Forbidden patterns

| Forbidden | Instead |
|---|---|
| `except Exception as e: raise HTTPException(400, str(e))` | let `AppError`s propagate |
| Returning `{"data": ...}` dicts by hand | `ok()` / `created()` / `paginated()` |
| `response_model` omitted | `ApiResponse[XResponse]` |
| Accepting `created_by` / `role` / `permissionId` from a self-service body | derive from `CurrentUser`; whitelist DTO fields |
| `GET` list with query-string filters | `POST /x/get-all` + `FindXDTO` |
| `/x/{id}` path params | `?id=` query (`IdParam`) or `id` in the update body |
| `async def` route calling repositories | `def` route |
| Encrypting/decrypting payloads in handlers | `BE_ENC_ACTIVE` middleware does it |
| Changing a response shape silently | update `apps/web/src/types/*.d.ts` + services in the same change |
