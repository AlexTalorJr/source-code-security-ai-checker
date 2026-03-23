"""FastAPI application factory with lifespan management."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

logger = logging.getLogger(__name__)

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
    if "scans" not in inspector.get_table_names():
        return

    scans_cols = {c["name"] for c in inspector.get_columns("scans")}

    migrations = {
        "ai_cost_usd": "ALTER TABLE scans ADD COLUMN ai_cost_usd FLOAT",
        "skip_ai": "ALTER TABLE scans ADD COLUMN skip_ai BOOLEAN NOT NULL DEFAULT 0",
        "scanner_version": "ALTER TABLE scans ADD COLUMN scanner_version VARCHAR(20)",
        "tool_versions": "ALTER TABLE scans ADD COLUMN tool_versions TEXT",
        "created_at": "ALTER TABLE scans ADD COLUMN created_at DATETIME DEFAULT (datetime('now'))",
    }

    for col, sql in migrations.items():
        if col not in scans_cols:
            connection.execute(text(sql))


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

    # Resolve or generate JWT secret key
    secret_key = settings.secret_key
    if not secret_key:
        secret_file = os.path.join(os.path.dirname(settings.db_path), ".secret_key")
        if os.path.exists(secret_file):
            with open(secret_file) as f:
                secret_key = f.read().strip()
        else:
            import secrets as secrets_mod

            secret_key = secrets_mod.token_hex(32)
            os.makedirs(os.path.dirname(secret_file), exist_ok=True)
            with open(secret_file, "w") as f:
                f.write(secret_key)
            logger.info("Generated new JWT secret key: %s", secret_file)
    settings.secret_key = secret_key

    # Admin bootstrap: create initial admin user if no users exist
    from scanner.models.user import User
    from sqlalchemy import select, func as sa_func
    from sqlalchemy.exc import IntegrityError
    from pwdlib import PasswordHash

    session_factory = create_session_factory(engine)
    async with session_factory() as session:
        user_count = await session.scalar(select(sa_func.count(User.id)))
        if user_count == 0:
            if not settings.admin_user or not settings.admin_password:
                raise RuntimeError(
                    "No users exist and SCANNER_ADMIN_USER / SCANNER_ADMIN_PASSWORD "
                    "not set. Cannot start without authentication."
                )
            pw_hash = PasswordHash.default()
            hashed = pw_hash.hash(settings.admin_password)
            admin = User(
                username=settings.admin_user,
                password_hash=hashed,
                role="admin",
            )
            try:
                session.add(admin)
                await session.commit()
                logger.info("Created initial admin user: %s", settings.admin_user)
            except IntegrityError:
                await session.rollback()
                logger.info("Admin user already exists (concurrent creation)")
        else:
            logger.debug("Users exist (%d), skipping admin bootstrap", user_count)

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
        title="Source Code Security AI Scanner",
        version="0.1.0",
        lifespan=lifespan,
    )
    app.include_router(api_router, prefix="/api")
    app.include_router(dashboard_router, prefix="/dashboard")
    return app


app = create_app()
