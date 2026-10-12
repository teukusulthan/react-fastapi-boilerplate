"""Fixtures for the auth tests: all auth routers mounted, emails captured in memory."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from typing import Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core.config import Settings
from router import HEALTH, ROUTERS
from service.auth.deps import get_email_sender
from tests.auth.helpers import PASSWORD, code_from
from util.email import MemoryEmailSender


@pytest.fixture
def app_routers():
    return [HEALTH, *[spec for spec in ROUTERS if spec.name == "auth"]]


@pytest.fixture
def outbox() -> MemoryEmailSender:
    return MemoryEmailSender()


@pytest.fixture
def build_app(make_app: Callable[..., FastAPI], outbox: MemoryEmailSender) -> Callable[..., FastAPI]:
    def factory(app_settings: Settings | None = None) -> FastAPI:
        application = make_app(app_settings)
        application.dependency_overrides[get_email_sender] = lambda: outbox
        return application

    return factory


@pytest.fixture
def app(build_app: Callable[..., FastAPI]) -> FastAPI:
    return build_app()


@pytest.fixture
def make_client(build_app: Callable[..., FastAPI]) -> Iterator[Callable[..., TestClient]]:
    """TestClient for an app built with other settings (``make_client(make_settings(...))``)."""
    clients: list[TestClient] = []

    def factory(app_settings: Settings, **kwargs: Any) -> TestClient:
        client = TestClient(build_app(app_settings), **kwargs)
        client.__enter__()
        clients.append(client)
        return client

    yield factory
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def last_code(outbox: MemoryEmailSender) -> Callable[..., str]:
    def get(address: str | None = None, template: str | None = None) -> str:
        return code_from(outbox.last(address, template))

    return get


@pytest.fixture
def do_login(client: TestClient) -> Callable[..., Any]:
    def login(identifier: str, password: str = PASSWORD, **kwargs: Any):
        return client.post("/auth/login", json={"identifier": identifier, "password": password}, **kwargs)

    return login
