"""Shared test fixtures for Phase 15: Scan Profiles."""

import hashlib
import os
import secrets
from contextlib import asynccontextmanager

import pytest
import yaml
from httpx import ASGITransport, AsyncClient

from scanner.main import create_app


TEST_ADMIN_USER = "testadmin"
TEST_ADMIN_PASSWORD = "testpass123"
TEST_SECRET_KEY = "test-secret-key-for-jwt-signing"

TEST_CONFIG = {
    "scanners": {
        "semgrep": {
            "enabled": "auto",
            "timeout": 180,
            "extra_args": ["--exclude", ".venv"],
            "adapter_class": "scanner.adapters.semgrep.SemgrepAdapter",
            "languages": ["python", "javascript"],
        },
        "gitleaks": {
            "enabled": True,
            "timeout": 120,
            "extra_args": [],
            "adapter_class": "scanner.adapters.gitleaks.GitleaksAdapter",
            "languages": [],
        },
        "nuclei": {
            "enabled": True,
            "timeout": 300,
            "extra_args": [],
            "adapter_class": "scanner.adapters.nuclei.NucleiAdapter",
            "languages": [],
        },
    },
    "profiles": {
        "quick_scan": {
            "description": "Fast scan with essential tools only",
            "scanners": {
                "semgrep": {},
            },
        },
    },
    "ai": {"model": "claude-sonnet-4-6", "max_cost_per_scan": 5.0},
    "gate": {"fail_on": ["critical", "high"]},
}


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Set up environment for test app with admin bootstrap and config.yml."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("SCANNER_DB_PATH", db_path)

    # Write test config.yml
    config_path = str(tmp_path / "config.yml")
    with open(config_path, "w") as f:
        yaml.dump(TEST_CONFIG, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
    monkeypatch.setenv("SCANNER_CONFIG_PATH", config_path)

    monkeypatch.setenv("SCANNER_ADMIN_USER", TEST_ADMIN_USER)
    monkeypatch.setenv("SCANNER_ADMIN_PASSWORD", TEST_ADMIN_PASSWORD)
    monkeypatch.setenv("SCANNER_SECRET_KEY", TEST_SECRET_KEY)
    return db_path


@asynccontextmanager
async def _lifespan_client(app):
    """Create an async client that properly triggers FastAPI lifespan events."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
async def auth_client(test_env):
    """Create test client with active lifespan and admin user bootstrapped."""
    app = create_app()
    async with _lifespan_client(app) as ac:
        yield ac


@pytest.fixture
def config_path(test_env, tmp_path):
    """Return path to the test config.yml for assertions."""
    return str(tmp_path / "config.yml")


async def get_admin_token(client):
    """Helper: generate an API token for the bootstrapped admin user."""
    # Login to get session cookie
    resp = await client.post(
        "/dashboard/login",
        data={"username": TEST_ADMIN_USER, "password": TEST_ADMIN_PASSWORD},
        follow_redirects=False,
    )
    cookies = resp.cookies

    # Create token via API using session cookie
    resp = await client.post(
        "/api/tokens",
        json={"name": "test-token"},
        cookies=cookies,
    )
    if resp.status_code == 200:
        return resp.json()["raw_token"]

    # Fallback: create token directly in DB
    import hashlib
    import secrets as sec
    from scanner.models.user import APIToken, User
    from sqlalchemy import select

    app = client._transport.app  # type: ignore
    async with app.state.session_factory() as session:
        result = await session.execute(
            select(User).where(User.username == TEST_ADMIN_USER)
        )
        user = result.scalar_one()
        raw = f"nvsec_{sec.token_hex(32)}"
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        token = APIToken(
            user_id=user.id,
            token_hash=token_hash,
            name="test-admin-token",
        )
        session.add(token)
        await session.commit()
    return raw


async def create_test_user(client, username, password, role="viewer"):
    """Helper: create a user via API and return the response."""
    admin_token = await get_admin_token(client)
    resp = await client.post(
        "/api/users",
        json={"username": username, "password": password, "role": role},
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    return resp


async def get_user_token(client, username, role="viewer"):
    """Helper: create a user and return a Bearer token for them."""
    import secrets as sec
    from scanner.models.user import APIToken, User
    from sqlalchemy import select

    # Create user first
    await create_test_user(client, username, "password123", role)

    # Create token directly in DB
    app = client._transport.app  # type: ignore
    async with app.state.session_factory() as session:
        result = await session.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one()
        raw = f"nvsec_{sec.token_hex(32)}"
        token_hash = hashlib.sha256(raw.encode()).hexdigest()
        token = APIToken(
            user_id=user.id,
            token_hash=token_hash,
            name=f"{role}-test-token",
        )
        session.add(token)
        await session.commit()
    return raw
