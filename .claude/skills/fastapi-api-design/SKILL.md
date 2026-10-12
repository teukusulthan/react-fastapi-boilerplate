---
name: api-design
description: "Backend (apps/backend) FastAPI API conventions: RPC-style routes (POST /x/add, PUT /x/update, DELETE /x/delete?id=, GET /x/get-one?id=, POST /x/get-all), ApiResponse envelope via ok()/created()/paginated(), AppError hierarchy + errorCode values, camelCase BaseSchema DTOs, FindDTO/FilterItem list queries, PATCH semantics with to_storage(exclude_unset=True), RBAC deps on routers, router registry (RouterSpec/BE_ENABLED_ROUTERS), optional AES-GCM payload encryption (BE_ENC_ACTIVE). Use when adding or changing endpoints, DTOs, response/error shapes or module boundaries."
---

# api-design — HTTP contract of the backend

## Use this skill when

- Adding a router/endpoint or changing a request/response shape in `apps/backend`
- Designing DTOs (create / update / list-query / response models)
- Deciding status codes, error codes or pagination
- Registering a router or toggling it per deployment

Related: data access → `fastapi-data`; a whole new resource → `fastapi-crud-collection`;
auth/RBAC → `fastapi-auth`; settings → `fastapi-config`; tests → `fastapi-unit-test`.

## Reference implementation (copy these)

| Layer | File | What to copy |
|---|---|---|
| Router | `apps/backend/router/group.py` | prefix/tags, router-wide auth dep, five CRUD routes |
| DTOs | `apps/backend/dto/group.py` | `GroupDTO` (create), `UpdateGroupDTO` (patch), `FindGroupDTO`, `GroupResponse` |
| Service | `apps/backend/service/group.py` | `CrudService` subclass + `get_group_service` + `GroupServiceDep` |
| Envelope | `apps/backend/core/responses.py` | `ApiResponse[T]`, `ok`, `created`, `paginated` |
| Errors | `apps/backend/core/errors.py` | `AppError` subclasses, `ErrorCode` |
| Shared DTOs | `apps/backend/dto/common.py` | `BaseSchema`, `FindDTO`, `FilterItem`, `IdParam`, `MessageData` |
| Registry | `apps/backend/router/__init__.py` | `RouterSpec`, `ROUTERS` |

## Rules

### MUST

- Use the house RPC style (one prefix per module, kebab-case verbs):

  | Verb | Route | Input | Success |
  |---|---|---|---|
  | create | `POST /x/add` | DTO body | **201** + `created(record)` |
  | update | `PUT /x/update` | DTO body incl. `id` | 200 + `ok(record, message="Updated")` |
  | delete | `DELETE /x/delete?id=` | `id: IdParam` | 200 + `ok(MessageData(message="X deleted"))` |
  | one | `GET /x/get-one?id=` | `id: IdParam` | 200 + `ok(record)` |
  | list | `POST /x/get-all` | `FindXDTO` body | 200 + `paginated(items, q.page, q.size, total)` |

  Extra actions follow the same style: `POST /user/reset-password`, `PUT /permission/update-partial`,
  `GET /user/check-email?email=`, `GET /user/get-by-username?username=`.
- Declare `response_model=ApiResponse[XResponse]` (or `ApiResponse[list[XResponse]]`) on **every** route.
  FastAPI re-validates the envelope through it: storage dicts (snake_case, may contain `password_hash`)
  come out camelCase with unknown fields dropped. This is the safety net — never skip it.
- Return `ok()` / `created()` / `paginated()`; for 201 also set `status_code=201` on the decorator.
- Signal failures by **raising** `core.errors` classes; global handlers render the error envelope.
- Inherit every DTO from `dto.common.BaseSchema` (snake_case attributes, camelCase JSON, accepts both).
  Request DTOs use `model_config = ConfigDict(extra="forbid")` (unknown/mass-assignment fields → 422).
