"""Shared test fixtures for Phase 05: API, Dashboard, CI, and Notifications."""

import os
from contextlib import asynccontextmanager
from datetime import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from scanner.main import create_app
from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.reports.models import DeltaResult
from scanner.schemas.scan import ScanResultSchema


# ---- API test fixtures ----


@pytest.fixture
def test_env(tmp_path, monkeypatch):
    """Set up environment for test app with temporary DB and API key."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("SCANNER_DB_PATH", db_path)
    monkeypatch.setenv("SCANNER_CONFIG_PATH", str(tmp_path / "nonexistent.yml"))
    monkeypatch.setenv("SCANNER_API_KEY", "test-api-key-12345")
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
    """Create an async test client with active lifespan and API key configured."""
    app = create_app()
    async with _lifespan_client(app) as ac:
        yield ac


@pytest.fixture
def api_headers():
    """Return headers with a valid API key."""
    return {"X-API-Key": "test-api-key-12345"}


async def seed_scan(
    session: AsyncSession,
    status: str = "completed",
    total_findings: int = 0,
    **kwargs,
) -> int:
    """Insert a ScanResult row and return the scan ID.

    Args:
        session: Active async database session.
        status: Scan status (default: completed).
        total_findings: Number of total findings.
        **kwargs: Additional ScanResult column overrides.

    Returns:
        The ID of the inserted scan record.
    """
    defaults = {
        "status": status,
        "total_findings": total_findings,
        "target_path": "/tmp/test-project",
        "critical_count": 0,
        "high_count": 0,
        "medium_count": 0,
        "low_count": 0,
        "info_count": 0,
        "started_at": datetime.utcnow(),
        "completed_at": datetime.utcnow(),
        "duration_seconds": 1.5,
    }
    defaults.update(kwargs)
    scan = ScanResult(**defaults)
    session.add(scan)
    await session.flush()
    return scan.id


async def seed_findings(
    session: AsyncSession,
    scan_id: int,
    count: int = 3,
) -> list[str]:
    """Insert N Finding rows for a scan and return their fingerprints.

    Args:
        session: Active async database session.
        scan_id: The scan to attach findings to.
        count: Number of findings to create.

    Returns:
        List of fingerprint strings.
    """
    fingerprints = []
    for i in range(count):
        fp = f"fp{i:060d}"  # 62 char fingerprint
        finding = Finding(
            scan_id=scan_id,
            fingerprint=fp,
            tool="semgrep",
            rule_id=f"test-rule-{i}",
            file_path=f"/src/file{i}.py",
            severity=3,  # MEDIUM
            title=f"Test finding {i}",
        )
        session.add(finding)
        fingerprints.append(fp)
    await session.flush()
    return fingerprints


# ---- Notification / CI test fixtures ----


@pytest.fixture
def scan_result_failed() -> ScanResultSchema:
    """A completed scan result with gate failed."""
    return ScanResultSchema(
        id=1,
        branch="main",
        status="completed",
        duration_seconds=120.5,
        total_findings=10,
        critical_count=1,
        high_count=2,
        medium_count=3,
        low_count=3,
        info_count=1,
        gate_passed=False,
    )


@pytest.fixture
def scan_result_passed() -> ScanResultSchema:
    """A completed scan result with gate passed."""
    return ScanResultSchema(
        id=2,
        branch="main",
        status="completed",
        duration_seconds=45.0,
        total_findings=2,
        critical_count=0,
        high_count=0,
        medium_count=1,
        low_count=1,
        info_count=0,
        gate_passed=True,
    )


@pytest.fixture
def delta() -> DeltaResult:
    """A delta result with 2 new and 1 fixed fingerprint."""
    return DeltaResult(
        new_fingerprints={"fp1", "fp2"},
        fixed_fingerprints={"fp3"},
        persisting_fingerprints={"fp4", "fp5"},
        previous_scan_id=1,
    )
