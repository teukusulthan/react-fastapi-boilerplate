# Command: /sync-types

Synchronizes data models across the Fullstack ecosystem. Given a backend response/schema, generates TypeScript Interfaces (FE) and Dart Models (Mobile).

## Trigger
`/sync-types` or `/sync-types [Backend File or JSON target]`

## Execution Steps
1. `<thinking>` Analyze the source JSON payload, Rust Struct, or Python Pydantic Model.
2. Identify data types (Strings, Ints, Dates, Nullables, Arrays).
3. Generate standard TypeScript interface/types for the ReactJS application.
4. Generate equivalent Dart classes using `json_serializable` or `freezed` mappings for the Flutter application.

## Sources and targets in this repo
- Source of truth: backend DTOs in `apps/backend/dto/*.py` (`BaseSchema` → JSON is **camelCase**; responses are wrapped in `{metaData, data}`), documented in `docs/api-spec.md` / `docs/api/*.md`. The live schema is `/openapi.json`.
- Web target: `apps/web/src/types/models.d.ts` (response models) and the payload interfaces in `apps/web/src/services/<module>.service.ts`; envelope/list types are already in `apps/web/src/types/api.d.ts` — do not redefine them.
- Mobile target: only if a Flutter app exists under `apps/` (none in this boilerplate).

## Output Format
Provide the TS and Dart code cleanly. Point out any potentially dangerous nullable mismatches.
