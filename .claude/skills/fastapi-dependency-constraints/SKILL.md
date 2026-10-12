---
name: dependency-constraints
description: "Dependency rules for the backend (apps/backend): pinned direct deps in requirements.txt (runtime) and requirements-dev.txt (-r requirements.txt + pytest/ruff/mongomock/fakeredis), what is already available (FastAPI, pydantic-settings, pymongo, psycopg 3 + pool, redis, PyJWT, bcrypt, cryptography, pyotp, loguru, httpx, boto3, python-magic, pillow, qrcode, kafka-python), how to add one and reinstall with npm run setup:backend. Load when installing libraries or setting up dependencies."
---

# Dependency constraints (backend)

## Use this skill when

- You think a feature needs a new Python package
- Installing/updating backend dependencies or fixing an import error

## Files

| File | Role |
|---|---|
| `apps/backend/requirements.txt` | runtime deps — **direct deps only, pinned `==`** |
| `apps/backend/requirements-dev.txt` | `-r requirements.txt` + pytest, pytest-cov, ruff, mongomock, fakeredis |
| `apps/backend/pyproject.toml` | ruff + pytest config only (no dependency list; `requires-python >= 3.10`) |

## Already available — use these before adding anything

| Need | Package (import) |
|---|---|
| Web/API, validation, settings | `fastapi`, `pydantic[email]`, `pydantic-settings`, `python-multipart`, `uvicorn[standard]` |
| MongoDB / Postgres (Supabase) / Redis | `pymongo`, `psycopg[binary]` + `psycopg-pool`, `redis` (only inside `db/` / `core/redis.py`) |
| JWT, passwords, crypto, TOTP | `PyJWT[crypto]`, `bcrypt`, `cryptography` (AES-GCM, Fernet), `pyotp`, `qrcode` |
| HTTP client | `httpx` (sync `httpx.Client` in `def` code) |
| Logging | `loguru` |
| Files | `boto3` (S3/MinIO/Supabase Storage), `python-magic` (needs system `libmagic1`), `pillow` |
| Messaging | `kafka-python` (lazy, optional) |
| Testing/lint (dev) | `pytest`, `pytest-cov`, `ruff`, `mongomock`, `fakeredis` |

## Rules

### MUST
- Reuse the stack above (e.g. `httpx` not `requests`, `loguru` not `logging` config, `cryptography` not
  `pycryptodome`, `pydantic-settings` not `python-dotenv`).
- If a genuinely new capability needs a package: add it **pinned** (`name==X.Y.Z`, current stable) to
  `requirements.txt` under the matching comment group (dev-only tools → `requirements-dev.txt`), then reinstall
  (`npm run setup:backend`) and run `npm run lint && npm run test`.
- Import optional/heavy integrations lazily inside the function that needs them (pattern: `util/s3.py`,
  `util/kafka.py`, `service/upload.py::detect_mime`) so the app boots without them.
- If the package needs a system library, note it for the backend Dockerfile (`apps/backend/Dockerfile`).
- Keep the architecture's tech stack (`.claude/rules/architecture.md`): no new web framework, ORM, DB driver
  for an unsupported database, or task queue without the user's approval.

### MUST NOT
- No unpinned or range specifiers, no transitive deps listed, no `pip install` without updating the requirements file.
- No global installs; everything goes into `apps/backend/.venv` (see `fastapi-virtual-environment`).
- No ORMs (SQLAlchemy, Beanie, ODMantic…) — data access goes through `db.Repository`.
- No second HTTP client, logging library, settings loader or crypto library.

## Checklist

- [ ] Existing package can't do it (checked the table above)
- [ ] Pinned line added to the right requirements file
- [ ] `npm run setup:backend` (or `uv pip install --python .venv/bin/python -r requirements-dev.txt`) succeeded
- [ ] Lazy import if optional; Dockerfile note if it needs system libs
- [ ] `npm run lint && npm run test` green
