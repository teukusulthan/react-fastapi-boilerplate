"""Envelope + global exception handlers, exercised through a throwaway router."""

from __future__ import annotations

from datetime import datetime

import pytest
from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient
from pydantic import EmailStr

from core.errors import (
    AuthenticationError,
    BadRequestError,
    ConfigurationError,
    ConflictError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitedError,
    ValidationError,
)
from core.responses import ApiResponse, Pagination, created, ok, paginated
from dto.common import BaseSchema
from router import HEALTH

router = APIRouter(prefix="/t")


class Item(BaseSchema):
    id: str
    full_name: str
    created_at: datetime | None = None


class Body(BaseSchema):
    email: EmailStr
    full_name: str


ERRORS = {
    "bad": BadRequestError("bad input"),
    "auth": AuthenticationError(),
    "perm": PermissionDeniedError(),
    "missing": NotFoundError("User not found"),
    "conflict": ConflictError("Email exists", details=[{"field": "email", "message": "already exists"}]),
    "validation": ValidationError.for_field("name", "bad name"),
    "limited": RateLimitedError(retry_after=42),
    "config": ConfigurationError(),
}


@router.get("/raise/{kind}")
def raise_kind(kind: str) -> None:
    raise ERRORS[kind]


@router.get("/boom")
def boom() -> None:
    raise RuntimeError("secret database password in message")


@router.get("/http")
def http_error() -> None:
    raise HTTPException(status_code=403, detail="nope")


@router.post("/body", status_code=201, response_model=ApiResponse[Item])
def body(dto: Body):
    return created({"id": "1", "full_name": dto.full_name, "password_hash": "x", "two_factor_secret": "y"})


@router.get("/one", response_model=ApiResponse[Item])
def one():
    return ok({"id": "1", "full_name": "A", "password_hash": "never"}, message="Fetched")


@router.get("/list", response_model=ApiResponse[list[Item]])
def listing():
    return paginated([{"id": str(i), "full_name": f"N{i}"} for i in range(3)], page=2, size=3, total=7)


@pytest.fixture
def app_routers():
    from router import RouterSpec

    return [HEALTH, RouterSpec("t", __name__)]


@pytest.mark.parametrize(
    ("kind", "status", "code"),
    [
        ("bad", 400, "BAD_REQUEST"),
        ("auth", 401, "AUTHENTICATION_ERROR"),
        ("perm", 403, "PERMISSION_ERROR"),
        ("missing", 404, "RESOURCE_NOT_FOUND"),
        ("conflict", 409, "CONFLICT"),
        ("validation", 422, "VALIDATION_ERROR"),
        ("limited", 429, "RATE_LIMITED"),
        ("config", 503, "CONFIGURATION_ERROR"),
    ],
)
def test_app_errors_use_envelope(client: TestClient, kind: str, status: int, code: str) -> None:
    resp = client.get(f"/t/raise/{kind}")
    assert resp.status_code == status
    body = resp.json()
    assert set(body) == {"metaData", "data"}
    meta = body["metaData"]
    assert meta["status"] is False
    assert meta["responseCode"] == status
    assert meta["errorCode"] == code
    assert meta["requestId"] == resp.headers["X-Request-ID"]
    assert isinstance(meta["executionTime"], int)
    assert "copyright" not in body and "detail" not in body


def test_error_details_and_headers(client: TestClient) -> None:
    resp = client.get("/t/raise/conflict")
    assert resp.json()["data"] == [{"field": "email", "message": "already exists"}]
    assert client.get("/t/raise/limited").headers["Retry-After"] == "42"
    assert client.get("/t/raise/auth").headers["WWW-Authenticate"] == "Bearer"
    assert client.get("/t/raise/missing").json()["metaData"]["message"] == "User not found"


def test_request_validation_422_field_list(client: TestClient) -> None:
    resp = client.post("/t/body", json={"email": "not-an-email"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["metaData"]["errorCode"] == "VALIDATION_ERROR"
    fields = {item["field"] for item in body["data"]}
    assert fields == {"email", "fullName"}


def test_unhandled_exception_is_500_without_leak(app) -> None:
    with TestClient(app, raise_server_exceptions=False) as c:
        resp = c.get("/t/boom", headers={"X-Request-ID": "req-123"})
    assert resp.status_code == 500
    assert resp.json()["metaData"] == {
        "status": False,
        "responseCode": 500,
        "message": "Internal server error",
        "errorCode": "INTERNAL_ERROR",
        "executionTime": resp.json()["metaData"]["executionTime"],
        "requestId": "req-123",
    }
    assert "secret" not in resp.text
    assert resp.headers["X-Request-ID"] == "req-123"


def test_http_exception_and_404_405(client: TestClient) -> None:
    assert client.get("/t/http").json()["metaData"]["errorCode"] == "PERMISSION_ERROR"
    assert client.get("/missing").json()["metaData"]["errorCode"] == "RESOURCE_NOT_FOUND"
    resp = client.delete("/t/one")
    assert resp.status_code == 405
    assert resp.json()["metaData"]["errorCode"] == "METHOD_NOT_ALLOWED"


def test_success_envelope_camelcase_and_strips_unknown_fields(client: TestClient) -> None:
    resp = client.post("/t/body", json={"email": "a@b.co", "fullName": "Ann"})
    assert resp.status_code == 201
    body = resp.json()
    assert body["metaData"]["responseCode"] == 201
    assert body["metaData"]["message"] == "Created"
    assert body["metaData"]["pagination"] is None
    assert body["data"] == {"id": "1", "fullName": "Ann", "createdAt": None}
    assert "password" not in resp.text and "two_factor" not in resp.text

    one = client.get("/t/one").json()
    assert one["metaData"]["message"] == "Fetched"
    assert "passwordHash" not in one["data"] and "password_hash" not in one["data"]


def test_paginated_envelope(client: TestClient) -> None:
    body = client.get("/t/list").json()
    assert body["metaData"]["pagination"] == {"page": 2, "size": 3, "totalElements": 7, "totalPages": 3}
    assert [item["id"] for item in body["data"]] == ["0", "1", "2"]


def test_pagination_build_zero() -> None:
    assert Pagination.build(1, 10, 0).total_pages == 0
    assert Pagination.build(1, 10, 11).total_pages == 2
