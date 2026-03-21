"""Config-driven scanner plugin registry."""

import importlib
import logging
from dataclasses import dataclass, field

from scanner.adapters.base import ScannerAdapter
from scanner.config import ScannerToolConfig

logger = logging.getLogger(__name__)


def load_adapter_class(tool_name: str, adapter_class_path: str) -> type | None:
    """Load an adapter class from a dotted module path.

    Returns the class on success, or None on failure (with WARNING logged).
    """
    try:
        module_path, class_name = adapter_class_path.rsplit(".", 1)
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        return cls
    except (ImportError, AttributeError, ValueError) as exc:
        logger.warning(
            "Scanner '%s': failed to load adapter_class '%s': %s",
            tool_name,
            adapter_class_path,
            exc,
        )
        return None


@dataclass
class RegisteredScanner:
    """A scanner entry in the registry."""

    name: str
    adapter_class_path: str
    adapter_class: type | None = None
    enabled: bool | str = "auto"
    timeout: int = 180
    extra_args: list[str] = field(default_factory=list)
    languages: list[str] = field(default_factory=list)
    load_error: str | None = None

    @property
    def status(self) -> str:
        if self.load_error:
            return "load_error"
        if self.enabled is False:
            return "disabled"
        return "enabled"


class ScannerRegistry:
    """Registry of all scanners loaded from config."""

    def __init__(self, scanners_config: dict[str, ScannerToolConfig]):
        self._scanners: dict[str, RegisteredScanner] = {}
        for name, config in scanners_config.items():
            self._register(name, config)

    def _register(self, name: str, config: ScannerToolConfig) -> None:
        entry = RegisteredScanner(
            name=name,
            adapter_class_path=config.adapter_class,
            enabled=config.enabled,
            timeout=config.timeout,
            extra_args=config.extra_args,
            languages=config.languages,
        )
        if not config.adapter_class:
            entry.load_error = "adapter_class is required"
            logger.warning(
                "Scanner '%s': adapter_class is required, skipping", name
            )
        else:
            cls = load_adapter_class(name, config.adapter_class)
            if cls is None:
                entry.load_error = f"Failed to import {config.adapter_class}"
            elif not issubclass(cls, ScannerAdapter):
                entry.load_error = (
                    f"{config.adapter_class} is not a ScannerAdapter subclass"
                )
                logger.warning("Scanner '%s': %s", name, entry.load_error)
            else:
                entry.adapter_class = cls
        self._scanners[name] = entry

    def get_enabled_adapters(
        self, detected_languages: set[str]
    ) -> list[ScannerAdapter]:
        """Return instantiated adapters that should run for detected languages."""
        adapters = []
        for scanner in self._scanners.values():
            if scanner.adapter_class is None:
                continue
            if scanner.enabled is False:
                continue
            if scanner.enabled == "auto":
                if scanner.languages and not (
                    set(scanner.languages) & detected_languages
                ):
                    continue
            adapters.append(scanner.adapter_class())
        return adapters

    def get_scanner_config(self, tool_name: str) -> RegisteredScanner | None:
        """Get a registered scanner by name."""
        return self._scanners.get(tool_name)

    def all_scanners_info(self) -> list[dict]:
        """For /api/scanners endpoint."""
        return [
            {
                "name": s.name,
                "status": s.status,
                "enabled": s.enabled,
                "languages": s.languages,
                "load_error": s.load_error,
            }
            for s in self._scanners.values()
        ]
