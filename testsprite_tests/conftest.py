"""
Conftest for TestSprite integration tests.

Starts a live uvicorn server backed by a file-based SQLite database on
port 8000 so that all TC0xx test files can hit http://localhost:8000
without needing a real PostgreSQL instance.
"""

import asyncio
import os
import pathlib
import threading
import time

import pytest
import requests as _requests

# ---------------------------------------------------------------------------
# Override DATABASE_URL and BASE_URL before any app module is imported.
# This ensures pydantic-settings picks up SQLite if app hasn't been imported
# yet (i.e. when testsprite_tests runs before the unit-test suite).
# ---------------------------------------------------------------------------
_TEST_DB = str(pathlib.Path(__file__).parent / "testsprite_integration.db")
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_TEST_DB}"
os.environ["BASE_URL"] = "http://localhost:8000"


def _patch_database() -> None:
    """
    Replace the module-level SQLAlchemy engine and session factory in
    ``app.database`` with a fresh SQLite-backed one, then create all
    tables.  This is safe to call after the unit-test suite has already
    imported the module with a different URL.
    """
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    import app.database as _db

    # Build a new SQLite engine using the same Base (which already has all
    # model metadata registered).
    new_engine = create_async_engine(
        f"sqlite+aiosqlite:///{_TEST_DB}", echo=False
    )
    new_session_factory = async_sessionmaker(
        new_engine, class_=AsyncSession, expire_on_commit=False
    )

    # Patch module-level names so init_db() / get_db() use the new engine.
    _db.engine = new_engine
    _db.async_session_factory = new_session_factory

    # Create all tables via the existing Base metadata.
    async def _create_tables() -> None:
        async with new_engine.begin() as conn:
            await conn.run_sync(_db.Base.metadata.create_all)

    asyncio.run(_create_tables())


@pytest.fixture(scope="session", autouse=True)
def live_server():
    """Start a uvicorn server backed by SQLite for the whole test session."""
    _patch_database()

    import uvicorn
    from app.main import create_app

    app_instance = create_app()
    config = uvicorn.Config(
        app=app_instance,
        host="127.0.0.1",
        port=8000,
        log_level="error",
        loop="asyncio",
    )
    server = uvicorn.Server(config)

    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait until the server is ready (up to 15 seconds for startup)
    deadline = time.time() + 15
    while time.time() < deadline:
        try:
            resp = _requests.get("http://127.0.0.1:8000/health", timeout=1)
            if resp.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(0.3)
    else:
        server.should_exit = True
        thread.join(timeout=5)
        pytest.fail("Test server did not start within 15 seconds")

    yield

    # Tear down – allow up to 10 seconds for graceful shutdown
    server.should_exit = True
    thread.join(timeout=10)

    # Remove the SQLite test DB file
    pathlib.Path(_TEST_DB).unlink(missing_ok=True)
