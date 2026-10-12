-- Minimal Supabase compatibility layer for a plain postgres:16 container.
--
-- Lets apps/backend/migrations/supabase/*.sql run unchanged outside a real Supabase
-- stack (docker compose --profile postgres). It only creates the objects Supabase
-- normally provides that migrations commonly reference: the API roles, the `auth` and
-- `extensions` schemas, and the auth.uid()/auth.role()/auth.jwt() helpers (which read the
-- PostgREST-style `request.jwt.claims` setting and return NULL otherwise).
-- The backend connects as the database owner, so RLS policies do not affect it.

do $$
begin
  if not exists (select 1 from pg_roles where rolname = 'anon') then
    create role anon nologin noinherit;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'authenticated') then
    create role authenticated nologin noinherit;
  end if;
  if not exists (select 1 from pg_roles where rolname = 'service_role') then
    create role service_role nologin noinherit bypassrls;
  end if;
end
$$;

create schema if not exists extensions;
create schema if not exists auth;

create extension if not exists pgcrypto with schema extensions;
create extension if not exists "uuid-ossp" with schema extensions;
create extension if not exists citext with schema extensions;

create or replace function auth.jwt() returns jsonb
language sql stable as $$
  select coalesce(nullif(current_setting('request.jwt.claims', true), ''), '{}')::jsonb
$$;

create or replace function auth.uid() returns uuid
language sql stable as $$
  select nullif(auth.jwt() ->> 'sub', '')::uuid
$$;

create or replace function auth.role() returns text
language sql stable as $$
  select auth.jwt() ->> 'role'
$$;

grant usage on schema auth, extensions to anon, authenticated, service_role;

-- Supabase's default search_path includes the extensions schema.
do $$
begin
  execute format('alter database %I set search_path = "$user", public, extensions', current_database());
end
$$;
