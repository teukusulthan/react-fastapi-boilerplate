"""Idempotent seed: default permissions + bootstrap administrator.

    cd apps/backend && python -m scripts.seed

* Creates the permissions ``admin`` (superuser, privileges ``["*"]``) and
  ``user`` (``BE_DEFAULT_PERMISSION_ALIAS`` is what new registrations get) when
  their alias does not exist yet. Existing permissions are never modified.
* Local auth (``BE_AUTH_PROVIDER=local``): if ``BE_BOOTSTRAP_ADMIN_EMAIL`` and
  ``BE_BOOTSTRAP_ADMIN_PASSWORD`` are set and no user has that email/username,
  creates an active, verified admin (username ``BE_BOOTSTRAP_ADMIN_USERNAME``).
  An existing user is left untouched (its password is never reset by the seed).
* Supabase auth: users come from Supabase. If a local user with
  ``BE_BOOTSTRAP_ADMIN_EMAIL`` exists (i.e. after their first sign-in) it is
  promoted to the admin permission; otherwise the seed tells you to sign in
  once and run it again.

Works with both DB providers (repositories only). Exit code 1 on failure.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import Any

from loguru import logger

from core.config import Settings, get_settings
from core.errors import AppError
from core.logging import setup_logging
from core.security import hash_password, validate_password_policy
from db.base import AnyOf, Condition, Database, Op
from db.factory import create_database
from db.schema import PERMISSIONS, USERS
from util.helper import censor_email

SEED_ACTOR = "seed"
ADMIN_ALIAS = "admin"
USER_ALIAS = "user"

DEFAULT_PERMISSIONS: tuple[dict[str, Any], ...] = (
    {
        "name": "Administrator",
        "alias": ADMIN_ALIAS,
        "description": "Full access (superuser)",
        "type": "system",
        "privileges": ["*"],
    },
    {
        "name": "User",
        "alias": USER_ALIAS,
        "description": "Default role for regular users",
        "type": "system",
        "privileges": ["profile:read", "profile:write", "upload:read", "upload:write"],
    },
)


@dataclass
class SeedResult:
    created_permissions: list[str] = field(default_factory=list)
    existing_permissions: list[str] = field(default_factory=list)
    admin: str = "skipped"  # created | exists | promoted | skipped | pending-signin


def _ensure_permissions(database: Database, result: SeedResult) -> dict[str, dict[str, Any]]:
    repo = database.repository(PERMISSIONS)
    by_alias: dict[str, dict[str, Any]] = {}
    for spec in DEFAULT_PERMISSIONS:
        existing = repo.find_one({"alias": spec["alias"]})
        if existing is None:
            existing = repo.insert({**spec, "created_by": SEED_ACTOR})
            result.created_permissions.append(spec["alias"])
            logger.info("Created permission {!r}", spec["alias"])
        else:
            result.existing_permissions.append(spec["alias"])
        by_alias[spec["alias"]] = existing
    return by_alias


def _ensure_admin(database: Database, settings: Settings, admin_permission: dict[str, Any], result: SeedResult) -> None:
    email = (settings.BOOTSTRAP_ADMIN_EMAIL or "").strip().lower()
    if not email:
        logger.info("BE_BOOTSTRAP_ADMIN_EMAIL not set; no bootstrap admin")
        return
    users = database.repository(USERS)
    username = settings.BOOTSTRAP_ADMIN_USERNAME.strip()

    if settings.AUTH_PROVIDER == "supabase":
        user = users.find_one({"email": email})
        if user is None:
            result.admin = "pending-signin"
            logger.warning("No user {} yet: sign in once via Supabase, then re-run the seed", censor_email(email))
        elif user.get("permission_id") != admin_permission["id"]:
            users.update(user["id"], {"permission_id": admin_permission["id"]})
            result.admin = "promoted"
            logger.info("Promoted {} to admin", censor_email(email))
        else:
            result.admin = "exists"
        return

    if settings.BOOTSTRAP_ADMIN_PASSWORD is None:
        logger.warning("BE_BOOTSTRAP_ADMIN_PASSWORD not set; no bootstrap admin")
        return
    existing = users.find_one(AnyOf(Condition("email", Op.EQ, email), Condition("username", Op.EQ, username)))
    if existing is not None:
        result.admin = "exists"
        logger.info("Bootstrap admin already exists ({}); left unchanged", censor_email(existing.get("email")))
        return
    password = settings.BOOTSTRAP_ADMIN_PASSWORD.get_secret_value()
    validate_password_policy(password, settings, field_name="BE_BOOTSTRAP_ADMIN_PASSWORD")
    users.insert(
        {
            "username": username,
            "fullname": settings.BOOTSTRAP_ADMIN_FULLNAME,
            "email": email,
            "password_hash": hash_password(password),
            "permission_id": admin_permission["id"],
            "status": "active",
            "email_verified": True,
            "auth_provider": "local",
            "created_by": SEED_ACTOR,
        }
    )
    result.admin = "created"
    logger.info("Created bootstrap admin {} ({})", username, censor_email(email))


def seed(database: Database, settings: Settings) -> SeedResult:
    """Run the seed against an open database (safe to call repeatedly)."""
    result = SeedResult()
    permissions = _ensure_permissions(database, result)
    _ensure_admin(database, settings, permissions[ADMIN_ALIAS], result)
    return result


def main() -> int:
    settings = get_settings()
    setup_logging(settings)
    database = create_database(settings)
    try:
        database.open()
        database.ensure_schema()
        result = seed(database, settings)
    except AppError as exc:
        logger.error("Seed failed: {} {}", exc.message, exc.details or "")
        return 1
    except Exception as exc:  # noqa: BLE001  # CLI boundary: report and exit non-zero
        logger.opt(exception=exc).error("Seed failed: {}", type(exc).__name__)
        return 1
    finally:
        database.close()
    logger.info(
        "Seed done: permissions created={} existing={}; admin={}",
        result.created_permissions,
        result.existing_permissions,
        result.admin,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