- Separate models for create (`XDTO`), update (`UpdateXDTO`, all optional except `id`), list
  (`class FindXDTO(FindDTO): pass`) and output (`XResponse`).
- Update = PATCH semantics: `dto.to_storage(exclude_unset=True, exclude={"id"})` sends only fields the
  client set; an explicit `null` clears an optional field. Reject `null` for required fields with a
  `field_validator(..., mode="before")` (see `_not_null` in `dto/group.py`).
- Create = `dto.to_storage(exclude_unset=False)` so defaults are stored.
- Protect routes with deps from `core/deps.py`: router-wide `dependencies=[Depends(require_auth)]`
  (or `get_current_user` if internal-token callers may read), and per-route `AdminUserDep`,
  `CurrentUserDep`, `require_privilege("x:write")`.
- `created_by` comes from the principal (`actor_id=user.id`), never from the body.
- Register the router in `router/__init__.py` → `ROUTERS` (`RouterSpec("note", "router.note")`).
- Keep routes sync `def` (repositories are blocking; FastAPI runs `def` in the threadpool).

### MUST NOT

- No `HTTPException(400, str(e))`, no `try/except Exception` around service calls, no exception text in messages.
- No raw dict responses, no `copyright` field, no `detail` wrapper on errors.
- No path params for ids (`/x/delete/{id}`), no `GET /x/get-all`, no `/x/{username}` catch-alls.
- No accepting `id`, `createdBy`, `createdAt`, `updatedAt`, `role`, `permissionId` etc. in self-service DTOs.
- No business logic or DB calls in routers or DTO validators (validators must be pure).
- No manual encryption/decryption in handlers.

## Envelope (produced by `core/responses.py` + `core/errors.py`)

```json
{"metaData":{"status":true,"responseCode":200,"message":"Success","executionTime":5,"requestId":"…","pagination":null},"data":{}}
```
List: `metaData.pagination = {"page":1,"size":10,"totalElements":42,"totalPages":5}`, `data` is an array.
Error (all 4xx/5xx, top level):
```json
{"metaData":{"status":false,"responseCode":404,"message":"User not found","errorCode":"RESOURCE_NOT_FOUND","executionTime":3,"requestId":"…"},"data":null}
```
422: `data = [{"field": "filters[0].field", "message": "…"}]` (camelCase field paths). 500 message is always
`"Internal server error"`. Every response has an `X-Request-ID` header.

