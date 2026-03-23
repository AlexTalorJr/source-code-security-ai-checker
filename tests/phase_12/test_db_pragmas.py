"""Tests for SQLite pragma configuration (INFRA-03)."""

import aiosqlite
import pytest


@pytest.mark.asyncio
async def test_busy_timeout(auth_client):
    """Verify busy_timeout=5000 is set on database connections."""
    app = auth_client._transport.app  # type: ignore
    async with app.state.engine.connect() as conn:
        result = await conn.exec_driver_sql("PRAGMA busy_timeout")
        row = result.fetchone()
        assert row is not None
        assert row[0] == 5000, f"Expected busy_timeout=5000, got {row[0]}"


@pytest.mark.asyncio
async def test_wal_mode(auth_client):
    """Verify WAL journal mode is still enabled."""
    app = auth_client._transport.app  # type: ignore
    async with app.state.engine.connect() as conn:
        result = await conn.exec_driver_sql("PRAGMA journal_mode")
        row = result.fetchone()
        assert row is not None
        assert row[0].lower() == "wal"


@pytest.mark.asyncio
async def test_foreign_keys(auth_client):
    """Verify foreign keys are enabled."""
    app = auth_client._transport.app  # type: ignore
    async with app.state.engine.connect() as conn:
        result = await conn.exec_driver_sql("PRAGMA foreign_keys")
        row = result.fetchone()
        assert row is not None
        assert row[0] == 1
