"""Scanner tool adapters package."""

from scanner.adapters.base import ScannerAdapter
from scanner.adapters.semgrep import SemgrepAdapter
from scanner.adapters.cppcheck import CppcheckAdapter
from scanner.adapters.gitleaks import GitleaksAdapter
from scanner.adapters.trivy import TrivyAdapter
from scanner.adapters.checkov import CheckovAdapter

ALL_ADAPTERS = [
    SemgrepAdapter,
    CppcheckAdapter,
    GitleaksAdapter,
    TrivyAdapter,
    CheckovAdapter,
]

__all__ = [
    "ScannerAdapter",
    "SemgrepAdapter",
    "CppcheckAdapter",
    "GitleaksAdapter",
    "TrivyAdapter",
    "CheckovAdapter",
    "ALL_ADAPTERS",
]
