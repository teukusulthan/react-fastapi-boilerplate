"""/group and /role: CRUD, PATCH semantics, hierarchy, references, query whitelists."""

from __future__ import annotations

import pytest

MISSING = "00000000-0000-4000-8000-000000000000"


@pytest.mark.parametrize("module", ["group", "role"])
def test_crud_roundtrip(module, client, admin_headers, admin_user, user_headers):
    created = client.post(f"/{module}/add", json={"name": "Alpha", "description": "first"}, headers=admin_headers)
    assert created.status_code == 201
    record = created.json()["data"]
    assert record["name"] == "Alpha" and record["createdBy"] == admin_user["id"]
    assert set(record) >= {"id", "createdAt", "updatedAt", "parentId"}

    updated = client.put(f"/{module}/update", json={"id": record["id"], "name": "Beta"}, headers=admin_headers)
    assert updated.status_code == 200 and updated.json()["metaData"]["message"] == "Updated"
    assert updated.json()["data"]["description"] == "first"  # PATCH: untouched

    got = client.get(f"/{module}/get-one", params={"id": record["id"]}, headers=user_headers)
    assert got.json()["data"]["name"] == "Beta"
    listed = client.post(f"/{module}/get-all", json={"search": "bet"}, headers=user_headers).json()
    assert listed["metaData"]["pagination"]["totalElements"] == 1

    deleted = client.delete(f"/{module}/delete", params={"id": record["id"]}, headers=admin_headers)
    assert deleted.status_code == 200
    for method, kwargs in (
        ("GET", {"params": {"id": record["id"]}}),
        ("DELETE", {"params": {"id": record["id"]}}),
    ):
        path = f"/{module}/get-one" if method == "GET" else f"/{module}/delete"
        assert client.request(method, path, headers=admin_headers, **kwargs).status_code == 404
    assert client.put(f"/{module}/update", json={"id": MISSING, "name": "x"}, headers=admin_headers).status_code == 404


@pytest.mark.parametrize("module", ["group", "role"])
def test_validation(module, client, admin_headers, admin_user):
    for body in ({}, {"name": ""}, {"name": "x", "unknown": 1}, {"name": "x", "createdBy": "me"}, {"name": "x" * 101}):
        assert client.post(f"/{module}/add", json=body, headers=admin_headers).status_code == 422, body
    assert (
        client.post(f"/{module}/add", json={"name": "x", "parentId": MISSING}, headers=admin_headers).status_code == 422
    )
    record = client.post(f"/{module}/add", json={"name": "x"}, headers=admin_headers).json()["data"]
    response = client.put(f"/{module}/update", json={"id": record["id"], "name": None}, headers=admin_headers)
    assert response.status_code == 422


@pytest.mark.parametrize("module", ["group", "role"])
def test_hierarchy(module, client, admin_headers, admin_user):
    def add(name, parent=None):
        body = {"name": name, **({"parentId": parent} if parent else {})}
        return client.post(f"/{module}/add", json=body, headers=admin_headers).json()["data"]

    root = add("root")
    child = add("child", root["id"])
    grandchild = add("grandchild", child["id"])
    cycle = client.put(
        f"/{module}/update", json={"id": root["id"], "parentId": grandchild["id"]}, headers=admin_headers
    )
    assert cycle.status_code == 422
    assert client.delete(f"/{module}/delete", params={"id": child["id"]}, headers=admin_headers).status_code == 200
    got = client.get(f"/{module}/get-one", params={"id": grandchild["id"]}, headers=admin_headers).json()["data"]
    assert got["parentId"] is None


def test_group_in_use_cannot_be_deleted(client, admin_headers, regular_user, groups_repo, users_repo):
    group = groups_repo.insert({"name": "Team"})
    users_repo.update(regular_user["id"], {"group_id": group["id"]})
    response = client.delete("/group/delete", params={"id": group["id"]}, headers=admin_headers)
    assert response.status_code == 409 and response.json()["metaData"]["errorCode"] == "CONFLICT"


def test_group_json_fields(client, admin_headers, admin_user):
    body = {"name": "G", "settings": {"theme": "dark"}, "filters": [{"field": "status", "operator": "is"}]}
    data = client.post("/group/add", json=body, headers=admin_headers).json()["data"]
    assert data["settings"] == {"theme": "dark"} and data["filters"] == [{"field": "status", "operator": "is"}]
    assert client.post("/group/add", json={"name": "G", "filters": {"x": 1}}, headers=admin_headers).status_code == 422


def test_role_position_filter_and_sort(client, admin_headers, admin_user, user_headers):
    for i, name in enumerate(["low", "mid", "high"]):
        client.post("/role/add", json={"name": name, "rolePosition": i * 10}, headers=admin_headers)
    body = {
        "filters": [{"field": "rolePosition", "operator": "greater than equals", "value": {"gte": 10}}],
        "orderBy": "rolePosition",
        "order": "desc",
    }
    data = client.post("/role/get-all", json=body, headers=user_headers).json()["data"]
    assert [r["name"] for r in data] == ["high", "mid"]
    bad = client.post("/role/add", json={"name": "x", "rolePosition": "first"}, headers=admin_headers)
    assert bad.status_code == 422
    not_filterable = client.post(
        "/role/get-all", json={"filters": [{"field": "description", "operator": "is exist"}]}, headers=user_headers
    )
    assert not_filterable.status_code == 422
    assert not_filterable.json()["data"] == [
        {"field": "filters[0].field", "message": "'description' is not a filterable field"}
    ]
