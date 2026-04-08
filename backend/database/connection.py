"""
Connection Manager for the SunLeo SQLite Database.

Provides async database access using aiosqlite, compatible with
FastAPI's async request handling model.

Usage:
    from backend.database import init_db, get_db

    # At startup
    await init_db()

    # In request handlers
    async with get_db() as db:
        rows = await db.execute("SELECT ...")
"""
from __future__ import annotations

import aiosqlite
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

# Default database file location (next to this module)
_MODULE_DIR = Path(__file__).resolve().parent
DB_PATH: Path = _MODULE_DIR / "sunleo.db"
_SCHEMA_PATH: Path = _MODULE_DIR / "schema.sql"


async def init_db(db_path: Path | str | None = None) -> None:
    """
    Initialize the database by executing the schema SQL script.
    Creates all tables if they do not already exist.

    Args:
        db_path: Optional override for the database file path.
                 Defaults to sunleo.db in the same directory as this module.
                 Pass ":memory:" for an in-memory database (used in tests).
    """
    target = str(db_path) if db_path else str(DB_PATH)

    async with aiosqlite.connect(target) as db:
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        await db.executescript(schema_sql)
        await db.commit()


@asynccontextmanager
async def get_db(db_path: Path | str | None = None) -> AsyncGenerator[aiosqlite.Connection, None]:
    """
    Async context manager that yields a database connection.

    The connection is automatically closed when the context exits.
    Row factory is set to aiosqlite.Row for dict-like access.

    Args:
        db_path: Optional override for the database file path.

    Yields:
        aiosqlite.Connection with Row factory enabled.

    Example:
        async with get_db() as db:
            cursor = await db.execute("SELECT * FROM jobs WHERE job_id = ?", (jid,))
            row = await cursor.fetchone()
    """
    target = str(db_path) if db_path else str(DB_PATH)

    async with aiosqlite.connect(target) as db:
        db.row_factory = aiosqlite.Row
        yield db
