"""Scanner configuration with YAML file loading and env var overrides."""

from __future__ import annotations

import os

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

from scanner.schemas.severity import Severity


class ScannerToolConfig(BaseModel):
    """Per-tool scanner configuration."""

    enabled: bool = True
    timeout: int = 180
    extra_args: list[str] = []


class ScannersConfig(BaseModel):
    """Configuration for all scanner tools."""

    semgrep: ScannerToolConfig = ScannerToolConfig(timeout=180)
    cppcheck: ScannerToolConfig = ScannerToolConfig(timeout=120)
    gitleaks: ScannerToolConfig = ScannerToolConfig(timeout=120)
    trivy: ScannerToolConfig = ScannerToolConfig(timeout=120)
    checkov: ScannerToolConfig = ScannerToolConfig(timeout=120)


class AIConfig(BaseModel):
    """AI analysis configuration."""

    max_cost_per_scan: float = 5.0
    model: str = "claude-sonnet-4-6"
    max_findings_per_batch: int = 50
    max_tokens_per_response: int = 4096


class GateConfig(BaseModel):
    """Quality gate configuration."""

    fail_on: list[str] = ["critical", "high"]
    include_compound_risks: bool = True

    def evaluate(
        self,
        severity_counts: dict[Severity, int],
        compound_risks: list,
    ) -> tuple[bool, list[str]]:
        """Evaluate gate. Returns (passed, fail_reasons)."""
        reasons: list[str] = []
        for sev_name in self.fail_on:
            sev = Severity[sev_name.upper()]
            count = severity_counts.get(sev, 0)
            if count > 0:
                reasons.append(f"{count} {sev.name} finding(s)")
        if self.include_compound_risks:
            for cr in compound_risks:
                cr_sev = (
                    Severity(cr.severity)
                    if isinstance(cr.severity, int)
                    else Severity[cr.severity.upper()]
                )
                if cr_sev.name.lower() in self.fail_on:
                    reasons.append(f"Compound risk: {cr.title} ({cr_sev.name})")
        return (len(reasons) == 0, reasons)


class ScannerSettings(BaseSettings):
    """Application settings loaded from YAML config with env var overrides.

    Priority order (first wins):
    1. Init values (constructor arguments)
    2. Environment variables (SCANNER_* prefix)
    3. Dotenv file
    4. File secrets
    5. YAML config file (lowest priority)
    """

    model_config = SettingsConfigDict(
        env_prefix="SCANNER_",
        env_nested_delimiter="__",
    )

    # Server
    host: str = "0.0.0.0"
    port: int = 8000

    # Database
    db_path: str = "/data/scanner.db"

    # API
    api_key: str = Field(default="", description="API key for authentication")

    # AI (secrets -- MUST come from env vars)
    claude_api_key: str = Field(default="", description="Claude API key")

    # Notifications (optional)
    slack_webhook_url: str = ""
    email_smtp_host: str = ""

    # Operational
    log_level: str = "info"
    scan_timeout: int = 600

    # Scanner tool configuration
    scanners: ScannersConfig = ScannersConfig()

    # AI analysis
    ai: AIConfig = AIConfig()

    # Quality gate
    gate: GateConfig = GateConfig()

    # Git auth
    git_token: str = Field(
        default="", description="HTTPS token for git clone auth"
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,  # Env vars override YAML
            dotenv_settings,
            file_secret_settings,
            YamlConfigSettingsSource(
                settings_cls,
                yaml_file=os.environ.get("SCANNER_CONFIG_PATH", "config.yml"),
            ),  # YAML is lowest priority
        )
