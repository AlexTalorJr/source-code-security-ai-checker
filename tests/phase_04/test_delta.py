"""Tests for delta comparison module (fingerprint set operations)."""

import pytest
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from scanner.models.base import Base
from scanner.models.finding import Finding
from scanner.models.scan import ScanResult
from scanner.reports.delta import compute_delta, get_previous_scan_fingerprints
from scanner.reports.models import DeltaResult
from scanner.schemas.finding import FindingSchema
from scanner.schemas.severity import Severity

# Import compound risk model so relationships resolve
import scanner.models.compound_risk  # noqa: F401


FP_A = "a" * 64
FP_B = "b" * 64
FP_C = "c" * 64
FP_D = "d" * 64


def _make_finding_schema(fingerprint: str) -> FindingSchema:
    """Create a minimal FindingSchema with given fingerprint."""
    return FindingSchema(
        fingerprint=fingerprint,
        tool="semgrep",
        rule_id="test-rule",
        file_path="src/app.py",
        severity=Severity.MEDIUM,
        title="Test finding",
    )


@pytest.fixture
async def db_session():
    """Create in-memory SQLite async session with tables."""
    engine = create_async_engine("sqlite+aiosqlite://", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest.fixture
async def seeded_session(db_session):
    """Session with a previous completed scan on branch 'release/v2.1' having findings A, B, C."""
    async with db_session.begin():
        prev_scan = ScanResult(
            branch="release/v2.1",
            status="completed",
            total_findings=3,
        )
        db_session.add(prev_scan)
        await db_session.flush()

        for fp in [FP_A, FP_B, FP_C]:
            db_session.add(Finding(
                scan_id=prev_scan.id,
                fingerprint=fp,
                tool="semgrep",
                rule_id="test-rule",
                file_path="src/app.py",
                severity=3,
                title="Test finding",
            ))

    return db_session, prev_scan.id


@pytest.mark.asyncio
async def test_delta_new_fixed_persisting(seeded_session):
    """Current scan with B,C,D vs previous A,B,C yields new={D}, fixed={A}, persisting={B,C}."""
    session, prev_scan_id = seeded_session

    # Create current scan
    async with session.begin():
        current_scan = ScanResult(
            branch="release/v2.1",
            status="completed",
            total_findings=3,
        )
        session.add(current_scan)
        await session.flush()

        for fp in [FP_B, FP_C, FP_D]:
            session.add(Finding(
                scan_id=current_scan.id,
                fingerprint=fp,
                tool="semgrep",
                rule_id="test-rule",
                file_path="src/app.py",
                severity=3,
                title="Test finding",
            ))

    current_findings = [_make_finding_schema(fp) for fp in [FP_B, FP_C, FP_D]]

    result = await compute_delta(
        current_findings=current_findings,
        branch="release/v2.1",
        current_scan_id=current_scan.id,
        session=session,
    )

    assert result is not None
    assert result.new_fingerprints == {FP_D}
    assert result.fixed_fingerprints == {FP_A}
    assert result.persisting_fingerprints == {FP_B, FP_C}
    assert result.previous_scan_id == prev_scan_id


@pytest.mark.asyncio
async def test_delta_first_scan_returns_none(db_session):
    """compute_delta for branch with no previous scan returns None."""
    current_findings = [_make_finding_schema(FP_A)]

    # Create current scan on a new branch
    async with db_session.begin():
        current_scan = ScanResult(
            branch="feature/new",
            status="completed",
            total_findings=1,
        )
        db_session.add(current_scan)
        await db_session.flush()

    result = await compute_delta(
        current_findings=current_findings,
        branch="feature/new",
        current_scan_id=current_scan.id,
        session=db_session,
    )

    assert result is None


@pytest.mark.asyncio
async def test_delta_no_branch_returns_none(db_session):
    """compute_delta with branch=None returns None."""
    current_findings = [_make_finding_schema(FP_A)]

    result = await compute_delta(
        current_findings=current_findings,
        branch=None,
        current_scan_id=1,
        session=db_session,
    )

    assert result is None


@pytest.mark.asyncio
async def test_delta_excludes_current_scan(db_session):
    """Current scan's own findings must not be treated as 'previous'."""
    async with db_session.begin():
        # Only one scan exists -- the current one
        current_scan = ScanResult(
            branch="release/v2.1",
            status="completed",
            total_findings=2,
        )
        db_session.add(current_scan)
        await db_session.flush()

        for fp in [FP_A, FP_B]:
            db_session.add(Finding(
                scan_id=current_scan.id,
                fingerprint=fp,
                tool="semgrep",
                rule_id="test-rule",
                file_path="src/app.py",
                severity=3,
                title="Test finding",
            ))

    current_findings = [_make_finding_schema(fp) for fp in [FP_A, FP_B]]

    result = await compute_delta(
        current_findings=current_findings,
        branch="release/v2.1",
        current_scan_id=current_scan.id,
        session=db_session,
    )

    # No previous scan (only current one exists), so result should be None
    assert result is None


@pytest.mark.asyncio
async def test_delta_picks_most_recent(db_session):
    """When multiple previous scans exist, delta compares against the most recent."""
    from datetime import datetime, timedelta

    async with db_session.begin():
        # Older scan with finding A
        older_scan = ScanResult(
            branch="release/v2.1",
            status="completed",
            total_findings=1,
            created_at=datetime(2026, 1, 1),
        )
        db_session.add(older_scan)
        await db_session.flush()
        db_session.add(Finding(
            scan_id=older_scan.id,
            fingerprint=FP_A,
            tool="semgrep",
            rule_id="test-rule",
            file_path="src/app.py",
            severity=3,
            title="Test finding",
        ))

        # Newer scan with findings A, B
        newer_scan = ScanResult(
            branch="release/v2.1",
            status="completed",
            total_findings=2,
            created_at=datetime(2026, 2, 1),
        )
        db_session.add(newer_scan)
        await db_session.flush()
        for fp in [FP_A, FP_B]:
            db_session.add(Finding(
                scan_id=newer_scan.id,
                fingerprint=fp,
                tool="semgrep",
                rule_id="test-rule",
                file_path="src/app.py",
                severity=3,
                title="Test finding",
            ))

        # Current scan with finding B, C
        current_scan = ScanResult(
            branch="release/v2.1",
            status="completed",
            total_findings=2,
            created_at=datetime(2026, 3, 1),
        )
        db_session.add(current_scan)
        await db_session.flush()

    current_findings = [_make_finding_schema(fp) for fp in [FP_B, FP_C]]

    result = await compute_delta(
        current_findings=current_findings,
        branch="release/v2.1",
        current_scan_id=current_scan.id,
        session=db_session,
    )

    assert result is not None
    # Compared against newer_scan (A, B): new={C}, fixed={A}, persisting={B}
    assert result.new_fingerprints == {FP_C}
    assert result.fixed_fingerprints == {FP_A}
    assert result.persisting_fingerprints == {FP_B}
    assert result.previous_scan_id == newer_scan.id


@pytest.mark.asyncio
async def test_persistence(db_session):
    """Findings are queryable from DB after insert (HIST-01 requirement)."""
    from sqlalchemy import select

    async with db_session.begin():
        scan = ScanResult(
            branch="main",
            status="completed",
            total_findings=2,
        )
        db_session.add(scan)
        await db_session.flush()

        for fp in [FP_A, FP_B]:
            db_session.add(Finding(
                scan_id=scan.id,
                fingerprint=fp,
                tool="semgrep",
                rule_id="test-rule",
                file_path="src/app.py",
                severity=3,
                title="Test finding",
            ))

    # Query findings back
    stmt = select(Finding.fingerprint).where(Finding.scan_id == scan.id)
    result = await db_session.execute(stmt)
    fingerprints = {row[0] for row in result.fetchall()}

    assert fingerprints == {FP_A, FP_B}
