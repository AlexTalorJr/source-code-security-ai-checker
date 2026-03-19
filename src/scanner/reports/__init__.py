"""Report generation for aipix-security-scanner."""

from scanner.reports.html_report import generate_html_report
from scanner.reports.pdf_report import generate_pdf_report

__all__ = ["generate_html_report", "generate_pdf_report"]
