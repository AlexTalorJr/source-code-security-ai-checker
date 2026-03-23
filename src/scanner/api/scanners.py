"""Scanner registry listing endpoint."""

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel

from scanner.adapters.registry import ScannerRegistry
from scanner.api.auth import get_current_user
from scanner.models.user import User

router = APIRouter(prefix="/scanners", tags=["scanners"])


class ScannerInfo(BaseModel):
    """Response model for a single scanner entry."""

    name: str
    status: str
    enabled: bool | str
    languages: list[str]
    load_error: str | None = None


@router.get("", response_model=list[ScannerInfo])
async def list_scanners(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> list[ScannerInfo]:
    """List all registered scanners with status information."""
    settings = request.app.state.settings
    registry = ScannerRegistry(settings.scanners)
    return [ScannerInfo(**info) for info in registry.all_scanners_info()]
