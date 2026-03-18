"""Health check endpoint for the security scanner API."""

import time

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sqlalchemy import text

router = APIRouter()
_start_time = time.time()


class HealthResponse(BaseModel):
    """Response schema for the health check endpoint."""

    status: str
    version: str
    uptime_seconds: float
    database: str


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request) -> HealthResponse:
    """Check application health including database connectivity."""
    db_status = "ok"
    try:
        async with request.app.state.session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="healthy" if db_status == "ok" else "degraded",
        version="0.1.0",
        uptime_seconds=round(time.time() - _start_time, 2),
        database=db_status,
    )
