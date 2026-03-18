"""Scanner configuration with YAML file loading and env var overrides."""

import os

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)


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
