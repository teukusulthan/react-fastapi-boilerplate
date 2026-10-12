"""/user: CRUD, PATCH semantics, references, uniqueness, query whitelists, guards, self-profile."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from core.deps import CurrentUser
from core.errors import ConflictError
from core.security import verify_password
from service.user import UserService

MISSING = "00000000-0000-4000-8000-000000000000"
NEW_USER = {
    "username": "bob",
    "fullname": "Bob Builder",
    "email": "Bob@Example.COM",
    "phone": "+62811111111",
    "password": "correct-horse-battery",
}


def _add(client, headers, **overrides):
    return client.post("/user/add", json={**NEW_USER, **overrides}, headers=headers)


# ----------------------------------------------------------------- create
def test_create_user_hashes_password_and_hides_secrets(client, admin_headers, admin_user, users_repo, user_permission):
    response = _add(client, admin_headers, permissionId=user_permission["id"])
    assert response.status_code == 201
    body = response.json()
    assert body["metaData"]["responseCode"] == 201
    user = body["data"]
    assert user["email"] == "bob@example.com"
    assert user["role"] == "user" and user["permission"]["alias"] == "user"
    assert user["status"] == "active" and user["createdBy"] == admin_user["id"]
    assert not {"password", "passwordHash", "password_hash", "twoFactorSecret"} & set(user)
    stored = users_repo.get_by_id(user["id"])
    assert stored["password_hash"] != NEW_USER["password"]
    assert verify_password(NEW_USER["password"], stored["password_hash"])


def test_create_user_defaults_to_default_permission(client, admin_headers, user_permission):
    omitted = _add(client, admin_headers)
    assert omitted.status_code == 201
    assert omitted.json()["data"]["permissionId"] == user_permission["id"]  # BE_DEFAULT_PERMISSION_ALIAS
    explicit_none = _add(
        client, admin_headers, username="carol", email="carol@example.com", phone=None, permissionId=None
    )
    assert explicit_none.status_code == 201
    assert explicit_none.json()["data"]["permissionId"] is None


@pytest.mark.parametrize(
    ("overrides", "field"),
    [
        ({"password": "short"}, "password"),
        ({"password": None}, "password"),
        ({"email": "not-an-email"}, "email"),
        ({"username": "a b"}, "username"),
        ({"status": "superadmin"}, "status"),
        ({"role": "admin"}, "role"),
        ({"createdBy": "someone"}, "createdBy"),
        ({"passwordHash": "x"}, "passwordHash"),
    ],
)
def test_create_user_validation(client, admin_headers, overrides, field):
    response = _add(client, admin_headers, **overrides)
    assert response.status_code == 422
    assert field in [item["field"] for item in response.json()["data"]]


def test_create_user_references_must_exist(client, admin_headers):
    response = _add(client, admin_headers, permissionId=MISSING, groupId="junk")
    assert response.status_code == 422
    assert {d["field"] for d in response.json()["data"]} == {"permissionId", "groupId"}


def test_create_user_duplicates_conflict(client, admin_headers, admin_user):
    assert _add(client, admin_headers).status_code == 201
    response = _add(client, admin_headers, username="bob2", email="BOB@example.com", phone="+62811111111")
    assert response.status_code == 409
    body = response.json()
    assert body["metaData"]["errorCode"] == "CONFLICT"
    assert {d["field"] for d in body["data"]} == {"email", "phone"}


# ----------------------------------------------------------------- update
def test_update_is_patch(client, admin_headers, regular_user, groups_repo, users_repo):
    group = groups_repo.insert({"name": "Ops"})
    users_repo.update(regular_user["id"], {"group_id": group["id"], "about": "keep me"})
    response = client.put(
        "/user/update", json={"id": regular_user["id"], "fullname": "Alice A."}, headers=admin_headers
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["fullname"] == "Alice A."
    assert data["about"] == "keep me" and data["groupId"] == group["id"]  # untouched

    cleared = client.put("/user/update", json={"id": regular_user["id"], "groupId": None}, headers=admin_headers)
    assert cleared.status_code == 200 and cleared.json()["data"]["groupId"] is None
    assert users_repo.get_by_id(regular_user["id"])["about"] == "keep me"


def test_update_rejects_null_required_and_unknown_fields(client, admin_headers, regular_user):
    for body in ({"username": None}, {"status": None}, {"password": "new-password-1"}, {"role": "admin"}):
        response = client.put("/user/update", json={"id": regular_user["id"], **body}, headers=admin_headers)
        assert response.status_code == 422, body


def test_update_missing_user_404(client, admin_headers):
    response = client.put("/user/update", json={"id": MISSING, "fullname": "x"}, headers=admin_headers)
    assert response.status_code == 404
    assert response.json()["metaData"]["errorCode"] == "RESOURCE_NOT_FOUND"


def test_update_unique_conflict(client, admin_headers, regular_user, admin_user):
    response = client.put(
        "/user/update", json={"id": regular_user["id"], "username": admin_user["username"]}, headers=admin_headers
    )
    assert response.status_code == 409


def test_blocking_a_user_revokes_their_tokens(client, admin_headers, regular_user, auth_headers):
    headers = auth_headers(regular_user)
    assert client.put("/user/settings/update-profile", json={}, headers=headers).status_code == 200
    response = client.put("/user/update", json={"id": regular_user["id"], "status": "blocked"}, headers=admin_headers)
    assert response.status_code == 200
    client.put("/user/update", json={"id": regular_user["id"], "status": "active"}, headers=admin_headers)
    # Re-activated, but the old token was revoked when the user was blocked.
    assert client.put("/user/settings/update-profile", json={}, headers=headers).status_code == 401


# ------------------------------------------------------------------ reads
def test_get_one_and_by_username(client, admin_headers, regular_user):
    one = client.get("/user/get-one", params={"id": regular_user["id"]}, headers=admin_headers)
    assert one.status_code == 200 and one.json()["data"]["username"] == "alice"
    assert "passwordHash" not in one.json()["data"]
    by_name = client.get("/user/get-by-username", params={"username": "alice"}, headers=admin_headers)
    assert by_name.json()["data"]["id"] == regular_user["id"]
    assert client.get("/user/get-one", params={"id": MISSING}, headers=admin_headers).status_code == 404
    assert client.get("/user/get-by-username", params={"username": "ghost"}, headers=admin_headers).status_code == 404
    assert client.get("/user/alice", headers=admin_headers).status_code == 404  # no catch-all route


def test_get_all_pagination_search_and_relations(client, admin_headers, user_factory, user_permission):
    for i in range(5):
        user_factory(username=f"member{i}", fullname=f"Member {i}", permission=user_permission)
    page = client.post("/user/get-all", json={"page": 2, "size": 2}, headers=admin_headers)
    assert page.status_code == 200
    body = page.json()
    assert body["metaData"]["pagination"] == {"page": 2, "size": 2, "totalElements": 6, "totalPages": 3}
    assert len(body["data"]) == 2

    found = client.post("/user/get-all", json={"search": "MEMBER 3"}, headers=admin_headers).json()
    assert [u["username"] for u in found["data"]] == ["member3"]
    assert found["data"][0]["permission"]["alias"] == "user"

    by_email = client.post(
        "/user/get-all", json={"search": "member1@", "searchBy": ["email"]}, headers=admin_headers
    ).json()
    assert by_email["metaData"]["pagination"]["totalElements"] == 0  # factory emails are userN@example.com

    filtered = client.post(
        "/user/get-all",
        json={
            "filters": [{"field": "username", "operator": "is one of", "value": {"isOneOf": ["member0", "member4"]}}],
            "orderBy": "username",
            "order": "ASC",
        },
        headers=admin_headers,
    ).json()
    assert [u["username"] for u in filtered["data"]] == ["member0", "member4"]


@pytest.mark.parametrize(
    "body",
    [
        {"filters": [{"field": "passwordHash", "operator": "is exist"}]},
        {"filters": [{"field": "password_hash", "operator": "is", "value": {"is": "x"}}]},
        {"filters": [{"field": "about", "operator": "is", "value": {"is": "x"}}]},
        {"filters": [{"field": "email", "operator": "is", "value": {"is": {"$ne": None}}}]},
        {"filters": [{"field": "email", "operator": "$where", "value": {"is": "1"}}]},
        {"filters": [{"field": "status", "operator": "is one of", "value": {"isOneOf": [{"$gt": ""}]}}]},
        {"searchBy": ["twoFactorSecret"], "search": "a"},
        {"orderBy": "passwordHash"},
        {"size": 0},
        {"size": 101},
        {"page": 0},
        {"search": "x" * 201},
    ],
)
def test_get_all_rejects_unsafe_queries(client, admin_headers, body):
    response = client.post("/user/get-all", json=body, headers=admin_headers)
    assert response.status_code == 422
    assert response.json()["metaData"]["errorCode"] == "VALIDATION_ERROR"


def test_search_is_literal_not_regex(client, admin_headers, user_factory):
    user_factory(username="dot.user", fullname="a.*b")
    user_factory(username="plain", fullname="axxb")
    data = client.post("/user/get-all", json={"search": "a.*b"}, headers=admin_headers).json()["data"]
    assert [u["username"] for u in data] == ["dot.user"]


def test_check_availability(client, admin_headers, regular_user, users_repo):
    users_repo.update(regular_user["id"], {"phone": "+6281234567"})
    cases = [
        ("/user/check-email", {"email": "ALICE@example.com"}, True),
        ("/user/check-email", {"email": "free@example.com"}, False),
        ("/user/check-username", {"username": "alice"}, True),
        ("/user/check-username", {"username": "nobody"}, False),
        ("/user/check-phone", {"phone": "+6281234567"}, True),
    ]
    for path, params, exists in cases:
        data = client.get(path, params=params, headers=admin_headers).json()["data"]
        assert data["exists"] is exists and data["available"] is (not exists), (path, params)


# ---------------------------------------------------------------- delete
def test_delete_user_and_revoke(client, admin_headers, regular_user, auth_headers, users_repo):
    headers = auth_headers(regular_user)
    response = client.delete("/user/delete", params={"id": regular_user["id"]}, headers=admin_headers)
    assert response.status_code == 200 and response.json()["data"] == {"message": "User deleted"}
    assert users_repo.get_by_id(regular_user["id"]) is None
    assert client.put("/user/settings/update-profile", json={}, headers=headers).status_code == 401
    assert client.delete("/user/delete", params={"id": regular_user["id"]}, headers=admin_headers).status_code == 404


def test_admin_cannot_delete_or_demote_self(client, admin_headers, admin_user, user_permission):
    assert client.delete("/user/delete", params={"id": admin_user["id"]}, headers=admin_headers).status_code == 409
    for change in (
        {"permissionId": user_permission["id"]},
        {"status": "blocked"},
        {"expiredAt": "2000-01-01T00:00:00Z"},
    ):
        response = client.put("/user/update", json={"id": admin_user["id"], **change}, headers=admin_headers)
        assert response.status_code == 409, change
    # harmless self-edits are fine
    assert (
        client.put("/user/update", json={"id": admin_user["id"], "fullname": "Root"}, headers=admin_headers).status_code
        == 200
    )


def test_admin_can_demote_another_admin(client, admin_headers, user_factory, admin_permission, user_permission):
    other = user_factory(permission=admin_permission)
    response = client.put(
        "/user/update", json={"id": other["id"], "permissionId": user_permission["id"]}, headers=admin_headers
    )
    assert response.status_code == 200 and response.json()["data"]["role"] == "user"


def test_last_superuser_guard(users_repo, permissions_repo, groups_repo, settings, redis_client, admin_user):
    from core.security import TokenStore

    service = UserService(users_repo, permissions_repo, groups_repo, settings, TokenStore(redis_client, settings))
    internal = CurrentUser.internal()
    with pytest.raises(ConflictError, match="last active administrator"):
        service.delete_user(admin_user["id"], internal)
    from dto.user import UpdateUserDTO

    with pytest.raises(ConflictError, match="last active administrator"):
        service.update_user(UpdateUserDTO(id=admin_user["id"], status="blocked"), internal)


# ---------------------------------------------------------- reset password
def test_reset_password_revokes_sessions(client, admin_headers, regular_user, auth_headers, users_repo):
    headers = auth_headers(regular_user)
    response = client.post(
        "/user/reset-password",
        json={"id": regular_user["id"], "newPassword": "brand-new-password"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"] == {"message": "Password has been reset"}
    assert verify_password("brand-new-password", users_repo.get_by_id(regular_user["id"])["password_hash"])
    assert client.put("/user/settings/update-profile", json={}, headers=headers).status_code == 401
    # fresh login works
    assert client.put("/user/settings/update-profile", json={}, headers=auth_headers(regular_user)).status_code == 200


def test_reset_password_validation(client, admin_headers, regular_user):
    weak = client.post(
        "/user/reset-password", json={"id": regular_user["id"], "newPassword": "x"}, headers=admin_headers
    )
    assert weak.status_code == 422 and weak.json()["data"][0]["field"] == "newPassword"
    missing = client.post(
        "/user/reset-password", json={"id": MISSING, "newPassword": "long-enough-1"}, headers=admin_headers
    )
    assert missing.status_code == 404


# -------------------------------------------------------------- self profile
def test_update_profile_whitelist(client, user_headers, regular_user, users_repo):
    response = client.put(
        "/user/settings/update-profile",
        json={"fullname": "Alice Liddell", "about": "hi", "settings": {"theme": "dark"}},
        headers=user_headers,
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["fullname"] == "Alice Liddell" and data["settings"] == {"theme": "dark"}
    assert data["id"] == regular_user["id"]

    for forbidden in (
        {"permissionId": MISSING},
        {"role": "admin"},
        {"status": "active"},
        {"email": "x@y.io"},
        {"username": "root"},
        {"id": MISSING},
        {"password": "whatever-123"},
    ):
        response = client.put("/user/settings/update-profile", json=forbidden, headers=user_headers)
        assert response.status_code == 422, forbidden
    stored = users_repo.get_by_id(regular_user["id"])
    assert stored["permission_id"] == regular_user["permission_id"] and stored["status"] == "active"


def test_update_profile_phone_conflict(client, user_headers, user_factory):
    user_factory(phone="+628999999")
    response = client.put("/user/settings/update-profile", json={"phone": "+628999999"}, headers=user_headers)
    assert response.status_code == 409


def test_supabase_mode_rejects_local_passwords(make_app, make_settings, admin_headers):
    from fastapi.testclient import TestClient

    app = make_app(make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET="s" * 40))
    with TestClient(app) as client:
        # local tokens are not accepted in supabase mode; exercise the service rule directly instead
        assert client.post("/user/get-all", json={}, headers=admin_headers).status_code == 401


def test_supabase_mode_service_rules(users_repo, permissions_repo, groups_repo, make_settings, redis_client):
    from core.errors import BadRequestError, ValidationError
    from core.security import TokenStore
    from dto.user import CreateUserDTO, ResetPasswordDTO

    settings = make_settings(AUTH_PROVIDER="supabase", SUPABASE_JWT_SECRET="s" * 40)
    service = UserService(users_repo, permissions_repo, groups_repo, settings, TokenStore(redis_client, settings))
    actor = CurrentUser(id="admin-id", is_superuser=True)
    created = service.create_user(CreateUserDTO(username="sbuser", fullname="Sb", email="sb@x.io"), actor)
    assert created.auth_provider == "supabase"
    assert users_repo.get_by_id(created.id)["password_hash"] is None
    with pytest.raises(ValidationError):
        service.create_user(
            CreateUserDTO(username="sbuser2", fullname="Sb", email="sb2@x.io", password="pw-123456"), actor
        )
    with pytest.raises(BadRequestError):
        service.reset_password(ResetPasswordDTO(id=created.id, new_password="pw-123456"), actor)


def test_page_size_limit_comes_from_the_serving_app_settings(make_app, make_settings, admin_headers):
    """FindDTO must use the app's own MAX_PAGE_SIZE, not the process-global settings."""
    app = make_app(app_settings=make_settings(MAX_PAGE_SIZE=5))
    with TestClient(app) as small_client:
        assert small_client.post("/user/get-all", json={"size": 5}, headers=admin_headers).status_code == 200
        response = small_client.post("/user/get-all", json={"size": 6}, headers=admin_headers)
    assert response.status_code == 422
    assert response.json()["metaData"]["errorCode"] == "VALIDATION_ERROR"
