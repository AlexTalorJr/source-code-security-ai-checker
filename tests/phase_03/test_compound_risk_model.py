"""Tests for CompoundRisk ORM model, join table, schema, and ScanResult extensions."""

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from scanner.models.base import Base
from scanner.models.compound_risk import CompoundRisk, compound_risk_findings
from scanner.models.scan import ScanResult
from scanner.schemas.compound_risk import CompoundRiskSchema
from scanner.schemas.scan import ScanResultSchema


class TestCompoundRiskModel:
    def test_tablename(self):
        assert CompoundRisk.__tablename__ == "compound_risks"

    def test_has_required_columns(self):
        mapper = inspect(CompoundRisk)
        column_names = {c.key for c in mapper.column_attrs}
        assert "id" in column_names
        assert "scan_id" in column_names
        assert "title" in column_names
        assert "description" in column_names
        assert "severity" in column_names
        assert "risk_category" in column_names
        assert "recommendation" in column_names

    def test_id_is_primary_key(self):
        table = CompoundRisk.__table__
        pk_cols = [c.name for c in table.primary_key.columns]
        assert "id" in pk_cols

    def test_scan_id_is_foreign_key(self):
        table = CompoundRisk.__table__
        fks = [
            fk.target_fullname
            for col in table.columns
            for fk in col.foreign_keys
        ]
        assert "scans.id" in fks


class TestCompoundRiskFindingsJoinTable:
    def test_join_table_has_columns(self):
        col_names = {c.name for c in compound_risk_findings.columns}
        assert "compound_risk_id" in col_names
        assert "finding_fingerprint" in col_names

    def test_both_columns_are_primary_key(self):
        pk_cols = {c.name for c in compound_risk_findings.primary_key.columns}
        assert "compound_risk_id" in pk_cols
        assert "finding_fingerprint" in pk_cols


class TestCompoundRiskSchema:
    def test_validates_all_fields(self):
        schema = CompoundRiskSchema(
            title="Auth bypass chain",
            description="SQL injection + mass assignment",
            severity=5,
            risk_category="auth_bypass",
            finding_fingerprints=["a" * 64, "b" * 64],
            recommendation="Fix injection first",
        )
        assert schema.title == "Auth bypass chain"
        assert len(schema.finding_fingerprints) == 2

    def test_optional_fields_default(self):
        schema = CompoundRiskSchema(
            title="Test",
            description="Test desc",
            severity=3,
        )
        assert schema.id is None
        assert schema.scan_id is None
        assert schema.risk_category is None
        assert schema.finding_fingerprints == []
        assert schema.recommendation is None


class TestScanResultExtensions:
    def test_scan_result_has_ai_cost_usd_column(self):
        mapper = inspect(ScanResult)
        column_names = {c.key for c in mapper.column_attrs}
        assert "ai_cost_usd" in column_names

    def test_scan_result_has_compound_risks_relationship(self):
        mapper = inspect(ScanResult)
        assert "compound_risks" in mapper.relationships

    def test_scan_result_schema_has_ai_fields(self):
        schema = ScanResultSchema()
        assert schema.ai_cost_usd is None
        assert schema.ai_skipped is False
        assert schema.ai_skip_reason is None


class TestDatabaseCreation:
    def test_create_all_creates_tables(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert "compound_risks" in table_names
        assert "compound_risk_findings" in table_names
        assert "scans" in table_names

    def test_insert_compound_risk(self):
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)

        with Session(engine) as session:
            scan = ScanResult(status="completed", target_path="/test")
            session.add(scan)
            session.flush()

            risk = CompoundRisk(
                scan_id=scan.id,
                title="Test compound risk",
                description="Two findings combine to create elevated risk",
                severity=5,
                risk_category="auth_bypass",
                recommendation="Fix both findings",
            )
            session.add(risk)
            session.commit()

            loaded = session.query(CompoundRisk).first()
            assert loaded is not None
            assert loaded.title == "Test compound risk"
            assert loaded.scan_id == scan.id
