"""Provider-agnostic data layer.

Services import from here only (never ``pymongo`` / ``psycopg``)::

    from db import Repository, QuerySpec, Condition, AnyOf, AllOf, Op, SortSpec, SortDirection
    from db.schema import USERS, PERMISSIONS, GROUPS, ROLES, UPLOADS
    from db.query import build_query_spec
"""

from db.base import (
    AllOf,
    AnyOf,
    Condition,
    Database,
    Filter,
    Op,
    QuerySpec,
    Repository,
    SortDirection,
    SortSpec,
    Where,
    normalize_where,
)

__all__ = [
    "AllOf",
    "AnyOf",
    "Condition",
    "Database",
    "Filter",
    "Op",
    "QuerySpec",
    "Repository",
    "SortDirection",
    "SortSpec",
    "Where",
    "normalize_where",
]
