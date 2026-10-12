"""RBAC matrix for every module endpoint: anonymous / internal token / regular user / admin.

``ALLOWED`` means "passes authorization" (any status but 401/403 — e.g. 200, 404
for a random id, 422 for an empty body). Denied principals get exactly 401 / 403.
"""

from __future__ import annotations

import pytest

from router import ROUTERS, load_router

RANDOM_ID = "00000000-0000-4000-8000-000000000000"
ADMIN, AUTH, USER_ONLY = "admin", "auth", "user-only"

# (method, path, kwargs, policy)
#   admin     : superuser only (internal -> 403, user -> 403)
#   auth      : any authenticated principal incl. X-Internal-Token
#   user-only : any authenticated *user* (internal -> 403)
ENDPOINTS = [
    ("POST", "/user/add", {"json": {}}, ADMIN),
    ("PUT", "/user/update", {"json": {"id": RANDOM_ID}}, ADMIN),
    ("DELETE", "/user/delete", {"params": {"id": RANDOM_ID}}, ADMIN),
    ("GET", "/user/get-one", {"params": {"id": RANDOM_ID}}, ADMIN),
    ("GET", "/user/get-by-username", {"params": {"username": "nobody"}}, ADMIN),
    ("POST", "/user/get-all", {"json": {}}, ADMIN),
    ("POST", "/user/reset-password", {"json": {"id": RANDOM_ID, "newPassword": "x" * 12}}, ADMIN),
    ("GET", "/user/check-email", {"params": {"email": "a@b.io"}}, ADMIN),
    ("GET", "/user/check-username", {"params": {"username": "abc"}}, ADMIN),
    ("GET", "/user/check-phone", {"params": {"phone": "0812345678"}}, ADMIN),
    ("PUT", "/user/settings/update-profile", {"json": {"about": "hi"}}, USER_ONLY),
    *[
        row
        for module in ("group", "permission", "role")
        for row in (
            ("POST", f"/{module}/add", {"json": {"name": "x"}}, ADMIN),
            ("PUT", f"/{module}/update", {"json": {"id": RANDOM_ID}}, ADMIN),
            ("DELETE", f"/{module}/delete", {"params": {"id": RANDOM_ID}}, ADMIN),
            ("GET", f"/{module}/get-one", {"params": {"id": RANDOM_ID}}, AUTH),
            ("POST", f"/{module}/get-all", {"json": {}}, AUTH),
        )
    ],
    ("PUT", "/permission/update-partial", {"json": {"id": RANDOM_ID}}, ADMIN),
    ("POST", "/upload/upload-file", {"files": {"file": ("a.txt", b"hello")}}, USER_ONLY),
    ("POST", "/upload/get-all", {"json": {}}, USER_ONLY),
    ("GET", "/upload/get-one", {"params": {"id": RANDOM_ID}}, USER_ONLY),
    ("DELETE", "/upload/delete", {"params": {"id": RANDOM_ID}}, USER_ONLY),
]

EXPECTED = {
    # principal -> policy -> expected status (None = allowed)
    "anon": {ADMIN: 401, AUTH: 401, USER_ONLY: 401},
    "internal": {ADMIN: 403, AUTH: None, USER_ONLY: 403},
    "user": {ADMIN: 403, AUTH: None, USER_ONLY: None},
    "admin": {ADMIN: None, AUTH: None, USER_ONLY: None},
}


def test_matrix_covers_every_module_route():
    declared = {(m, p) for m, p, _, _ in ENDPOINTS}
    mounted = {
        (method, route.path)
        for spec in ROUTERS
        if spec.name in {"user", "group", "permission", "role", "upload"}
        for route in load_router(spec).routes
        for method in route.methods
    }
    assert mounted == declared


@pytest.mark.parametrize("principal", list(EXPECTED))
def test_rbac_matrix(principal, client, fake_storage, admin_headers, user_headers, internal_headers):
    headers = {"anon": {}, "internal": internal_headers, "user": user_headers, "admin": admin_headers}[principal]
    failures = []
    for method, path, kwargs, policy in ENDPOINTS:
        response = client.request(method, path, headers=headers, **kwargs)
        expected = EXPECTED[principal][policy]
        if expected is None:
            ok = response.status_code not in (401, 403)
        else:
            ok = response.status_code == expected
            body = response.json()
            ok = ok and body["data"] is None and body["metaData"]["status"] is False
        if not ok:
            failures.append((method, path, response.status_code, expected))
    assert failures == []


def test_invalid_token_is_401_not_anonymous(client):
    response = client.post("/role/get-all", json={}, headers={"Authorization": "Bearer not-a-jwt"})
    assert response.status_code == 401
    assert response.json()["metaData"]["errorCode"] == "AUTHENTICATION_ERROR"
