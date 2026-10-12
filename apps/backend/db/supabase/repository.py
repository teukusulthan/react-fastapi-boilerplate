"""Postgres (Supabase) implementation of :class:`db.base.Repository`.

All SQL is composed with ``psycopg.sql``; identifiers come from the entity
schema, values are bound parameters. JSON/list fields are written as ``jsonb``.
Connections come from a ``psycopg_pool.ConnectionPool`` in autocommit mode
(each call is one statement / one transaction).
"""

from __future__ import annotations

import json
import uuid
from collections.abc import Iterable, Mapping, Sequence
from datetime import date, datetime
from typing import Any

from psycopg import errors as pg_errors
from psycopg import sql
from psycopg.types.json import Jsonb
from psycopg_pool import ConnectionPool

from core.errors import ConflictError, ValidationError
from db.base import Condition, Op, QuerySpec, Repository, SortSpec, Where, normalize_where
from db.records import prepare_insert, prepare_update
from db.schema import EntitySchema
from db.supabase.translator import SqlTranslator
from util.helper import as_utc, is_uuid, to_camel


def _json_default(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, uuid.UUID):
        return str(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _dumps(obj: Any) -> str:
    return json.dumps(obj, default=_json_default)


def _from_row(row: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if row is None:
        return None
    out: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, uuid.UUID):
            value = str(value)
        elif isinstance(value, datetime):
            value = as_utc(value)
        out[key] = value
    return out


def _constraint_field(entity: EntitySchema, constraint: str | None) -> str | None:
    if not constraint:
        return None
    padded = f"_{constraint}_"
    for field in sorted(entity.fields, key=lambda f: -len(f.name)):
        if f"_{field.name}_" in padded:
            return field.name
    return None


class PostgresRepository(Repository):
    def __init__(self, pool: ConnectionPool, entity: EntitySchema, table: str, schema: str = "public") -> None:
        self.pool = pool
        self.entity = entity
        self.table = sql.Identifier(schema, table)
        self.translator = SqlTranslator(entity)

    # ------------------------------------------------------------- plumbing
    def _adapt(self, name: str, value: Any) -> Any:
        if name in self.entity.json_fields and value is not None:
            return Jsonb(value, dumps=_dumps)
        return value

    def _run(self, query: sql.Composable, params: Sequence[Any]) -> tuple[list[dict[str, Any]], int]:
        """Execute one statement; returns ``(rows, rowcount)`` with DB errors mapped to AppErrors."""
        try:
            with self.pool.connection() as conn, conn.cursor() as cur:
                cur.execute(query, params)
                rows = cur.fetchall() if cur.description else []
                rowcount = cur.rowcount
        except pg_errors.UniqueViolation as exc:
            raise self._conflict(exc) from None
        except pg_errors.ForeignKeyViolation as exc:
            field = _constraint_field(self.entity, exc.diag.constraint_name)
            label = to_camel(field) if field else "reference"
            raise ValidationError.for_field(label, "Referenced record does not exist") from None
        except pg_errors.CheckViolation as exc:
            field = _constraint_field(self.entity, exc.diag.constraint_name)
            raise ValidationError.for_field(to_camel(field) if field else "body", "Invalid value") from None
        return [_from_row(r) for r in rows], rowcount  # type: ignore[misc]

    def _execute(self, query: sql.Composable, params: Sequence[Any]) -> list[dict[str, Any]]:
        return self._run(query, params)[0]

    def _rowcount(self, query: sql.Composable, params: Sequence[Any]) -> int:
        return self._run(query, params)[1]

    def _conflict(self, exc: pg_errors.UniqueViolation) -> ConflictError:
        field = _constraint_field(self.entity, exc.diag.constraint_name)
        if field is None:
            return ConflictError()
        label = to_camel(field)
        return ConflictError(f"{label} already exists", details=[{"field": label, "message": "already exists"}])

    def _where(self, where: Where, params: list[Any]) -> sql.Composable:
        return self.translator.where(normalize_where(where), params)

    # ------------------------------------------------------------------ read
    def get_by_id(self, id: str) -> dict[str, Any] | None:
        if not is_uuid(id):
            return None
        rows = self._execute(sql.SQL("SELECT * FROM {} WHERE id = %s").format(self.table), [id])
        return rows[0] if rows else None

    def get_many_by_ids(self, ids: Iterable[str]) -> list[dict[str, Any]]:
        unique = [i for i in dict.fromkeys(ids) if is_uuid(i)]
        if not unique:
            return []
        params: list[Any] = []
        clause = self.translator.condition(Condition("id", Op.IN, tuple(unique)), params)
        return self._execute(sql.SQL("SELECT * FROM {} WHERE {}").format(self.table, clause), params)

    def find_one(self, where: Where) -> dict[str, Any] | None:
        params: list[Any] = []
        clause = self._where(where, params)
        rows = self._execute(sql.SQL("SELECT * FROM {} WHERE {} LIMIT 1").format(self.table, clause), params)
        return rows[0] if rows else None

    def find(self, spec: QuerySpec) -> tuple[list[dict[str, Any]], int]:
        params: list[Any] = []
        clause = self.translator.where(spec.where, params)
        total_rows = self._execute(
            sql.SQL("SELECT count(*) AS total FROM {} WHERE {}").format(self.table, clause), list(params)
        )
        total = int(total_rows[0]["total"]) if total_rows else 0
        query = sql.SQL("SELECT * FROM {} WHERE {}{}").format(self.table, clause, self.translator.order_by(spec.sort))
        if spec.limit is not None:
            query = sql.SQL("{} LIMIT %s").format(query)
            params.append(spec.limit)
        if spec.offset:
            query = sql.SQL("{} OFFSET %s").format(query)
            params.append(spec.offset)
        return self._execute(query, params), total

    def find_all(
        self, where: Where = None, *, sort: Sequence[SortSpec] | None = None, limit: int | None = None
    ) -> list[dict[str, Any]]:
        params: list[Any] = []
        clause = self._where(where, params)
        query = sql.SQL("SELECT * FROM {} WHERE {}{}").format(self.table, clause, self.translator.order_by(sort or ()))
        if limit is not None:
            query = sql.SQL("{} LIMIT %s").format(query)
            params.append(limit)
        return self._execute(query, params)

    def count(self, where: Where = None) -> int:
        params: list[Any] = []
        clause = self._where(where, params)
        rows = self._execute(sql.SQL("SELECT count(*) AS total FROM {} WHERE {}").format(self.table, clause), params)
        return int(rows[0]["total"]) if rows else 0

    # ----------------------------------------------------------------- write
    def insert(self, data: Mapping[str, Any]) -> dict[str, Any]:
        record = prepare_insert(self.entity, data)
        if not is_uuid(record["id"]):
            raise ValueError("Postgres ids must be UUID strings")
        columns = list(record)
        query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) RETURNING *").format(
            self.table,
            sql.SQL(", ").join(self.translator.column(c) for c in columns),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        rows = self._execute(query, [self._adapt(c, record[c]) for c in columns])
        return rows[0]

    def _set_clause(self, update: Mapping[str, Any], params: list[Any]) -> sql.Composable:
        parts = []
        for name, value in update.items():
            parts.append(sql.SQL("{} = %s").format(self.translator.column(name)))
            params.append(self._adapt(name, value))
        return sql.SQL(", ").join(parts)

    def update(self, id: str, changes: Mapping[str, Any]) -> dict[str, Any] | None:
        update = prepare_update(self.entity, changes)
        if not is_uuid(id):
            return None
        params: list[Any] = []
        set_clause = self._set_clause(update, params)
        params.append(id)
        rows = self._execute(
            sql.SQL("UPDATE {} SET {} WHERE id = %s RETURNING *").format(self.table, set_clause), params
        )
        return rows[0] if rows else None

    def update_many(self, where: Where, changes: Mapping[str, Any]) -> int:
        update = prepare_update(self.entity, changes)
        params: list[Any] = []
        set_clause = self._set_clause(update, params)
        clause = self._where(where, params)
        return self._rowcount(sql.SQL("UPDATE {} SET {} WHERE {}").format(self.table, set_clause, clause), params)

    def delete(self, id: str) -> bool:
        if not is_uuid(id):
            return False
        return self._rowcount(sql.SQL("DELETE FROM {} WHERE id = %s").format(self.table), [id]) == 1

    def delete_many(self, where: Where) -> int:
        filters = normalize_where(where)
        if not filters:
            raise ValueError("delete_many requires a filter (refusing to delete everything)")
        params: list[Any] = []
        clause = self.translator.where(filters, params)
        return self._rowcount(sql.SQL("DELETE FROM {} WHERE {}").format(self.table, clause), params)
