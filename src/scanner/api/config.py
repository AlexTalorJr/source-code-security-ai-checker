"""Configuration CRUD API endpoints for scanner management."""

import os

import yaml
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ValidationError

from scanner.api.auth import require_role, Role
from scanner.config import ScannerSettings
from scanner.models.user import User

router = APIRouter(prefix="/config", tags=["config"])


def get_config_path() -> str:
    """Return the path to the YAML config file."""
    return os.environ.get("SCANNER_CONFIG_PATH", "config.yml")


def read_config() -> dict:
    """Read and parse the YAML config file."""
    path = get_config_path()
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def write_config(data: dict) -> None:
    """Write config dict to the YAML config file."""
    path = get_config_path()
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def validate_config_data(data: dict) -> list[str]:
    """Validate config data against ScannerSettings schema.

    Returns list of error messages (empty if valid).
    """
    try:
        ScannerSettings.model_validate(data)
        return []
    except ValidationError as e:
        return [
            f"{'.'.join(str(loc) for loc in err['loc'])}: {err['msg']}"
            for err in e.errors()
        ]


def validate_extra_args(args: list[str]) -> str | None:
    """Validate extra_args list. Returns error message or None if valid."""
    for arg in args:
        if not arg or not arg.strip():
            return "Empty argument not allowed"
    joined = " ".join(args)
    if joined.count("'") % 2 != 0:
        return "Unbalanced single quotes"
    if joined.count('"') % 2 != 0:
        return "Unbalanced double quotes"
    return None


class ScannerSettingsUpdate(BaseModel):
    """Request model for updating individual scanner settings."""

    enabled: bool | str | None = None
    timeout: int | None = None
    extra_args: list[str] | None = None


@router.get("")
async def get_config(
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Return full config as JSON dict."""
    return read_config()


@router.get("/yaml")
async def get_config_yaml(
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Return raw config.yml content as text/plain."""
    path = get_config_path()
    if not os.path.exists(path):
        return Response(content="", media_type="text/plain")
    with open(path) as f:
        raw_text = f.read()
    return Response(content=raw_text, media_type="text/plain")


@router.patch("/scanners/{scanner_name}")
async def update_scanner_config(
    scanner_name: str,
    update: ScannerSettingsUpdate,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Update settings for a single scanner and persist to config.yml."""
    config = read_config()
    scanners = config.get("scanners", {})

    if scanner_name not in scanners:
        raise HTTPException(status_code=404, detail=f"Scanner '{scanner_name}' not found")

    scanner = scanners[scanner_name]

    if update.enabled is not None:
        if isinstance(update.enabled, str) and update.enabled != "auto":
            raise HTTPException(
                status_code=422,
                detail=f"Invalid enabled value: '{update.enabled}'. Must be true, false, or 'auto'.",
            )
        scanner["enabled"] = update.enabled

    if update.timeout is not None:
        if not (30 <= update.timeout <= 900):
            raise HTTPException(
                status_code=422,
                detail="Timeout must be between 30 and 900 seconds",
            )
        scanner["timeout"] = update.timeout

    if update.extra_args is not None:
        error = validate_extra_args(update.extra_args)
        if error:
            raise HTTPException(status_code=422, detail=error)
        scanner["extra_args"] = update.extra_args

    # Validate full config
    errors = validate_config_data(config)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    write_config(config)
    return {"status": "ok", "scanner": scanner_name}


@router.put("/yaml")
async def put_config_yaml(
    request: Request,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Replace config.yml with raw YAML content (validated before writing)."""
    body = await request.body()
    text = body.decode("utf-8")

    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise HTTPException(status_code=422, detail=f"YAML syntax error: {e}")

    if data is None or not isinstance(data, dict):
        raise HTTPException(status_code=422, detail="Config must be a YAML mapping")

    errors = validate_config_data(data)
    if errors:
        raise HTTPException(status_code=422, detail=errors)

    # Write raw text directly to preserve user formatting
    path = get_config_path()
    with open(path, "w") as f:
        f.write(text)

    return {"status": "ok"}
