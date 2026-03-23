"""API router aggregator for the security scanner."""

from fastapi import APIRouter

from scanner.api.config import router as config_router
from scanner.api.findings import router as findings_router
from scanner.api.health import router as health_router
from scanner.api.scanners import router as scanners_router
from scanner.api.scans import router as scans_router
from scanner.api.tokens import router as tokens_router
from scanner.api.users import router as users_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(scans_router)
api_router.include_router(findings_router)
api_router.include_router(scanners_router)
api_router.include_router(users_router)
api_router.include_router(tokens_router)
api_router.include_router(config_router)
