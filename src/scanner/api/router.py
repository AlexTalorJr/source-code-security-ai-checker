"""API router aggregator for the security scanner."""

from fastapi import APIRouter

from scanner.api.health import router as health_router

api_router = APIRouter()
api_router.include_router(health_router)
