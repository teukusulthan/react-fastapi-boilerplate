# React + FastAPI Boilerplate

A production-minded starting point for internal web applications:

- **Backend:** FastAPI (`apps/backend`). JWT auth with httpOnly cookies, refresh rotation, 2FA,
  registration and password reset (or Supabase-issued JWTs instead), RBAC, user/group/permission/role
  CRUD, S3 uploads, health probes, and one JSON envelope for every response.
- **Database:** MongoDB (default) **or** Supabase Postgres, chosen with one setting
  (`BE_DB_PROVIDER`) behind a provider-agnostic repository layer.
- **Web:** React 18 + Vite (`apps/web`). Login with 2FA, email verification, an authenticated shell with
  a config-driven sidebar, an admin user list, TanStack Query and typed API services.
- **Tooling:** Nx task runner, cross-platform setup and dev scripts, Docker Compose, GitLab CI,
  pre-commit, ruff, ESLint, Prettier, pytest and Vitest.
- **AI-agent ready:** `AGENTS.md`, `CLAUDE.md`, `.claude/rules`, `.claude/skills` and
  `.claude/commands` describe how to extend the codebase safely.

## Stack

| Layer | Tech |
|-------|------|
| Backend | Python ≥ 3.10 (3.12 in Docker/CI), FastAPI, Pydantic v2, pydantic-settings, loguru, PyJWT, bcrypt |
| Data | MongoDB (pymongo) or Supabase Postgres (psycopg 3), Redis |
| Auth | Local JWT (`BE_AUTH_PROVIDER=local`) or Supabase JWT (`supabase`), plus `X-Internal-Token` for services |
| Web | React 18, TypeScript 5.9, Vite 7, React Router 7, TanStack Query 5, Zustand 5, React Hook Form + Zod 4, Tailwind CSS v4, shadcn/ui (Radix) |
| Tests / quality | pytest (mongomock, fakeredis), Vitest + Testing Library, ruff, ESLint 9, Prettier |
| Ops | Nx 23, Docker (nginx-unprivileged web image, slim Python image), docker compose, GitLab CI |

## Quick start

