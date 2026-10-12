---
name: virtual-environment
description: "Python virtual environment for the backend: apps/backend/.venv created by npm run setup:backend (uv if installed, else python -m venv; Python >= 3.10, 3.12 preferred), run tools through it (scripts/py.mjs, .venv/bin/python -m pytest, .venv/bin/ruff), recreate with --recreate. Load when setting up the project, installing Python libraries, or when python/pytest/ruff commands fail."
---

# Virtual environment (backend)

## Use this skill when

- First-time setup, a broken/missing venv, or "module not found" when running backend commands
- Installing or upgrading Python packages
- Choosing how to invoke Python, pytest or ruff

## The one venv: `apps/backend/.venv`

Create/refresh it from the repo root:

```bash
npm run setup:backend                         # create .venv + install requirements-dev.txt + create .env if missing
node scripts/setup.mjs backend --recreate     # wipe and rebuild the venv
node scripts/setup.mjs backend --python 3.12  # pick an interpreter (version or path)
node scripts/setup.mjs backend --no-uv        # force python -m venv + pip
```

`scripts/setup.mjs` uses `uv` when it is on PATH (`uv venv` + `uv pip install --python .venv/bin/python -r requirements-dev.txt`),
otherwise the newest local Python ≥ 3.10 with `python -m venv` + pip. It also creates `apps/backend/.env` from
`.env.example` with generated `BE_JWT_SECRET`, `BE_INTERNAL_TOKEN`, `BE_DATA_ENCRYPTION_KEY` and a bootstrap-admin password.

## Running things inside the venv

| Task | Command |
|---|---|
| Dev server (reload) | `npm run dev:backend` (root) or `cd apps/backend && .venv/bin/python api.py` |
| Tests | `npm run test` (root) or `cd apps/backend && .venv/bin/python -m pytest` |
| Lint / format | `npm run lint`, `npm run format` or `.venv/bin/ruff check .`, `.venv/bin/ruff format .` |
| Seed | `npm run seed` (= `python -m scripts.seed` in the venv) |
| Any Python in the venv, cross-platform | `node ../../scripts/py.mjs <args>` from `apps/backend` (what the Nx targets do) |
| Install a new package | add it pinned to `requirements*.txt`, then `npm run setup:backend` |

Windows paths: `apps\backend\.venv\Scripts\python.exe` (handled by `scripts/py.mjs`).

## Rules

### MUST
- Use `apps/backend/.venv` for every backend command; invoke its interpreter explicitly (`.venv/bin/python -m ...`)
  or through the npm/Nx scripts.
- Record dependency changes in `requirements.txt` / `requirements-dev.txt` (see `fastapi-dependency-constraints`).
- Keep `.venv/` out of version control (already in the root `.gitignore`).

### MUST NOT
- No global `pip install`, no second venv (`venv/`, `env/`) in the repo, no `sudo pip`.
- Don't rely on whatever `python3` is on PATH — some environments shim it; use the venv interpreter.
- Don't install packages into the venv without updating the requirements files (the next setup would drop them).

## Troubleshooting

| Symptom | Fix |
|---|---|
| `Backend virtualenv not found` from `scripts/py.mjs` | `npm run setup:backend` |
| `uv` present but `uv pip` refused / misbehaving | the `uv` on PATH may be a restricted wrapper — use the real binary's full path, or `node scripts/setup.mjs backend --no-uv` |
| Wrong Python version in the venv | `node scripts/setup.mjs backend --recreate --python 3.12` |
| Upload returns 503 "File type detection is not available" | python-magic can't load libmagic: | install the system package `libmagic1` (Debian/Ubuntu) / `libmagic` (brew) |
