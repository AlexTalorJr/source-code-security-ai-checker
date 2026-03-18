"""Unified severity levels for security findings."""

from enum import IntEnum


class Severity(IntEnum):
    """Unified severity levels. IntEnum enables comparison operators."""

    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1
