# Command: /generate-api

Generates a complete backend API endpoint (Rust or Python).

## Trigger
`/generate-api [resource_name]`

## Execution Steps
1. `<thinking>` Analyze the `[resource_name]`. In this repo the backend is Python/FastAPI at `apps/backend/` (read `apps/backend/AI_GUIDE.md` first; copy the `role` module).
2. Outline the endpoints in the house style (`POST /x/add`, `PUT /x/update`, `DELETE /x/delete?id=`, `GET /x/get-one?id=`, `POST /x/get-all`) and the payload schema; decide RBAC per endpoint.
3. Apply the backend constraints in `.claude/rules/architecture.md` § Backend Enforcement.
4. Declare the entity in `db/schema.py` (+ `TABLE_*` setting in `core/config.py` and `.env.example`) and add `migrations/supabase/NNN_<x>.sql`.
5. Generate the DTOs (`dto/<x>.py`: create / update / `Find<X>DTO(FindDTO)` / response).
6. Generate the Service layer (`service/<x>.py`: `CrudService` subclass + `Depends` provider).
7. Generate the Router (`router/<x>.py`, every route with `response_model=ApiResponse[...]`) and register it in `router/__init__.py` (`RouterSpec`).
8. Add tests (`tests/modules/test_<x>.py`), update `docs/api-spec.md`, `docs/api/<x>.md`, `docs/database-schema.md`, `changelog/backend.md`, then run `ruff check .`, `ruff format --check .`, `pytest`.

Full recipe: `apps/backend/AI_GUIDE.md` §5.1.

## Output Format
Deliver the required boilerplate code neatly organized by file path. Do not skip error handling or type definitions.
