# /deploy — Deployment Workflow

Executes the deployment workflow for services to the target environment, including full support for local machine deployment accessible over a Local Area Network (LAN).

## Usage
```text
/deploy
/deploy [service_name] [stage]
/deploy backend staging
/deploy web production
/deploy all staging
```

## Phase 1: Artifact Verification

1. Inspect the project root directory for the existence of `docker-compose.yml`. Additionally, inspect each target application folder within the `apps/` directory to ensure a `Dockerfile` exists for each respective service.
2. If **missing** (either the root `docker-compose.yml` or the required `Dockerfile` for the target service): Pause the deployment process and instruct the user to run `/dockerize` (or `/dockerize [service_name]`) to generate the necessary artifacts first.
3. If **present**: Proceed to Phase 2.

## Phase 2: Mandatory Interactive Interview & Metadata Collection

You **MUST** conduct an interactive interview with the user to collect or confirm the following information before proceeding with the deployment:
- **Application Name (`appname`):**
  - **Strict Rule:** Must be entirely lowercase, words separated only by hyphens (`-`), with no spaces or other symbols allowed (e.g., `vibe-fs-app`, `core-backend`).
- **Application Description (`description`):** A brief explanation of the application (e.g., File management system).
- **Target Stage:** Prompt the user to select one of the following: `'local' | 'staging' | 'production'`.

## Phase 3: Service Identification & `deployment.json` Generation

1. **Directory Scan:** Scan the `apps/` directory in the project root to identify the names of all application folders (e.g., `web`, `backend`, `mobile`).
2. **Artifact Generation:** Generate or update the `deployment.json` file in the root directory based on the interview results and the discovered folder names. Update the `deployed_at` timestamp **only** for the target stage being deployed.

**Required `deployment.json` Format:**
*(Replace `<app_folder_name_X>` with the actual directory names found inside the `apps/` folder).*
```json
{
  "appname": "[INTERVIEW_APPNAME_KEBAB_CASE]",
  "description": "[INTERVIEW_DESCRIPTION]",
  "version": "0.0.0",
  "build": {
    "development": {
      "deployed_at": "[TIMESTAMP_ONLY_UPDATED_ON_LOCAL_DEPLOY]",
      "url": "http://[LOCAL_LAN_IP]:[PORT]",
      "services": {
        "<app_folder_name_1>": {
          "env": {
            "NODE_ENV": "development",
          }
        },
        "<app_folder_name_2>": {
          "env": {
            "NODE_ENV": "development",
          }
        }
      }
    },
    "staging": {
      "deployed_at": "[TIMESTAMP_ONLY_UPDATED_ON_STAGING_DEPLOY]",
      "url": "[https://api-staging.vibe-fs.com](https://api-staging.vibe-fs.com)",
      "services": {
        "<app_folder_name_1>": {
          "env": {
            "NODE_ENV": "staging",
          }
        }
      }
    },
    "production": {
      "deployed_at": "[TIMESTAMP_ONLY_UPDATED_ON_PRODUCTION_DEPLOY]",
      "url": "[https://api-vibe-fs.com](https://api-vibe-fs.com)",
      "services": {
        "<app_folder_name_1>": {
          "env": {
            "NODE_ENV": "production",
          }
        }
      }
    }
  }
}
```

## Phase 4: Pre-Deploy Checklist

Before deploying any service to staging or production, confirm:

- [ ] All CI checks pass on the target branch
- [ ] `npm run ci` passes locally (lint, format-check, typecheck, test, build for both apps)
- [ ] Database migrations reviewed and tested (`BE_DB_PROVIDER=supabase`: `apps/backend/migrations/supabase/*.sql` applied to the target database; Mongo needs none)
- [ ] Environment variables configured in target environment (`apps/backend/.env.example` → `BE_*`; web `VITE_*` are baked in at build time)
- [ ] Production backend settings: `BE_ENVIRONMENT=production`, real `BE_JWT_SECRET`, `BE_COOKIE_SECURE=true` (HTTPS), explicit `BE_CORS_ORIGINS`, `BE_PUBLIC_WEB_URL`, SMTP configured
- [ ] Dependencies pinned (`apps/backend/requirements*.txt`, `apps/web/package-lock.json`)
- [ ] `changelog/*.md` updated
- [ ] Feature flags enabled/disabled as intended

## Phase 5: Deployment Execution by Stage

### Local Deployment (Target: `local`)

To ensure the application is accessible to other devices on the same network (WiFi/LAN):
1. **Retrieve Local IP:** Execute system commands to fetch the machine's internal IP address (e.g., `192.168.1.X`).
   - *Linux/macOS:* `hostname -I | awk '{print $1}'`
   - *Windows:* `ipconfig`
