"""
Shared test fixtures.

pytest-asyncio runs every test in its own event loop, while the app's async
engine keeps a cross-test connection pool. Disposing the engine after each
test keeps pooled connections from being reused across loops.
"""
import pytest_asyncio

from core.database import engine


@pytest_asyncio.fixture(autouse=True)
async def _dispose_engine():
    yield
    await engine.dispose()
