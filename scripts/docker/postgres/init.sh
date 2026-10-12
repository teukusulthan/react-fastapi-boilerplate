#!/bin/sh
# docker-entrypoint-initdb.d hook for the `postgres` compose profile.
# Runs once, on an empty data volume: applies the Supabase compatibility layer and then
# every apps/backend/migrations/supabase/*.sql file (mounted at /migrations) in name order.
# To re-run after changing migrations: docker compose --profile postgres down -v
set -eu

psql_run() {
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" "$@"
}

echo "[init] applying Supabase compatibility layer"
psql_run -f /compat/00-supabase-compat.sql

found=0
for f in /migrations/*.sql; do
  [ -e "$f" ] || continue
  found=1
  echo "[init] applying migration $(basename "$f")"
  psql_run -f "$f"
done

if [ "$found" -eq 0 ]; then
  echo "[init] WARNING: no migrations found in /migrations (apps/backend/migrations/supabase)"
fi
