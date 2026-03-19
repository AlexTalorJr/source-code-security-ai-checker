"""Suppression ORM model for tracking false positive fingerprints."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from scanner.models.base import Base


class Suppression(Base):
    """Tracks fingerprints marked as false positives."""

    __tablename__ = "suppressions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    fingerprint = Column(String(64), nullable=False, unique=True, index=True)
    reason = Column(Text, nullable=True)
    suppressed_by = Column(String(100), default="api")
    created_at = Column(DateTime, default=datetime.utcnow)
