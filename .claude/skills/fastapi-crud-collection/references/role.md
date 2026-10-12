# Reference — `role` (minimal CRUD module)

The smallest complete resource in the backend. Copy this shape for a new resource
(see the recipe in `../SKILL.md`).

## Files

- `apps/backend/dto/role.py` — `RoleDTO` (create, `extra="forbid"`), `UpdateRoleDTO` (`id` + optional
  fields, `name` rejects explicit `null`), `FindRoleDTO(FindDTO)`, `RoleResponse`
- `apps/backend/service/role.py` — `RoleService(CrudService)`, `get_role_service`, `RoleServiceDep`
- `apps/backend/router/role.py` — `router = APIRouter(prefix="/role", tags=["role"], dependencies=[Depends(get_current_user)])`
- Entity: `ROLES` in `apps/backend/db/schema.py`; table `roles` in `apps/backend/migrations/supabase/001_init.sql`
- Tests: `apps/backend/tests/modules/test_groups_roles.py` (parametrized over group + role), RBAC rows in
  `apps/backend/tests/modules/test_rbac.py`
- Web: `apps/web/src/services/role.service.ts` (no admin page yet)

## Endpoints and RBAC

| Method | Path | Body / query | Who |
|---|---|---|---|
| POST | `/role/add` | `RoleDTO` → 201 | superuser (`AdminUserDep`) |
| PUT | `/role/update` | `UpdateRoleDTO` (PATCH semantics) | superuser |
| DELETE | `/role/delete?id=` | — | superuser |
| GET | `/role/get-one?id=` | — | any authenticated principal (user or `X-Internal-Token`) |
| POST | `/role/get-all` | `FindRoleDTO` | any authenticated principal |

## Fields and whitelists (`ROLES`)

`name` (required; filter/search/sort), `alias` (filter/search/sort; not unique), `description`
(search), `role_position` int (filter/sort), `type` (filter), `parent_id` (filter),
`workspace_id`, `organization_id` (filter; free-form external refs), audit fields.

## Domain rules

- `parent_id` validated with `service.ensure_valid_parent` (422: not found / own parent / cycle /
  too deep) on create and update.
- Delete: children get `parent_id = null` (`repo.update_many`) then the role is deleted — same
  result as the Postgres FK `on delete set null`.
- Roles are a catalog only: nothing in auth reads them. Authorization uses **permissions**
  (`users.permission_id` → `permissions.alias/privileges`).
