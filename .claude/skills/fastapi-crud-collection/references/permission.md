# Reference — `permission` (RBAC catalog with guards and an extra endpoint)

## Files

- `apps/backend/dto/permission.py` — `PermissionDTO`, `UpdatePermissionDTO`, `UpdatePrivilegesDTO`,
  `FindPermissionDTO(FindDTO)`, `PermissionResponse`
- `apps/backend/service/permission.py` — `PermissionService(CrudService)`, `PermissionServiceDep`
- `apps/backend/router/permission.py`
- Entity: `PERMISSIONS` in `apps/backend/db/schema.py`
- Tests: `apps/backend/tests/modules/test_permissions.py`
- Web: `apps/web/src/services/permission.service.ts` (CRUD + `updatePrivileges`)

## Endpoints and RBAC

Router-level `Depends(get_current_user)`; writes add `AdminUserDep`.

| Method | Path | Body | Who |
|---|---|---|---|
| POST | `/permission/add` | `{name, alias?, description?, type?, privileges?, parentId?, image?}` → 201 | superuser |
| PUT | `/permission/update` | `{id, …}` PATCH semantics (`name`, `privileges` reject `null`) | superuser |
| PUT | `/permission/update-partial` | `{id, addPrivileges?: [], removePrivileges?: []}` | superuser |
| DELETE | `/permission/delete?id=` | — | superuser |
| GET | `/permission/get-one?id=` | — | any authenticated principal |
| POST | `/permission/get-all` | `FindPermissionDTO` | any authenticated principal |

## Fields and whitelists (`PERMISSIONS`)

`name` (fso), `alias` (fso, **unique**, nullable; lowercased, `^[a-z0-9_-]+$`), `description` (s),
`type` (f), `privileges` (LIST, f — `is` = contains, `is one of` = contains any, `all` = contains all),
`parent_id` (f), `image`, audit fields.

## Domain rules

- `alias` is what a user's `role` resolves to; aliases in `BE_SUPERUSER_ALIASES` (default
  `admin,owner`) make superusers. `privileges` are strings checked by
  `core.deps.require_privilege("x:y")`; the seeded `admin` permission has `["*"]`
  (`apps/backend/scripts/seed.py`).
- Alias uniqueness pre-checked (`_check_alias_free`) for a friendly 409; the unique index /
  constraint is the real guarantee.
- Lockout guard: renaming a superuser alias to a non-superuser alias → 409 if the caller holds that
  permission or no other active superuser would remain (`superuser_permission_ids`,
  `count_active_superusers` from `service/user.py`).
- Privileges are de-duplicated; `update-partial` removes first, then appends new ones.
- Delete: 409 while any user has `permission_id = id`; children's `parent_id` set to null.
