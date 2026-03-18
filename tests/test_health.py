"""Tests for FastAPI application factory and health endpoint."""

import os
from contextlib import asynccontextmanager

import pytest
from httpx import ASGITransport, AsyncClient

from scanner.main import create_app


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Set up environment for test app with temporary DB."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("SCANNER_DB_PATH", db_path)
    monkeypatch.setenv("SCANNER_CONFIG_PATH", str(tmp_path / "nonexistent.yml"))
    return db_path


@asynccontextmanager
async def _lifespan_client(app):
    """Create an async client that properly triggers FastAPI lifespan events."""
    async with app.router.lifespan_context(app):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.fixture
async def client(test_env):
    """Create an async test client with the FastAPI app and active lifespan."""
    app = create_app()
    async with _lifespan_client(app) as ac:
        yield ac


class TestHealthEndpoint:
    @pytest.mark.asyncio
    async def test_health_endpoint_200(self, client):
        """GET /api/health returns 200."""
        resp = await client.get("/api/health")
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_health_response_fields(self, client):
        """Response JSON has keys: status, version, uptime_seconds, database."""
        resp = await client.get("/api/health")
        data = resp.json()
        assert "status" in data
        assert "version" in data
        assert "uptime_seconds" in data
        assert "database" in data

    @pytest.mark.asyncio
    async def test_health_status_healthy(self, client):
        """When DB is accessible, status == 'healthy' and database == 'ok'."""
        resp = await client.get("/api/health")
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["database"] == "ok"

    @pytest.mark.asyncio
    async def test_health_version(self, client):
        """version == '0.1.0'."""
        resp = await client.get("/api/health")
        data = resp.json()
        assert data["version"] == "0.1.0"

    @pytest.mark.asyncio
    async def test_health_uptime_positive(self, client):
        """uptime_seconds >= 0."""
        resp = await client.get("/api/health")
        data = resp.json()
        assert data["uptime_seconds"] >= 0


class TestAppStartup:
    @pytest.mark.asyncio
    async def test_app_creates_tables(self, test_env):
        """After app startup, 'scans' and 'findings' tables exist in the DB."""
        app = create_app()
        async with _lifespan_client(app) as ac:
            await ac.get("/api/health")

        # Verify tables exist by checking the DB directly
        from sqlalchemy import inspect

        from scanner.db.session import create_engine

        engine = create_engine(test_env)
        async with engine.connect() as conn:
            tables = await conn.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )
        await engine.dispose()

        assert "scans" in tables
        assert "findings" in tables
