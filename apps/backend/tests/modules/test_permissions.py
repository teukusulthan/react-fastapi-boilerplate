"""/permission: CRUD, alias uniqueness, privilege add/remove, references and lockout guards."""

from __future__ import annotations

MISSING = "00000000-0000-4000-8000-000000000000"


def _add(client, headers, **body):
    return client.post("/permission/add", json={"name": "Editor", **body}, headers=headers)


def test_permission_crud(client, admin_headers, admin_user, user_headers, internal_headers):
    created = _add(client, admin_headers, alias=" Editor ", privileges=["post:write", "post:write", "post:read"])
    assert created.status_code == 201
    perm = created.json()["data"]
    assert perm["alias"] == "editor" and perm["privileges"] == ["post:write", "post:read"]
    assert perm["createdBy"] == admin_user["id"]

    updated = client.put("/permission/update", json={"id": perm["id"], "description": "Edits"}, headers=admin_headers)
    assert updated.status_code == 200
    assert updated.json()["data"]["description"] == "Edits"
    assert updated.json()["data"]["privileges"] == ["post:write", "post:read"]  # PATCH: untouched

    for headers in (user_headers, internal_headers):  # reads: any authenticated principal
        got = client.get("/permission/get-one", params={"id": perm["id"]}, headers=headers)
        assert got.status_code == 200 and got.json()["data"]["name"] == "Editor"

    listed = client.post(
        "/permission/get-all",
        json={"filters": [{"field": "privileges", "operator": "is", "value": {"is": "post:read"}}]},
        headers=user_headers,
    ).json()
    assert [p["alias"] for p in listed["data"]] == ["editor"]

    assert client.delete("/permission/delete", params={"id": perm["id"]}, headers=admin_headers).status_code == 200
    assert client.get("/permission/get-one", params={"id": perm["id"]}, headers=admin_headers).status_code == 404


def test_permission_validation_and_conflicts(client, admin_headers, admin_user):
    assert _add(client, admin_headers, alias="dup").status_code == 201
    conflict = _add(client, admin_headers, alias="DUP")
    assert conflict.status_code == 409 and conflict.json()["data"][0]["field"] == "alias"
    for body in ({"alias": "has space"}, {"privileges": ["ok", "has space"]}, {"name": ""}, {"createdBy": "x"}):
        assert _add(client, admin_headers, **body).status_code == 422, body
    assert _add(client, admin_headers, parentId=MISSING).status_code == 422
    response = client.put("/permission/update", json={"id": MISSING, "name": "x"}, headers=admin_headers)
    assert response.status_code == 404
    perm = _add(client, admin_headers).json()["data"]
    response = client.put("/permission/update", json={"id": perm["id"], "name": None}, headers=admin_headers)
    assert response.status_code == 422


def test_update_partial_adds_and_removes(client, admin_headers, admin_user):
    perm = _add(client, admin_headers, privileges=["a", "b"]).json()["data"]
    response = client.put(
        "/permission/update-partial",
        json={"id": perm["id"], "addPrivileges": ["c", "a"], "removePrivileges": ["b"]},
        headers=admin_headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["privileges"] == ["a", "c"]


def test_delete_referenced_permission_conflicts(client, admin_headers, regular_user, user_permission):
    response = client.delete("/permission/delete", params={"id": user_permission["id"]}, headers=admin_headers)
    assert response.status_code == 409
    assert "1 user" in response.json()["metaData"]["message"]


def test_delete_detaches_children_and_rejects_cycles(client, admin_headers, admin_user, permissions_repo):
    parent = _add(client, admin_headers, name="Parent").json()["data"]
    child = _add(client, admin_headers, name="Child", parentId=parent["id"]).json()["data"]
    cycle = client.put("/permission/update", json={"id": parent["id"], "parentId": child["id"]}, headers=admin_headers)
    assert cycle.status_code == 422 and cycle.json()["data"][0]["field"] == "parentId"
    own = client.put("/permission/update", json={"id": parent["id"], "parentId": parent["id"]}, headers=admin_headers)
    assert own.status_code == 422
    assert client.delete("/permission/delete", params={"id": parent["id"]}, headers=admin_headers).status_code == 200
    assert permissions_repo.get_by_id(child["id"])["parent_id"] is None


def test_admin_cannot_rename_own_superuser_alias(client, admin_headers, admin_permission, user_factory):
    response = client.put(
        "/permission/update", json={"id": admin_permission["id"], "alias": "staff"}, headers=admin_headers
    )
    assert response.status_code == 409
    # another superuser permission held by another admin can be renamed while we stay admin
    owner = client.post("/permission/add", json={"name": "Owner", "alias": "owner"}, headers=admin_headers).json()
    user_factory(permission=owner["data"])
    renamed = client.put(
        "/permission/update", json={"id": owner["data"]["id"], "alias": "co-owner"}, headers=admin_headers
    )
    assert renamed.status_code == 200
