"""Idempotent MongoDB index creation (run on startup and by readiness retries).

* Unique fields -> unique index ``uniq_<field>``; nullable unique fields use a
  partial filter (``$type``) so many ``null`` values are allowed (same semantics
  as Postgres ``UNIQUE``).
* ``created_at`` and every reference id field get a plain index ``idx_<field>``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from loguru import logger
from pymongo import ASCENDING, DESCENDING

from db.schema import ENTITIES, EntitySchema, FieldType

if TYPE_CHECKING:
    from pymongo.database import Database as PyMongoDatabase

    from core.config import Settings

_BSON_TYPE = {
    FieldType.ID: "string",
    FieldType.STR: "string",
    FieldType.INT: "number",
    FieldType.FLOAT: "number",
    FieldType.BOOL: "bool",
    FieldType.DATETIME: "date",
}


IndexSpec = tuple[list[tuple[str, int]], dict[str, Any]]


def index_specs(entity: EntitySchema) -> list[IndexSpec]:
    """``(keys, options)`` pairs for ``collection.create_index``."""
    specs: list[IndexSpec] = []
    for field in entity.unique_fields:
        options: dict[str, Any] = {"unique": True, "name": f"uniq_{field.name}"}
        if field.nullable:
            options["partialFilterExpression"] = {field.name: {"$type": _BSON_TYPE.get(field.type, "string")}}
        specs.append(([(field.name, ASCENDING)], options))
    specs.append(([("created_at", DESCENDING)], {"name": "idx_created_at"}))
    for field in entity.fields:
        if field.type == FieldType.ID and field.name != "id" and not field.unique:
            specs.append(([(field.name, ASCENDING)], {"name": f"idx_{field.name}"}))
    return specs


def ensure_indexes(db: PyMongoDatabase, settings: Settings, entities: list[EntitySchema] | None = None) -> None:
    # One create_index call per index (idempotent; also honoured by mongomock, whose
    # create_indexes() drops partialFilterExpression).
    for entity in entities or list(ENTITIES.values()):
        collection = db[entity.table(settings)]
        names = [collection.create_index(keys, **options) for keys, options in index_specs(entity)]
        logger.debug("Mongo indexes ensured on {}: {}", collection.name, ", ".join(names))
