"""Async SQLAlchemy engine and session factory with SQLite WAL mode."""

from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def _set_sqlite_pragmas(dbapi_conn, connection_record):
    """Enable WAL mode and other SQLite optimizations on every connection."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA busy_timeout=5000")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


def create_engine(db_path: str):
    """Create an async SQLAlchemy engine for SQLite with WAL mode.

    Args:
        db_path: Filesystem path to the SQLite database file.

    Returns:
        AsyncEngine configured with WAL mode, synchronous=NORMAL,
        and foreign_keys=ON on every connection.
    """
    url = f"sqlite+aiosqlite:///{db_path}"
    engine = create_async_engine(url, echo=False)

    # Register PRAGMA on every new connection
    event.listen(engine.sync_engine, "connect", _set_sqlite_pragmas)

    return engine


def create_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    """Create an async session factory bound to the given engine."""
    return async_sessionmaker(engine, expire_on_commit=False)
