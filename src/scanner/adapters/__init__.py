"""Scanner tool adapters package."""

from scanner.adapters.base import ScannerAdapter
from scanner.adapters.semgrep import SemgrepAdapter
from scanner.adapters.cppcheck import CppcheckAdapter
from scanner.adapters.gitleaks import GitleaksAdapter
from scanner.adapters.trivy import TrivyAdapter
from scanner.adapters.checkov import CheckovAdapter
from scanner.adapters.psalm import PsalmAdapter
from scanner.adapters.enlightn import EnlightnAdapter
from scanner.adapters.php_security_checker import PhpSecurityCheckerAdapter

ALL_ADAPTERS = [
    SemgrepAdapter,
    CppcheckAdapter,
    GitleaksAdapter,
    TrivyAdapter,
    CheckovAdapter,
    PsalmAdapter,
    EnlightnAdapter,
    PhpSecurityCheckerAdapter,
]

__all__ = [
    "ScannerAdapter",
    "SemgrepAdapter",
    "CppcheckAdapter",
    "GitleaksAdapter",
    "TrivyAdapter",
    "CheckovAdapter",
    "PsalmAdapter",
    "EnlightnAdapter",
    "PhpSecurityCheckerAdapter",
    "ALL_ADAPTERS",
]
