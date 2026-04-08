"""
Shared pytest fixtures for SunLeo test suites.

Provides:
- In-memory SQLite database (fresh per test)
- Initialized DAL instances (JobDAL, FeedbackDAL)
- FastAPI test client for endpoint testing
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest
import pytest_asyncio

# ---------------------------------------------------------------------------
# Add project root to sys.path so we can import backend modules directly
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import aiosqlite

from backend.database.connection import _SCHEMA_PATH
from backend.database.dal import JobDAL, FeedbackDAL


# ---------------------------------------------------------------------------
# Database fixtures — each test gets a fresh in-memory DB
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def db_connection():
    """
    Yield a fresh in-memory SQLite connection with schema applied.
    Automatically closed after the test.
    """
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        schema_sql = _SCHEMA_PATH.read_text(encoding="utf-8")
        await db.executescript(schema_sql)
        await db.commit()
        yield db


@pytest_asyncio.fixture
async def job_dal(db_connection):
    """Yield a JobDAL wired to the in-memory test database."""
    return JobDAL(db_connection)


@pytest_asyncio.fixture
async def feedback_dal(db_connection):
    """Yield a FeedbackDAL wired to the in-memory test database."""
    return FeedbackDAL(db_connection)


# ---------------------------------------------------------------------------
# FastAPI test client fixture (for black box endpoint testing)
# ---------------------------------------------------------------------------

@pytest.fixture
def test_client():
    """
    Create a synchronous TestClient for the ytconverter FastAPI app.
    Uses httpx for ASGI transport.
    """
    from httpx import ASGITransport, AsyncClient
    from backend.ytconverter.app.main import app

    transport = ASGITransport(app=app)
    return transport


@pytest_asyncio.fixture
async def async_client():
    """
    Create an async httpx client mounted on the ytconverter FastAPI app.
    """
    from httpx import ASGITransport, AsyncClient
    from backend.ytconverter.app.main import app

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
