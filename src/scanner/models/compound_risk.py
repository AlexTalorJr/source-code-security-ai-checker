"""CompoundRisk ORM model for cross-tool correlation storage."""

from sqlalchemy import Column, ForeignKey, Integer, String, Table, Text
from sqlalchemy.orm import relationship

from scanner.models.base import Base


compound_risk_findings = Table(
    "compound_risk_findings",
    Base.metadata,
    Column(
        "compound_risk_id",
        Integer,
        ForeignKey("compound_risks.id"),
        primary_key=True,
    ),
    Column("finding_fingerprint", String(64), nullable=False, primary_key=True),
)


class CompoundRisk(Base):
    """A compound risk identified by AI cross-component correlation."""

    __tablename__ = "compound_risks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    scan_id = Column(Integer, ForeignKey("scans.id"), nullable=False, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    severity = Column(Integer, nullable=False)  # Maps to Severity IntEnum
    risk_category = Column(String(100), nullable=True)
    recommendation = Column(Text, nullable=True)

    scan = relationship("ScanResult", back_populates="compound_risks")