Prerequisites: Node ≥ 20.19 (24 recommended), Python ≥ 3.10 ([uv](https://docs.astral.sh/uv/)
recommended), MongoDB and Redis (or Docker), and `libmagic` (`apt install libmagic1` / `brew install libmagic`).

```bash
npm install            # root tooling (Nx)
npm run setup          # backend .venv + deps + apps/backend/.env (random secrets, admin password printed)
                       # web deps + apps/web/env/.env
npm run docker:infra   # optional: MongoDB + Redis in Docker (then set BE_REDIS_PASSWORD, see docker-compose.yml)
npm run seed           # default permissions (admin, user) + bootstrap admin
npm run dev            # backend http://localhost:8020 (Swagger /docs) + web http://localhost:3000
```

Sign in at http://localhost:3000 with `BE_BOOTSTRAP_ADMIN_EMAIL` (default `admin@example.com`) and the
password that `npm run setup` printed (it is also stored in `apps/backend/.env`). In development,
emails (OTP codes, verification links) are printed in the backend log.

## Commands

| Command | What it does |
|---|---|
| `npm run setup` / `setup:backend` / `setup:web` | Install dependencies and create env files (`node scripts/setup.mjs --help` for options) |
| `npm run dev` / `dev:backend` / `dev:web` | Dev servers with prefixed output and clean Ctrl+C |
| `npm run seed` | Idempotent seed: permissions `admin`/`user` + bootstrap admin |
| `npm run lint` · `format` · `format:check` · `typecheck` · `test` · `build` | Nx run-many over both apps |
| `npm run ci` | The full quality gate: lint, format-check, typecheck, test and build for both apps |
| `npm run docker:up` · `docker:down` · `docker:logs` | Full stack in Docker: http://localhost:8080 |
| `npm run docker:infra` | Only MongoDB + Redis (for host development) |
| `DB_PROVIDER=supabase docker compose --profile postgres up -d --build` | Full stack on Postgres (the migrations are applied automatically) |

Per-app commands (pytest options, Postgres integration tests, vitest) are in
[`apps/backend/README.md`](apps/backend/README.md) and [`apps/web/README.md`](apps/web/README.md).

## Project layout

```
.
├── apps/
│   ├── backend/        FastAPI app — see apps/backend/README.md and AI_GUIDE.md
│   └── web/            React SPA — see apps/web/README.md and AI_GUIDE.md
├── docs/               api-spec.md (endpoint registry), api/*.md, database-schema.md, mock-data.md
├── changelog/          per-stack changelogs (newest first)
├── sprint/             sprint planning (backlog/active/archive), managed by the sprint-builder skill
├── brief/, mockup/     outputs of the brief / HTML-mockup skills (empty here)
├── data/               source mock datasets
├── scripts/            setup.mjs, dev.mjs, py.mjs, web-tool.mjs, docker/postgres/*
├── .claude/            rules/, skills/, commands/ for AI agents
├── AGENTS.md           master guide for AI agents (and humans)
├── CLAUDE.md           Claude Code entry point (imports AGENTS.md)
├── docker-compose.yml  mongo, redis, postgres (profile), backend, web
├── .gitlab-ci.yml      lint → test (+ Postgres) → build (+ Docker images)
├── nx.json, package.json
└── .pre-commit-config.yaml
```

## How it fits together

- The web app calls `/api/v1/apps/*`. The Vite dev server (and nginx in Docker) strips the prefix and
  forwards to the backend on :8020, so the browser sees a single origin and httpOnly cookies work
  without CORS tricks.
- Every backend response is `{"metaData": {...}, "data": ...}`, and errors carry
  `metaData.errorCode`. See [`docs/api-spec.md`](docs/api-spec.md).
- Authorization: each user has a permission whose `alias` is the user's role (`admin` and `owner` are
  superusers) and whose `privileges` are checked by the API.

## Docker

```bash
npm run docker:up          # builds and starts mongo, redis, backend, web
open http://localhost:8080 # web (API proxied at /api/v1/apps/); backend also on 127.0.0.1:8020
```

The backend reads `apps/backend/.env` (create it with `npm run setup:backend`). Compose overrides the
datastore settings. Compose knobs (`WEB_PORT`, `BACKEND_PORT`, `REDIS_PASSWORD`, `DB_PROVIDER`,
`PUBLIC_WEB_URL`, …) are documented at the top of `docker-compose.yml`. Over plain HTTP, keep
`BE_COOKIE_SECURE=false`.

## CI

GitLab CI (`.gitlab-ci.yml`) has these jobs:
- `backend:lint` (ruff check + format check), `backend:test` (pytest), `backend:test-postgres` (pytest
  `-m integration` against `postgres:16-alpine`);
- `web:lint` (typecheck, ESLint, Prettier), `web:test` (Vitest), `web:build`;
- `docker:build` (default branch and tags; images are pushed when registry credentials exist).

## Working with AI agents

Start with [`AGENTS.md`](AGENTS.md): the repo map, architecture, recipes (new resource, endpoint,
setting, page, service), testing, the definition of done, and pitfalls. Claude Code loads
[`CLAUDE.md`](CLAUDE.md) automatically. Project rules are in [`.claude/rules/`](.claude/rules/), on-demand
skills in [`.claude/skills/`](.claude/skills/), and slash commands in [`.claude/commands/`](.claude/commands/).

This repository is the **already-scaffolded** web + backend part of a larger agent-driven workflow
(brief → spec → design → sprint → build). The scaffold tooling itself (the `.ai/` CLI, boilerplate
packs, design-system packs, the scaffold service) is **not** part of this repo. See AGENTS.md §10 for
which lifecycle commands apply here.

## License

MIT
