"""Configuration CRUD API endpoints for scanner management."""

import os
import re

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


# --- Profile CRUD ---

PROFILE_NAME_PATTERN = re.compile(r'^[a-zA-Z][a-zA-Z0-9_-]{0,63}$')
YAML_RESERVED = {"true", "false", "null", "yes", "no", "on", "off"}


def _validate_profile_name(name: str) -> str | None:
    """Validate profile name. Returns error message or None."""
    if name.lower() in YAML_RESERVED:
        return f"Profile name '{name}' is a YAML reserved word"
    if not PROFILE_NAME_PATTERN.match(name):
        return "Profile name must contain only letters, numbers, hyphens, and underscores."
    return None


class ProfileCreateRequest(BaseModel):
    name: str
    description: str = ""
    scanners: dict[str, dict] = {}


class ProfileUpdateRequest(BaseModel):
    description: str | None = None
    scanners: dict[str, dict] | None = None


@router.get("/profiles")
async def list_profiles(
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """List all scan profiles."""
    config = read_config()
    return {"profiles": config.get("profiles", {})}


@router.post("/profiles", status_code=201)
async def create_profile(
    body: ProfileCreateRequest,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Create a new scan profile."""
    error = _validate_profile_name(body.name)
    if error:
        raise HTTPException(status_code=422, detail=error)
    if not body.scanners:
        raise HTTPException(
            status_code=422,
            detail="Profile must have at least one scanner enabled. Select at least one scanner and try again.",
        )
    config = read_config()
    profiles = config.get("profiles", {})
    if len(profiles) >= 10:
        raise HTTPException(
            status_code=400,
            detail="Maximum 10 profiles allowed. Delete an existing profile before creating a new one.",
        )
    if body.name in profiles:
        raise HTTPException(
            status_code=409,
            detail=f"Profile '{body.name}' already exists. Choose a different name.",
        )
    profiles[body.name] = {"description": body.description, "scanners": body.scanners}
    config["profiles"] = profiles
    write_config(config)
    return {"status": "ok", "profile": body.name}


@router.get("/profiles/{name}")
async def get_profile(
    name: str,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Get a single scan profile by name."""
    config = read_config()
    profiles = config.get("profiles", {})
    if name not in profiles:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    return {"name": name, **profiles[name]}


@router.put("/profiles/{name}")
async def update_profile(
    name: str,
    body: ProfileUpdateRequest,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Update an existing scan profile."""
    config = read_config()
    profiles = config.get("profiles", {})
    if name not in profiles:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    if body.description is not None:
        profiles[name]["description"] = body.description
    if body.scanners is not None:
        if not body.scanners:
            raise HTTPException(
                status_code=422,
                detail="Profile must have at least one scanner enabled. Select at least one scanner and try again.",
            )
        profiles[name]["scanners"] = body.scanners
    config["profiles"] = profiles
    write_config(config)
    return {"status": "ok", "profile": name}


@router.delete("/profiles/{name}")
async def delete_profile(
    name: str,
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Delete a scan profile."""
    config = read_config()
    profiles = config.get("profiles", {})
    if name not in profiles:
        raise HTTPException(status_code=404, detail=f"Profile '{name}' not found")
    del profiles[name]
    config["profiles"] = profiles
    write_config(config)
    return {"status": "ok"}