| Raise | Status | `errorCode` |
|---|---|---|
| `BadRequestError` | 400 | `BAD_REQUEST` |
| `AuthenticationError` | 401 | `AUTHENTICATION_ERROR` (`ACCOUNT_NOT_VERIFIED` on login only) |
| `PermissionDeniedError` | 403 | `PERMISSION_ERROR` |
| `NotFoundError` | 404 | `RESOURCE_NOT_FOUND` |
| (framework) | 405 / 413 / 415 | `METHOD_NOT_ALLOWED` / `PAYLOAD_TOO_LARGE` / `UNSUPPORTED_MEDIA_TYPE` |
| `ConflictError` | 409 | `CONFLICT` (repositories raise it on unique violations) |
| `ValidationError` / `ValidationError.for_field(f, msg)` | 422 | `VALIDATION_ERROR` (not pydantic's class) |
| `RateLimitedError(retry_after=s)` | 429 | `RATE_LIMITED` + `Retry-After` |
| `ConfigurationError` | 503 | `CONFIGURATION_ERROR` (SMTP/S3/Kafka/Google not configured) |
| `ServiceUnavailableError` | 503 | `SERVICE_UNAVAILABLE` (also automatic for Mongo/Postgres/Redis outages) |
| `AppError(msg, status_code=, error_code=, details=)` | any | custom |

## Canonical router (from `router/group.py`)

```python
router = APIRouter(prefix="/group", tags=["group"], dependencies=[Depends(get_current_user)])

@router.post("/add", status_code=201, response_model=ApiResponse[GroupResponse])
def add(dto: GroupDTO, service: GroupServiceDep, admin: AdminUserDep):
    return created(service.create(dto.to_storage(exclude_unset=False), actor_id=admin.id))

@router.put("/update", response_model=ApiResponse[GroupResponse])
def update(dto: UpdateGroupDTO, service: GroupServiceDep, _: AdminUserDep):
    return ok(service.update(dto.id, dto.to_storage(exclude_unset=True, exclude={"id"})), message="Updated")

@router.post("/get-all", response_model=ApiResponse[list[GroupResponse]])
def get_all(query: FindGroupDTO, service: GroupServiceDep):
    items, total = service.list(query)
    return paginated(items, query.page, query.size, total)
```

## List query contract (`FindDTO` in `dto/common.py`)

`{page>=1 (1), size 1..BE_MAX_PAGE_SIZE (10), search?, searchBy?: [field], orderBy? (createdAt), order: asc|desc (desc), filters?: [FilterItem]}` — `search_by` is accepted too.
`FilterItem = {field, operator, value: {is?, isOneOf?, gte?, lte?}, operatorType?: "and"|"or"}`.
Operators: `is`, `is not`, `is one of`, `is not one of`, `greater than equals`, `less than equals`,
`is between`, `is not between`, `is exist`, `is not exist`, `is contains`, `is not contains`, `all` (list fields).
Whitelists live on the entity in `db/schema.py` (`filterable`/`searchable`/`sortable` flags); unknown or
sensitive fields → one 422 listing every bad field. Search is a literal, case-insensitive contains.
Translation: `db/query.py::build_query_spec` (called by `CrudService.list`).

## Optional payload encryption

`BE_ENC_ACTIVE=true` + `BE_ENC_SECRET` (base64 32 bytes) installs `PayloadEncryptionMiddleware`
(`core/middleware.py`, pure ASGI, AES-256-GCM). JSON request bodies arrive as `{"payload": "<b64 nonce|ciphertext|tag>"}`
and JSON responses leave the same way; `/health`, `/docs`, `/redoc`, `/openapi.json` and non-JSON (multipart)
bodies are exempt. Handlers never see or produce ciphertext.

## Checklist — new endpoint

1. DTO(s) in `dto/<module>.py` extending `BaseSchema` (`extra="forbid"` on requests) + `XResponse`.
2. Service method (business rules, raises `AppError`s) — see `fastapi-data`.
3. Route: correct verb/path, `response_model=ApiResponse[...]`, `status_code=201` for creates, auth dep.
4. New module → add `RouterSpec` to `router/__init__.py`; name it in `BE_ENABLED_ROUTERS` docs if toggled.
5. Tests in `tests/modules/` (success, 401/403, 404, 409, 422) — see `fastapi-unit-test`.
6. `npm run lint && npm run test` (or `.venv/bin/ruff check . && .venv/bin/python -m pytest` in `apps/backend`).
7. Web side: add the endpoint constant/service in `apps/web/src/services/` (see `reactjs-service`).

## Common mistakes

| Mistake | Fix |
|---|---|
| Route without `response_model` returns `password_hash` / snake_case keys | Always `response_model=ApiResponse[...]` |
| `created()` but decorator lacks `status_code=201` | HTTP status stays 200 — set both |
| Update DTO dumped with `exclude_unset=False` | Wipes fields the client didn't send |
| Raising pydantic `ValidationError` | Use `core.errors.ValidationError.for_field(...)` |
| Error message built from `str(exc)` | Fixed, safe message; log the exception |
| `async def` route calling a service | Use `def` (see `fastapi-async-performance`) |
| Forgot `RouterSpec` | Router never mounted (404) |

Detailed rules and the full route/DTO templates: [references/api-rules.md](references/api-rules.md)
