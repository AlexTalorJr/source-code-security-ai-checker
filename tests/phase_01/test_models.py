"""Tests for SQLAlchemy ORM models and database session with WAL mode."""

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession

from scanner.db.session import create_engine, create_session_factory
from scanner.models import Base, Finding, ScanResult
from scanner.schemas.severity import Severity


@pytest.fixture
async def db_engine(tmp_path):
    """Create a test async engine with a temporary SQLite database."""
    db_path = str(tmp_path / "test.db")
    engine = create_engine(db_path)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
async def db_session(db_engine) -> AsyncSession:
    """Create a test async session."""
    factory = create_session_factory(db_engine)
    async with factory() as session:
        yield session


class TestSeverityEnum:
    def test_severity_enum_values(self):
        """Severity enum imported in finding model, values 1-5."""
        assert Severity.CRITICAL == 5
        assert Severity.HIGH == 4
        assert Severity.MEDIUM == 3
        assert Severity.LOW == 2
        assert Severity.INFO == 1


class TestFindingModelColumns:
    def test_finding_model_columns(self):
        """Finding model has all expected columns."""
        columns = {c.name for c in Finding.__table__.columns}
        expected = {
            "id", "scan_id", "fingerprint", "tool", "rule_id",
            "file_path", "line_start", "line_end", "snippet",
            "severity", "title", "description", "recommendation",
            "ai_analysis", "ai_fix_suggestion", "false_positive",
            "created_at",
        }
        assert expected == columns


class TestScanModelColumns:
    def test_scan_model_columns(self):
        """ScanResult model has all expected columns."""
        columns = {c.name for c in ScanResult.__table__.columns}
        expected = {
            "id", "target_path", "repo_url", "branch", "commit_hash",
            "status", "started_at", "completed_at", "duration_seconds",
            "total_findings", "critical_count", "high_count",
            "medium_count", "low_count", "info_count", "gate_passed",
            "scanner_version", "tool_versions", "error_message",
            "created_at",
        }
        assert expected == columns


class TestForeignKey:
    def test_finding_scan_foreign_key(self):
        """Finding.scan_id references scans.id."""
        scan_id_col = Finding.__table__.c.scan_id
        fk = list(scan_id_col.foreign_keys)
        assert len(fk) == 1
        assert fk[0].target_fullname == "scans.id"


class TestSQLitePragmas:
    @pytest.mark.asyncio
    async def test_sqlite_wal_mode(self, db_engine):
        """After engine creation, PRAGMA journal_mode returns 'wal'."""
        async with db_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA journal_mode"))
            mode = result.scalar()
            assert mode == "wal"

    @pytest.mark.asyncio
    async def test_sqlite_foreign_keys(self, db_engine):
        """After engine creation, PRAGMA foreign_keys returns 1."""
        async with db_engine.connect() as conn:
            result = await conn.execute(text("PRAGMA foreign_keys"))
            fk_enabled = result.scalar()
            assert fk_enabled == 1


class TestCRUD:
    @pytest.mark.asyncio
    async def test_create_and_read_scan(self, db_session):
        """Insert ScanResult, read back, verify fields match."""
        scan = ScanResult(
            target_path="/tmp/test-repo",
            repo_url="https://github.com/test/repo",
            branch="main",
            commit_hash="abc123def456",
            status="completed",
            total_findings=5,
            critical_count=1,
            high_count=2,
            medium_count=1,
            low_count=1,
            info_count=0,
        )
        db_session.add(scan)
        await db_session.commit()
        await db_session.refresh(scan)

        assert scan.id is not None
        assert scan.target_path == "/tmp/test-repo"
        assert scan.repo_url == "https://github.com/test/repo"
        assert scan.branch == "main"
        assert scan.status == "completed"
        assert scan.total_findings == 5
        assert scan.critical_count == 1
        assert scan.created_at is not None

    @pytest.mark.asyncio
    async def test_create_and_read_finding(self, db_session):
        """Insert Finding with scan_id, read back, verify fields."""
        scan = ScanResult(status="completed")
        db_session.add(scan)
        await db_session.commit()
        await db_session.refresh(scan)

        finding = Finding(
            scan_id=scan.id,
            fingerprint="a" * 64,
            tool="semgrep",
            rule_id="python.security.sql-injection",
            file_path="src/app.py",
            line_start=42,
            line_end=45,
            snippet="cursor.execute(query)",
            severity=Severity.HIGH,
            title="SQL Injection",
            description="User input used in SQL query",
            recommendation="Use parameterized queries",
        )
        db_session.add(finding)
        await db_session.commit()
        await db_session.refresh(finding)

        assert finding.id is not None
        assert finding.scan_id == scan.id
        assert finding.fingerprint == "a" * 64
        assert finding.tool == "semgrep"
        assert finding.severity == Severity.HIGH
        assert finding.title == "SQL Injection"
        assert finding.created_at is not None


class TestPersistence:
    @pytest.mark.asyncio
    async def test_db_persistence(self, tmp_path):
        """Insert data, dispose engine, create new engine, data still present."""
        db_path = str(tmp_path / "persist_test.db")

        # First engine: create and insert
        engine1 = create_engine(db_path)
        async with engine1.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        factory1 = create_session_factory(engine1)
        async with factory1() as session:
            scan = ScanResult(
                target_path="/test",
                status="completed",
                total_findings=3,
            )
            session.add(scan)
            await session.commit()
        await engine1.dispose()

        # Second engine: read back
        engine2 = create_engine(db_path)
        factory2 = create_session_factory(engine2)
        async with factory2() as session:
            result = await session.execute(
                text("SELECT total_findings FROM scans WHERE target_path = '/test'")
            )
            row = result.one()
            assert row[0] == 3
        await engine2.dispose()
