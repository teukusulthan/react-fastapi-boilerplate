"""Write-side record preparation shared by every provider (identical semantics)."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from typing import Any

from db.schema import EntitySchema
from util.helper import new_id, utc_now

IMMUTABLE_FIELDS = frozenset({"id", "created_at"})


def check_fields(entity: EntitySchema, keys: Iterable[str]) -> None:
    unknown = sorted(set(keys) - entity.storage_fields)
    if unknown:
        raise ValueError(f"Unknown field(s) for entity {entity.name!r}: {', '.join(unknown)}")


def to_storage_datetime(value: datetime) -> datetime:
    """Aware UTC truncated to milliseconds (MongoDB's precision) so every provider round-trips equally."""
    aware = value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)
    return aware.replace(microsecond=aware.microsecond // 1000 * 1000)


def _normalise(value: Any) -> Any:
    return to_storage_datetime(value) if isinstance(value, datetime) else value


def _check_not_null(entity: EntitySchema, record: Mapping[str, Any]) -> None:
    missing = sorted(name for name, value in record.items() if value is None and not entity.get_field(name).nullable)
    if missing:
        raise ValueError(f"Field(s) of entity {entity.name!r} cannot be null: {', '.join(missing)}")


def prepare_insert(entity: EntitySchema, data: Mapping[str, Any]) -> dict[str, Any]:
    """Full record: defaults for omitted fields, ``id`` (uuid4 unless given), UTC timestamps."""
    check_fields(entity, data.keys())
    now = to_storage_datetime(utc_now())
    record: dict[str, Any] = {f.name: f.make_default() for f in entity.fields}
    record.update({k: _normalise(v) for k, v in data.items()})
    record["id"] = str(data.get("id") or new_id())
    record["created_at"] = _normalise(data.get("created_at")) or now
    record["updated_at"] = now
    _check_not_null(entity, record)
    return record


def prepare_update(entity: EntitySchema, changes: Mapping[str, Any]) -> dict[str, Any]:
    """``$set``-style partial change set; ``id``/``created_at`` are ignored, ``updated_at`` refreshed."""
    check_fields(entity, changes.keys())
    update = {k: _normalise(v) for k, v in changes.items() if k not in IMMUTABLE_FIELDS}
    update["updated_at"] = to_storage_datetime(utc_now())
    _check_not_null(entity, update)
    return update