2. **Update Configuration:** Inject the fetched IP into the `development.url` field in `deployment.json` (e.g., `http://192.168.1.24:3000`). Update `development.deployed_at` with the current timestamp.
3. **Prepare config:** `apps/backend/.env` must exist (`npm run setup:backend`). For plain-HTTP LAN access set `BE_COOKIE_SECURE=false` in it (otherwise browsers drop the auth cookies), and export `PUBLIC_WEB_URL=http://[LOCAL_IP]:8080` so emails and CORS use the LAN URL.
4. **Run Containers:** Execute Docker Compose at the project root. Ensure Docker Engine/Docker Desktop is running.
   ```bash
   npm run docker:up        # = docker compose up -d --build  (Postgres provider: DB_PROVIDER=supabase docker compose --profile postgres up -d --build)
   npm run seed             # first run only, from the host (or: docker compose exec backend python -m scripts.seed)
   ```
5. **Access Notice:** Output the following message to the user:
   > *"Deployment successful. The application is accessible on your local network at: http://[LOCAL_IP]:8080"*

   *(Note: `docker-compose.yml` publishes only the web container (`${WEB_PORT:-8080}`) on all interfaces; the backend (8020) and datastores are bound to 127.0.0.1. The web nginx proxies `/api/v1/apps/` to the backend.)*

### Staging / Production Deployment

**Backend Deploy (FastAPI, `apps/backend`)**
```bash
# 0. Postgres provider only: apply new migrations (the app never runs DDL)
psql "$BE_SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f apps/backend/migrations/supabase/<NNN_new>.sql

# 1. Build Docker image (python:3.12-slim, non-root, :8020) — CI job docker:build does this on the default branch/tags
docker build -t registry/<app>-backend:$VERSION apps/backend
docker push registry/<app>-backend:$VERSION

# 2. Verify health (liveness + readiness: DB and Redis)
curl -fsS https://<api-host>/health/live && curl -fsS https://<api-host>/health/ready
```

**Web Deploy (React + Vite, `apps/web`)**
```bash
# 1. Build image (npm ci + vite build → nginx-unprivileged on :8080; VITE_* passed as build args)
docker build --build-arg VITE_APP_NAME="<App>" -t registry/<app>-web:$VERSION apps/web
docker push registry/<app>-web:$VERSION
# Run with BACKEND_URL=<backend upstream> (nginx proxies /api/v1/apps/ → backend, prefix stripped)

# (static hosting alternative: cd apps/web && npm ci && npm run build → upload build/, and proxy /api/v1/apps/ to the backend)

# 2. Verify deployment
curl -I https://<web-host> && curl -fsS https://<web-host>/api/v1/apps/health/ready
```

**Mobile Deploy (Flutter)** — only if a mobile app exists under `apps/` (none in this boilerplate)
```bash
# Android
flutter build appbundle --release
# Upload to Google Play Console

# iOS
flutter build ipa --release
# Upload to App Store Connect via Xcode or xcrun altool
```

## Phase 6: Post-Deploy Verification

After every deploy:

1. **Health check** — `GET /health/live` and `GET /health/ready` return `200` (through the web: `/api/v1/apps/health/ready`).
2. **Connectivity Test** — For `local` deployments, verify access using the provided LAN URL from another device on the same network.
3. **Smoke test** — Log in, retrieve data, test main feature.
4. **Logs** — Check for unexpected errors in the first 5 minutes (`docker compose logs -f` for local).
5. **Metrics** — Verify error rate and p95 latency in monitoring dashboard (Staging/Production).

## Rollback

```bash
# Backend / Web: redeploy previous Docker image tag
docker pull registry/vibe-fs-$SERVICE:$PREVIOUS_VERSION
# restart service

# Database: there are no down-migrations. Postgres: write a new forward-fix migration
# (apps/backend/migrations/supabase/NNN_*.sql); Mongo: restore from backup if data changed.
```

## Environments

| Env        | Default Target URL            | Branch  |
|------------|-------------------------------|---------|
| local      | `http://[LOCAL_LAN_IP]:[PORT]`| any     |
| staging    | `https://api-staging.vibe-fs.com` | develop |
| production | `https://api.vibe-fs.com`       | main    |

## Notes

- Never deploy directly to production from a local machine.
- All production deploys go through the CI/CD pipeline.
- CI (`.gitlab-ci.yml`) builds and pushes the images; it does **not** apply Postgres migrations — apply them before rolling out the new backend.
- Keep at least 2 previous Docker image tags available for rollback.
