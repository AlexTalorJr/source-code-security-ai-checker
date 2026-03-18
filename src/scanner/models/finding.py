"""Finding ORM model for normalized security vulnerability data."""

from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from scanner.models.base import Base


class Finding(Base):
    __tablename__ = "findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    fingerprint = Column(String(64), nullable=False, index=True)  # SHA-256 hex

    # Source
    tool = Column(String(50), nullable=False)  # semgrep, gitleaks, trivy, etc.
    rule_id = Column(String(200), nullable=False)

    # Location
    file_path = Column(String(500), nullable=False)
    line_start = Column(Integer, nullable=True)
    line_end = Column(Integer, nullable=True)
    snippet = Column(Text, nullable=True)

    # Classification
    severity = Column(Integer, nullable=False)  # Maps to Severity IntEnum
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    recommendation = Column(Text, nullable=True)

    # AI enrichment (Phase 3, nullable for now)
    ai_analysis = Column(Text, nullable=True)
    ai_fix_suggestion = Column(Text, nullable=True)

    # Metadata
    false_positive = Column(Integer, default=0)  # 0=no, 1=yes (Phase 5)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    scan = relationship("ScanResult", back_populates="findings")
