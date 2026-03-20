"""ScanResult ORM model for tracking scan execution and results."""

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import relationship

from scanner.models.base import Base


class ScanResult(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # Target
    target_path = Column(String(500), nullable=True)
    repo_url = Column(String(500), nullable=True)
    branch = Column(String(200), nullable=True)
    commit_hash = Column(String(40), nullable=True)

    # Options
    skip_ai = Column(Boolean, nullable=False, default=False, server_default="0")

    # Status
    status = Column(String(20), nullable=False, default="pending")
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)

    # Results summary
    total_findings = Column(Integer, default=0)
    critical_count = Column(Integer, default=0)
    high_count = Column(Integer, default=0)
    medium_count = Column(Integer, default=0)
    low_count = Column(Integer, default=0)
    info_count = Column(Integer, default=0)

    # Quality gate
    gate_passed = Column(Integer, nullable=True)  # 0=fail, 1=pass, NULL=not evaluated

    # Metadata
    scanner_version = Column(String(20), nullable=True)
    tool_versions = Column(Text, nullable=True)  # JSON blob of tool versions
    error_message = Column(Text, nullable=True)
    ai_cost_usd = Column(Float, nullable=True, default=None)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    findings = relationship(
        "Finding", back_populates="scan", cascade="all, delete-orphan"
    )
    compound_risks = relationship(
        "CompoundRisk", back_populates="scan", cascade="all, delete-orphan"
    )
