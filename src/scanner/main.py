"""FastAPI application factory with lifespan management."""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from scanner.api.router import api_router
from scanner.config import ScannerSettings
from scanner.dashboard.router import router as dashboard_router
from scanner.core.scan_queue import ScanQueue
from scanner.db.session import create_engine, create_session_factory
from scanner.models.base import Base


def _apply_schema_updates(connection) -> None:
    """Add missing columns to existing tables (lightweight migration)."""
    from sqlalchemy import inspect, text

    inspector = inspect(connection)
    scans_cols = {c["name"] for c in inspector.get_columns("scans")}
    if "skip_ai" not in scans_cols:
        connection.execute(
            text("ALTER TABLE scans ADD COLUMN skip_ai BOOLEAN NOT NULL DEFAULT 0")
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown logic for the FastAPI application.

    On startup:
    - Load settings from config/env
    - Create async SQLite engine with WAL mode
    - Create all tables (Phase 1 approach; Alembic for later phases)
    - Store engine, session factory, and settings on app.state
    - Start background scan queue worker

    On shutdown:
    - Cancel scan queue worker
    - Dispose engine and release connections
    """
    settings = ScannerSettings()
    engine = create_engine(settings.db_path)

    # Create tables and apply schema migrations
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Add columns that may be missing in existing databases
        await conn.run_sync(_apply_schema_updates)

    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.settings = settings

    # Start background scan queue
    scan_queue = ScanQueue()
    app.state.scan_queue = scan_queue
    await scan_queue.recover_stuck_scans(app)
    worker_task = asyncio.create_task(scan_queue.worker(app))

    yield

    # Shutdown: cancel worker, dispose engine
    worker_task.cancel()
    await asyncio.gather(worker_task, return_exceptions=True)
    await engine.dispose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="aipix-security-scanner",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/dashboard")
    return app


app = create_app()
