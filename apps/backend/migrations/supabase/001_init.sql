-- 001_init.sql — initial schema for BE_DB_PROVIDER=supabase.
-- Idempotent: safe to re-run. Mirrors db/schema.py (field names, uniques, defaults).
-- Table names assume the default BE_TABLE_* settings (users, permissions, groups, roles, uploads)
-- and BE_SUPABASE_DB_SCHEMA=public.

begin;

-- ---------------------------------------------------------------- helpers
-- Refresh updated_at on UPDATE unless the statement already set a new value
-- (the backend always sets it; this covers manual edits in the SQL editor).
create or replace function public.set_updated_at() returns trigger
language plpgsql as $$
begin
  if new.updated_at is not distinct from old.updated_at then
    new.updated_at := now();
  end if;
  return new;
end;
$$;

-- ------------------------------------------------------------ permissions
create table if not exists public.permissions (
  id           uuid primary key default gen_random_uuid(),
  name         text not null,
  alias        text,
  description  text,
  type         text,
  privileges   jsonb not null default '[]'::jsonb,
  parent_id    uuid references public.permissions (id) on delete set null,
  image        text,
  created_by   text,
  created_at   timestamptz not null default now(),
  updated_at   timestamptz not null default now(),
  constraint permissions_alias_key unique (alias),
  constraint permissions_privileges_check check (jsonb_typeof(privileges) = 'array')
);
create index if not exists permissions_created_at_idx on public.permissions (created_at desc);
create index if not exists permissions_parent_id_idx on public.permissions (parent_id);

-- ----------------------------------------------------------------- groups
create table if not exists public.groups (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  description      text,
  parent_id        uuid references public.groups (id) on delete set null,
  settings         jsonb,
  filters          jsonb,
  image            text,
  personalization  jsonb,
  created_by       text,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create index if not exists groups_created_at_idx on public.groups (created_at desc);
create index if not exists groups_parent_id_idx on public.groups (parent_id);

-- ------------------------------------------------------------------ roles
create table if not exists public.roles (
  id               uuid primary key default gen_random_uuid(),
  name             text not null,
  alias            text,
  description      text,
  role_position    integer,
  type             text,
  parent_id        uuid references public.roles (id) on delete set null,
  workspace_id     text,
  organization_id  text,
  created_by       text,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);
create index if not exists roles_created_at_idx on public.roles (created_at desc);
create index if not exists roles_parent_id_idx on public.roles (parent_id);

-- ------------------------------------------------------------------ users
create table if not exists public.users (
  id                  uuid primary key default gen_random_uuid(),
  username            text not null,
  fullname            text,
  email               text not null,
  phone               text,
  password_hash       text,
  permission_id       uuid references public.permissions (id) on delete set null,
  group_id            uuid references public.groups (id) on delete set null,
  status              text not null default 'pending',
  email_verified      boolean not null default false,
  multi_login         boolean not null default true,
  expired_at          timestamptz,
  last_login_at       timestamptz,
  two_factor_enabled  boolean not null default false,
  two_factor_method   text,
  two_factor_secret   text,
  about               text,
  image               text,
  settings            jsonb,
  personalization     jsonb,
  additional          jsonb,
  auth_provider       text not null default 'local',
  external_id         text,
  created_by          text,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now(),
  constraint users_username_key unique (username),
  constraint users_email_key unique (email),
  constraint users_phone_key unique (phone),
  constraint users_external_id_key unique (external_id),
  constraint users_status_check check (status in ('pending', 'active', 'blocked', 'deleted')),
  constraint users_auth_provider_check check (auth_provider in ('local', 'google', 'supabase')),
  constraint users_two_factor_method_check check (two_factor_method is null or two_factor_method in ('email', 'totp'))
);
create index if not exists users_created_at_idx on public.users (created_at desc);
create index if not exists users_permission_id_idx on public.users (permission_id);
create index if not exists users_group_id_idx on public.users (group_id);

-- ---------------------------------------------------------------- uploads
create table if not exists public.uploads (
  id             uuid primary key default gen_random_uuid(),
  bucket         text not null,
  object_key     text not null,
  filename       text not null,
  mime_type      text,
  filesize       bigint,
  folder         text,
  tags           jsonb not null default '[]'::jsonb,
  widget_id      text,
  dashboard_id   text,
  workspace_id   text,
  connection_id  text,
  created_by     text,
  created_at     timestamptz not null default now(),
  updated_at     timestamptz not null default now(),
  constraint uploads_object_key_key unique (object_key),
  constraint uploads_tags_check check (jsonb_typeof(tags) = 'array')
);
create index if not exists uploads_created_at_idx on public.uploads (created_at desc);
create index if not exists uploads_created_by_idx on public.uploads (created_by);

-- --------------------------------------------------------------- triggers
do $$
declare
  t text;
begin
  foreach t in array array['permissions', 'groups', 'roles', 'users', 'uploads'] loop
    execute format('drop trigger if exists set_updated_at on public.%I', t);
    execute format(
      'create trigger set_updated_at before update on public.%I for each row execute function public.set_updated_at()',
      t
    );
  end loop;
end;
$$;

-- -------------------------------------------------------------- lockdown
-- These tables are accessed ONLY by the backend (table owner / service role).
-- Enable RLS without policies and revoke grants so Supabase's auto-generated
-- REST/GraphQL APIs (anon / authenticated keys) can never read password hashes.
alter table public.permissions enable row level security;
alter table public.groups enable row level security;
alter table public.roles enable row level security;
alter table public.users enable row level security;
alter table public.uploads enable row level security;

do $$
declare
  r text;
begin
  foreach r in array array['anon', 'authenticated'] loop
    if exists (select 1 from pg_roles where rolname = r) then
      execute format(
        'revoke all on table public.permissions, public.groups, public.roles, public.users, public.uploads from %I',
        r
      );
    end if;
  end loop;
end;
$$;

commit;
