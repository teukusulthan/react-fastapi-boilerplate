"""Small, dependency-free helpers shared across layers.

Keep this module tiny: anything that needs settings, a database or a network
client belongs in ``core/`` or ``db/`` instead.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime, timezone

_CAMEL_BOUNDARY = re.compile(r"(?<!^)(?=[A-Z])")


def utc_now() -> datetime:
    """Current time as a timezone-aware UTC datetime (never use naive datetimes)."""
    return datetime.now(timezone.utc)


def new_id() -> str:
    """App-generated primary key used by every entity in every provider."""
    return str(uuid.uuid4())


def is_uuid(value: object) -> bool:
    """True when ``value`` is a canonical UUID string (or a ``uuid.UUID``)."""
    if isinstance(value, uuid.UUID):
        return True
    if not isinstance(value, str):
        return False
    try:
        return str(uuid.UUID(value)) == value.lower()
    except ValueError:
        return False


def to_camel(name: str) -> str:
    """``created_at`` -> ``createdAt``."""
    head, *tail = name.split("_")
    return head + "".join(part[:1].upper() + part[1:] for part in tail)


def to_snake(name: str) -> str:
    """``createdAt`` -> ``created_at``."""
    return _CAMEL_BOUNDARY.sub("_", name).lower()


def censor_email(email: str | None) -> str:
    """Mask an email for logs: ``john.doe@example.com`` -> ``jo***@example.com``."""
    if not email or "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    return f"{local[:2]}***@{domain}"


def as_utc(value: datetime | None) -> datetime | None:
    """Normalise a datetime to aware UTC (naive values are assumed to be UTC)."""
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
