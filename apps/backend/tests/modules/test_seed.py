"""scripts/seed.py: idempotent permissions + bootstrap admin (both auth providers)."""

from __future__ import annotations

import pytest

from core.deps import build_principal
from core.errors import ValidationError
from core.security import verify_password
from scripts import seed as seed_module
from scripts.seed import seed

ADMIN_ENV = {
    "BOOTSTRAP_ADMIN_EMAIL": "Root@Example.com",
    "BOOTSTRAP_ADMIN_PASSWORD": "bootstrap-password-1",
    "BOOTSTRAP_ADMIN_USERNAME": "root",
}


def test_seed_is_idempotent(database, make_settings, users_repo, permissions_repo):
    settings = make_settings(**ADMIN_ENV)
    first = seed(database, settings)
    assert first.created_permissions == ["admin", "user"] and first.admin == "created"

    admin = users_repo.find_one({"email": "root@example.com"})
    assert admin["username"] == "root" and admin["status"] == "active" and admin["email_verified"] is True
    assert verify_password("bootstrap-password-1", admin["password_hash"])
    admin_perm = permissions_repo.find_one({"alias": "admin"})
    assert build_principal(admin, admin_perm, settings).is_superuser

    second = seed(database, make_settings(**{**ADMIN_ENV, "BOOTSTRAP_ADMIN_PASSWORD": "another-password-2"}))
    assert second.created_permissions == [] and second.existing_permissions == ["admin", "user"]
    assert second.admin == "exists"
    assert permissions_repo.count() == 2 and users_repo.count() == 1
    # the seed never resets an existing admin's password
    assert verify_password("bootstrap-password-1", users_repo.get_by_id(admin["id"])["password_hash"])


def test_seed_keeps_customised_permissions(database, make_settings, permission_factory, permissions_repo):
    custom = permission_factory(name="My admins", alias="admin", privileges=["custom"])
    result = seed(database, make_settings())
    assert result.created_permissions == ["user"] and result.admin == "skipped"
    assert permissions_repo.get_by_id(custom["id"])["privileges"] == ["custom"]


def test_seed_without_password_or_with_weak_password(database, make_settings, users_repo):
    assert seed(database, make_settings(BOOTSTRAP_ADMIN_EMAIL="a@b.io")).admin == "skipped"
    assert users_repo.count() == 0
    with pytest.raises(ValidationError):
        seed(database, make_settings(BOOTSTRAP_ADMIN_EMAIL="a@b.io", BOOTSTRAP_ADMIN_PASSWORD="short"))


def test_seed_supabase_auth_promotes_existing_user(database, make_settings, user_factory, users_repo, permissions_repo):
    settings = make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET="s" * 40, **ADMIN_ENV)
    assert seed(database, settings).admin == "pending-signin"
    user = user_factory(email="root@example.com", username="root-sb", auth_provider="supabase", password=None)
    assert seed(database, settings).admin == "promoted"
    assert users_repo.get_by_id(user["id"])["permission_id"] == permissions_repo.find_one({"alias": "admin"})["id"]
    assert seed(database, settings).admin == "exists"


def test_main_runs_against_configured_database(monkeypatch, database, make_settings, permissions_repo):
    settings = make_settings()
    monkeypatch.setattr(seed_module, "get_settings", lambda: settings)
    monkeypatch.setattr(seed_module, "create_database", lambda _: database)
    monkeypatch.setattr(database, "close", lambda: None)  # shared fixture; keep it open
    assert seed_module.main() == 0
    assert permissions_repo.count() == 2
