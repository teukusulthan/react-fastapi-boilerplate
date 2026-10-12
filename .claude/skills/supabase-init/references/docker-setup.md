# Self-hosted Supabase via Docker — distilled reference

> Source: <https://supabase.com/docs/guides/self-hosting/docker> + the upstream
> [`supabase/docker/utils/generate-keys.sh`](https://github.com/supabase/supabase/blob/master/docker/utils/generate-keys.sh).
> Captured during the supabase-init skill build. Keep verbatim — `init.py`
> mirrors this contract.

## Bring-up sequence (what init.py automates)

```sh
# 1. Sparse-clone the docker/ subtree.
git clone --filter=blob:none --no-checkout https://github.com/supabase/supabase
cd supabase
git sparse-checkout set --cone docker
git checkout master
cd ..

# 2. Materialise into the stack dir.
mkdir supabase-project
cp -rf supabase/docker/* supabase-project/
cp supabase/docker/.env.example supabase-project/.env

# 3. Inside supabase-project/.env, replace defaults (see "Secret rotation").

# 4. Pull + boot.
cd supabase-project
docker compose pull
docker compose up -d

# 5. Verify (within ~60s of boot all services should be `Up (healthy)`):
docker compose ps
```

## Secret rotation — what generate-keys.sh writes

These keys MUST be rotated before first boot. The official script uses
`openssl` only; Python `init.py` reproduces the exact byte-for-byte output via
`secrets`/`hmac`/`hashlib` (no PyJWT — stdlib is enough for HS256).

| Key                            | Generation                                       | Notes                              |
| ------------------------------ | ------------------------------------------------ | ---------------------------------- |
| `POSTGRES_PASSWORD`            | `openssl rand -hex 16`                           | 32 hex chars                       |
| `JWT_SECRET`                   | `openssl rand -base64 30`                        | 40 base64 chars                    |
| `ANON_KEY`                     | HS256(`{role:"anon",iss:"supabase",iat,exp}`)    | iat=now, exp=now+5y                |
| `SERVICE_ROLE_KEY`             | HS256(`{role:"service_role",iss:"supabase",…}`)  | same shape, different role         |
| `DASHBOARD_USERNAME`           | left at `supabase` default                       | Studio HTTP basic auth user        |
| `DASHBOARD_PASSWORD`           | `openssl rand -hex 16`                           | Studio HTTP basic auth password    |
| `SECRET_KEY_BASE`              | `openssl rand -base64 48`                        | Realtime / Supavisor               |
| `VAULT_ENC_KEY`                | `openssl rand -hex 16`                           | Supavisor — must be 32 chars       |
| `PG_META_CRYPTO_KEY`           | `openssl rand -base64 24`                        | postgres-meta                      |
| `LOGFLARE_PUBLIC_ACCESS_TOKEN` | `openssl rand -base64 24`                        | Analytics                          |
| `LOGFLARE_PRIVATE_ACCESS_TOKEN`| `openssl rand -base64 24`                        | Analytics                          |
| `S3_PROTOCOL_ACCESS_KEY_ID`    | `openssl rand -hex 16`                           | Storage S3 protocol                |
| `S3_PROTOCOL_ACCESS_KEY_SECRET`| `openssl rand -hex 32`                           | Storage S3 protocol                |
| `MINIO_ROOT_PASSWORD`          | `openssl rand -hex 16`                           | Bundled object store               |

### JWT payload format (HS256)

```json
header  = {"alg": "HS256", "typ": "JWT"}
payload = {"role": "<anon|service_role>", "iss": "supabase", "iat": <unix-now>, "exp": <unix-now + 5y>}
```

Algorithm: `base64url(header) + "." + base64url(payload) + "." + base64url(HMAC-SHA256(secret, signed_content))`.

The `iss` claim is `supabase` (NOT `supabase-demo` — that's only on the
shipped example keys). The role names (`anon`, `service_role`) must already
exist as Postgres roles; the supabase/postgres image creates them at init.

## Default ports (host-side)

| Service               | Host port | Container port |
| --------------------- | --------- | -------------- |
| Kong API gateway      | `8000`    | `8000`         |
| Kong API gateway TLS  | `8443`    | `8443`         |
| Studio (via Kong)     | `8000/`   | proxied        |
| Postgres (Supavisor)  | `5432`    | `5432`         |
| Pooler transaction    | `6543`    | `6543`         |
| Analytics (Logflare)  | `4000`    | `4000`         |

PostgREST, GoTrue, Realtime, Storage, Edge Functions, postgres-meta are all
internal-only and reached via Kong on `:8000` under `/rest/v1/`, `/auth/v1/`,
`/realtime/v1/`, `/storage/v1/`, `/functions/v1/`, and `/pg/`.

## Connection-string envs we expose to downstream consumers

These are the canonical names every consumer reads from `<sandbox>/.supabase/credentials.env`
— the backend (`<cwd>/apps/backend/`, which copies them into its `BE_SUPABASE_*` settings; it has no `agent_mgmt` router),
specialist agents that need DB access (`<cwd>/apps/agents/<role>/`),
and the `supabase-db` MCP (`<cwd>/apps/mcp/supabase-db/`):

```
SUPABASE_URL=http://127.0.0.1:8000
SUPABASE_ANON_KEY=<JWT signed with JWT_SECRET, role=anon>
SUPABASE_SERVICE_ROLE_KEY=<JWT signed with JWT_SECRET, role=service_role>
SUPABASE_JWT_SECRET=<the secret used to sign both keys>
SUPABASE_DB_URL=postgres://postgres:<POSTGRES_PASSWORD>@127.0.0.1:5432/postgres
SUPABASE_STUDIO_URL=http://127.0.0.1:8000
SUPABASE_DASHBOARD_USERNAME=supabase
SUPABASE_DASHBOARD_PASSWORD=<DASHBOARD_PASSWORD>
```

## Volume layout (persistence)

```
<stack>/docker/volumes/
├── api/kong.yml              ← Kong route config (in-repo)
├── db/                       ← Postgres init scripts (in-repo)
│   ├── data/                 ← LIVE Postgres datadir (do not commit)
│   ├── init/                 ← seed scripts
│   ├── jwt.sql / logs.sql / realtime.sql / roles.sql / webhooks.sql
├── functions/                ← Edge Functions sources
├── logs/vector.yml
├── pooler/pooler.exs
└── storage/                  ← LIVE storage objects (do not commit)
```

Postgres data lives at `<stack>/docker/volumes/db/data`. Removing this
directory wipes all rows — `teardown.py --wipe` does it for you.

## Health-check invariants

After `docker compose up -d`, all services should reach `Up (healthy)` within
~90s on a fresh pull. Key probes:

- `docker compose ps` — every row's STATUS column says `(healthy)`.
- `curl http://127.0.0.1:8000/rest/v1/` with `apikey: <ANON_KEY>` → `200 OK`.
- `psql "$SUPABASE_DB_URL" -c "select 1"` — quick sanity for direct PG access.

## Teardown

```sh
docker compose down            # stop + remove containers; volumes preserved
docker compose down -v         # ALSO drops the named volumes  (data lost)
rm -rf volumes/db/data         # ALSO wipes the bind-mounted PG datadir
rm -rf volumes/storage         # storage objects, if any
```

`teardown.py` defaults to the non-destructive form. `--wipe` adds `down -v`
plus the bind-mount cleanup. `--remove-stack` further deletes the entire
`<stack>/` directory.

## Gotchas

1. **Docker socket on rootless / Podman.** Set `DOCKER_SOCKET_LOCATION` in
   `.env` to `/run/user/<uid>/docker.sock` (rootless) or
   `/run/podman/podman.sock` (Podman). Required for the analytics service.
2. **Studio HTTP-auth password rules.** Must contain at least one letter and
   cannot be all-numeric — `openssl rand -hex 16` satisfies both.
3. **Pre-signed example keys.** `.env.example` ships with demo ANON_KEY /
   SERVICE_ROLE_KEY signed against the demo JWT_SECRET. Booting with these
   lets the stack come up but every project that signs against the rotated
   secret will reject the demo keys — always rotate before first boot.
4. **`iss` claim mismatch.** The demo keys carry `iss: "supabase-demo"`; the
   real generator emits `iss: "supabase"`. Some downstream services log
   warnings on this mismatch — match what `generate-keys.sh` writes.
5. **Port collisions.** If `8000` or `5432` are taken, edit `.env`'s
   `KONG_HTTP_PORT` / `POSTGRES_PORT` *before* `docker compose up` —
   changing them later requires a `down` + bring-up cycle.
6. **Re-pull cadence.** `docker compose pull` periodically; otherwise
   `supabase/postgres` and friends drift behind upstream security fixes.
