"""MongoDB provider (``BE_DB_PROVIDER=mongo``)."""

from db.mongo.client import MongoDatabase
from db.mongo.repository import MongoRepository

__all__ = ["MongoDatabase", "MongoRepository"]
