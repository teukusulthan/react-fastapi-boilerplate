# File naming rules (detailed)

Companion to [../SKILL.md](../SKILL.md). Every file named here exists in `apps/backend/` unless it is
marked as an example to create.

## Current modules (pattern source)

| Feature | DTO | Service | Router | Tests |
|---|---|---|---|---|
| user | `dto/user.py` | `service/user.py` | `router/user.py` | `tests/modules/test_users.py` |
| group | `dto/group.py` | `service/group.py` | `router/group.py` | `tests/modules/test_groups_roles.py` |
| role | `dto/role.py` | `service/role.py` | `router/role.py` | `tests/modules/test_groups_roles.py` |
| permission | `dto/permission.py` | `service/permission.py` | `router/permission.py` | `tests/modules/test_permissions.py` |
| upload | `dto/upload.py` | `service/upload.py` | `router/upload.py` | `tests/modules/test_upload.py` |
| auth | `dto/auth.py` | `service/auth/` (package) | `router/auth.py` | `tests/auth/` |
| health | — | — | `router/health.py` | `tests/core/test_app_factory.py` |

Shared: `dto/common.py`, `dto/user_profile.py`, `service/__init__.py` (`CrudService`, `ensure_valid_parent`),
`service/user_profile.py`.

## When a feature outgrows one file

Turn the service into a package like `service/auth/`: one module per concern (`login.py`, `tokens.py`, …),
an `__init__.py` docstring listing them, and a `deps.py` holding the `get_*` providers and `*Dep` aliases.
Keep the router and DTOs as single files unless they exceed ~400 lines.

## Placement decision

| Code | Goes to |
|---|---|
| Request/response models | `dto/` |
| Business rules, orchestration | `service/` |
| HTTP wiring only | `router/` |
| Entity fields / whitelists | `db/schema.py` (or `register_entity` in the feature module) |
| New DB provider | `db/<provider>/` + `db/factory.py` (see `fastapi-database-init`) |
| App-wide dependency, error type, middleware, setting | `core/` |
| Pure helper or thin client for an external system | `util/` |
| One-off CLI task | `scripts/<task>.py`, run as `python -m scripts.<task>` |
| Postgres DDL | `migrations/supabase/NNN_<what>.sql` |

## Forbidden

| Forbidden | Why |
|---|---|
| CamelCase or plural module names | breaks the one-name-per-feature convention |
| Importing `router.*` from services | layering inversion |
| Re-creating `config/`, `models/`, `exceptions/`, `middleware/` packages | replaced by `core/` modules |
| Per-request module-level state | services are built per request via `Depends` |
