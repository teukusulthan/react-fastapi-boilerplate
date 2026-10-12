"""MongoDB implementation of :class:`db.base.Repository`.

Documents store the app id in ``_id`` (uuid4 string); records returned to
callers expose it as ``id``.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import Any

from pymongo import ASCENDING, DESCENDING, ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import DuplicateKeyError

from core.errors import ConflictError
from db.base import QuerySpec, Repository, SortDirection, SortSpec, Where, normalize_where
from db.mongo.translator import mongo_field, translate_where
from db.records import prepare_insert, prepare_update
from db.schema import EntitySchema
from util.helper import as_utc, to_camel

_INDEX_NAME = re.compile(r"index: uniq_([a-z0-9_]+)")


def _from_doc(doc: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if doc is None:
        return None
    record = {k: as_utc(v) if isinstance(v, datetime) else v for k, v in doc.items()}
    record["id"] = record.pop("_id")
    return record


def _probe_duplicate_field(
    collection: Collection | None, entity: EntitySchema, values: Mapping[str, Any] | None, self_id: Any
) -> list[str]:
    """Find which unique field collides by querying for another document with the same value.

    Used only when the driver error carries neither ``keyPattern`` nor the index name
    (e.g. mongomock's bare ``E11000 Duplicate Key Error``).
    """
    if collection is None or not values:
        return []
    for unique in entity.unique_fields:
        value = values.get(unique.name)
        if value is None:
            continue
        query: dict[str, Any] = {unique.name: value}
        if self_id is not None:
            query["_id"] = {"$ne": self_id}
        if collection.find_one(query, projection={"_id": 1}) is not None:
            return [unique.name]
    return []


def conflict_from_duplicate(
    entity: EntitySchema,
    exc: DuplicateKeyError,
    *,
    collection: Collection | None = None,
    values: Mapping[str, Any] | None = None,
    self_id: Any = None,
) -> ConflictError:
    details = exc.details or {}
    keys = list((details.get("keyPattern") or details.get("keyValue") or {}).keys())
    if not keys:  # fall back to the index name in the message: "... index: uniq_email dup key ..."
        match = _INDEX_NAME.search(str(exc))
        keys = [match.group(1)] if match and entity.has(match.group(1)) else []
    if not keys:  # last resort: ask the collection which unique value is already taken
        keys = _probe_duplicate_field(collection, entity, values, self_id)
    field = keys[0] if keys else None
    if field == "_id":
        field = "id"
    label = to_camel(field) if field else "record"
    return ConflictError(
        f"{label} already exists" if field else "Resource already exists",
        details=[{"field": label, "message": "already exists"}] if field else None,
    )


class MongoRepository(Repository):
    def __init__(self, collection: Collection, entity: EntitySchema) -> None:
        self.collection = collection
        self.entity = entity

    # ------------------------------------------------------------------ read
    def _sort(self, sort: Sequence[SortSpec] | None) -> list[tuple[str, int]]:
        pairs = [
            (mongo_field(s.field), ASCENDING if s.direction == SortDirection.ASC else DESCENDING) for s in sort or ()
        ]
        if pairs and all(name != "_id" for name, _ in pairs):
            pairs.append(("_id", pairs[-1][1]))  # deterministic pagination
        return pairs

    def get_by_id(self, id: str) -> dict[str, Any] | None:
        if not isinstance(id, str) or not id:
            return None
        return _from_doc(self.collection.find_one({"_id": id}))

    def get_many_by_ids(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        unique = [i for i in dict.fromkeys(ids) if isinstance(i, str) and i]
        if not unique:
            return []
        return [_from_doc(d) for d in self.collection.find({"_id": {"$in": unique}})]  # type: ignore[misc]

    def find_one(self, where: Where) -> dict[str, Any] | None:
        return _from_doc(self.collection.find_one(translate_where(normalize_where(where))))

    def find(self, spec: QuerySpec) -> tuple[list[dict[str, Any]], int]:
        query = translate_where(spec.where)
        total = self.collection.count_documents(query)
        cursor = self.collection.find(query)
        sort = self._sort(spec.sort)
        if sort:
            cursor = cursor.sort(sort)
        if spec.offset:
            cursor = cursor.skip(spec.offset)
        if spec.limit is not None:
            cursor = cursor.limit(spec.limit)
        return [_from_doc(d) for d in cursor], total  # type: ignore[misc]

    def find_all(
        self, where: Where = None, *, sort: Sequence[SortSpec] | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        cursor = self.collection.find(translate_where(normalize_where(where)))
        pairs = self._sort(sort)
        if pairs:
            cursor = cursor.sort(pairs)
        if limit is not None:
            cursor = cursor.limit(limit)
        return [_from_doc(d) for d in cursor]  # type: ignore[misc]

    def count(self, where: Where = None) -> int:
        return self.collection.count_documents(translate_where(normalize_where(where)))

    # ----------------------------------------------------------------- write
    def insert(self, data: Mapping[str, Any]) -> dict[str, Any]:
        record = prepare_insert(self.entity, data)
        doc = {"_id": record.pop("id"), **record}
        try:
            self.collection.insert_one(doc)
        except DuplicateKeyError as exc:
            raise conflict_from_duplicate(
                self.entity, exc, collection=self.collection, values=doc, self_id=doc["_id"]
            ) from None
        return _from_doc(doc)  # type: ignore[return-value]

    def update(self, id: str, changes: Mapping[str, Any]) -> dict[str, Any] | None:
        update = prepare_update(self.entity, changes)
        if not isinstance(id, str) or not id:
            return None
        try:
            doc = self.collection.find_one_and_update(
                {"_id": id}, {"$set": update}, return_document=ReturnDocument.AFTER, upsert=False
            )
        except DuplicateKeyError as exc:
            raise conflict_from_duplicate(
                self.entity, exc, collection=self.collection, values=update, self_id=id
            ) from None
        return _from_doc(doc)

    def update_many(self, where: Where, changes: Mapping[str, Any]) -> int:
        update = prepare_update(self.entity, changes)
        try:
            result = self.collection.update_many(
                translate_where(normalize_where(where)), {"$set": update}, upsert=False
            )
        except DuplicateKeyError as exc:
            raise conflict_from_duplicate(self.entity, exc, collection=self.collection, values=update) from None
        return result.matched_count

    def delete(self, id: str) -> bool:
        if not isinstance(id, str) or not id:
            return False
        return self.collection.delete_one({"_id": id}).deleted_count == 1

    def delete_many(self, where: Where) -> int:
        filters = normalize_where(where)
        if not filters:
            raise ValueError("delete_many requires a filter (refusing to delete everything)")
        return self.collection.delete_many(translate_where(filters)).deleted_count
