"""MongoDB provider: client lifecycle + repository cache."""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING, Any

from pymongo import MongoClient

from db.base import Database
from db.mongo.indexes import ensure_indexes
from db.mongo.repository import MongoRepository
from db.schema import EntitySchema, get_entity

if TYPE_CHECKING:
    from core.config import Settings


class MongoDatabase(Database):
    provider = "mongo"

    def __init__(self, settings: Settings, client: Any | None = None) -> None:
        """``client`` may be injected (e.g. ``mongomock.MongoClient(tz_aware=True)`` in tests)."""
        self.settings = settings
        self.client = client or MongoClient(
            settings.MONGO_URI.get_secret_value(),
            tz_aware=True,
            uuidRepresentation="standard",
            serverSelectionTimeoutMS=settings.MONGO_TIMEOUT_MS,
            connectTimeoutMS=settings.MONGO_TIMEOUT_MS,
            appname=settings.APP_NAME,
        )
        self.db = self.client[settings.MONGO_DB]
        self._repos: dict[str, MongoRepository] = {}
        self._lock = threading.Lock()

    def repository(self, entity: EntitySchema | str) -> MongoRepository:
        schema = get_entity(entity)
        repo = self._repos.get(schema.name)
        if repo is None:
            with self._lock:
                repo = self._repos.get(schema.name)
                if repo is None:
                    repo = MongoRepository(self.db[schema.table(self.settings)], schema)
                    self._repos[schema.name] = repo
        return repo

    def ping(self) -> None:
        self.db.command("ping")

    def ensure_schema(self) -> None:
        ensure_indexes(self.db, self.settings)

    def close(self) -> None:
        self.client.close()
