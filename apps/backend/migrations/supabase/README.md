# Supabase (Postgres) migrations

Used only when `BE_DB_PROVIDER=supabase`. (With `BE_DB_PROVIDER=mongo` the backend
creates its unique indexes itself on startup — see `db/mongo/indexes.py`.)

Files are plain, idempotent SQL applied in lexical order (`001_init.sql`, `002_…`).
The backend never runs DDL; on startup and on `GET /health/ready` it only checks
that the tables exist and reports "not ready" until they do.

## Apply

**Supabase dashboard:** SQL Editor → New query → paste `001_init.sql` → Run.

**psql** (use the *direct* or *session pooler* connection string from
Project Settings → Database):

```bash
psql "$BE_SUPABASE_DB_URL" -v ON_ERROR_STOP=1 -f migrations/supabase/001_init.sql
```

**Supabase CLI:** copy the file to `supabase/migrations/<timestamp>_init.sql` and run
`supabase db push`.

## Rules for new migrations

- Never edit an applied file; add `NNN_<what>.sql`.
- Keep it idempotent (`create … if not exists`, `drop trigger if exists`).
- Mirror every change in `db/schema.py` (fields, `unique=True`, defaults) so both
  providers behave the same.
- Unique constraints must be named `<table>_<field>_key` and check constraints
  `<table>_<field>_check`: the repository maps those names back to the API
  field in 409/422 responses.
- New tables: enable RLS and revoke `anon` / `authenticated` (see the lockdown
  block in `001_init.sql`) — the backend is the only client.

## Connection notes

- `BE_SUPABASE_DB_URL` accepts the direct connection (port 5432) or the
  transaction pooler (port 6543); prepared statements are disabled so both work.
- Table names are configurable (`BE_TABLE_*`), but these SQL files assume the
  defaults — edit them if you rename tables.
