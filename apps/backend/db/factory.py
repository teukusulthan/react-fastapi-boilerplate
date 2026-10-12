"""Pick the configured database provider (imports the driver lazily)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from db.base import Database

if TYPE_CHECKING:
    from core.config import Settings


def create_database(settings: Settings) -> Database:
    if settings.DB_PROVIDER == "mongo":
        from db.mongo import MongoDatabase

        return MongoDatabase(settings)
    if settings.DB_PROVIDER == "supabase":
        from db.supabase import PostgresDatabase

        return PostgresDatabase(settings)
    raise ValueError(f"Unsupported BE_DB_PROVIDER {settings.DB_PROVIDER!r}")
