"""Supabase/Postgres provider: psycopg 3 connection pool + repository cache.

``prepare_threshold=None`` disables server-side prepared statements so the pool
works behind Supabase's transaction pooler (Supavisor, port 6543) as well as a
direct connection (port 5432).
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from psycopg import sql
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from db.base import Database
from db.schema import ENTITIES, EntitySchema, get_entity
from db.supabase.repository import PostgresRepository

if TYPE_CHECKING:
    from core.config import Settings


class PostgresDatabase(Database):
    provider = "supabase"

    def __init__(self, settings: Settings, pool: ConnectionPool | None = None) -> None:
        self.settings = settings
        self.schema = settings.SUPABASE_DB_SCHEMA
        if pool is None:
            if settings.SUPABASE_DB_URL is None:
                raise ValueError("BE_SUPABASE_DB_URL is not configured")
            pool = ConnectionPool(
                conninfo=settings.SUPABASE_DB_URL.get_secret_value(),
                min_size=settings.SUPABASE_DB_POOL_MIN,
                max_size=settings.SUPABASE_DB_POOL_MAX,
                timeout=settings.SUPABASE_DB_TIMEOUT,
                kwargs={
                    "autocommit": True,
                    "row_factory": dict_row,
                    "prepare_threshold": None,
                    "application_name": settings.APP_NAME,
                    "connect_timeout": int(settings.SUPABASE_DB_TIMEOUT),
                },
                open=False,
                name="app-db",
            )
        self.pool = pool
        self._repos: dict[str, PostgresRepository] = {}
        self._lock = threading.Lock()

    def open(self) -> None:
        # Don't block startup if the DB is down; readiness reports it instead.
        self.pool.open(wait=False)

    def repository(self, entity: EntitySchema | str) -> PostgresRepository:
        schema = get_entity(entity)
        repo = self._repos.get(schema.name)
        if repo is None:
            with self._lock:
                repo = self._repos.get(schema.name)
                if repo is None:
                    repo = PostgresRepository(self.pool, schema, schema.table(self.settings), self.schema)
                    self._repos[schema.name] = repo
        return repo

    def ping(self) -> None:
        with self.pool.connection(timeout=5) as conn:
            conn.execute("SELECT 1")

    def missing_tables(self, entities: list[EntitySchema] | None = None) -> list[str]:
        missing: list[str] = []
        with self.pool.connection(timeout=5) as conn:
            for entity in entities or list(ENTITIES.values()):
                name = entity.table(self.settings)
                qualified = sql.Identifier(self.schema, name).as_string(conn)
                row: Any = conn.execute("SELECT to_regclass(%s) AS reg", [qualified]).fetchone()
                if row is None or row["reg"] is None:
                    missing.append(f"{self.schema}.{name}")
        return missing

    def ensure_schema(self) -> None:
        """Tables are created by ``migrations/supabase/*.sql``; here we only verify them."""
        missing = self.missing_tables()
        if missing:
            raise RuntimeError(
                f"Missing tables: {', '.join(missing)} — apply migrations/supabase/*.sql (see migrations/supabase/README.md)"
            )

    def close(self) -> None:
        self.pool.close()
