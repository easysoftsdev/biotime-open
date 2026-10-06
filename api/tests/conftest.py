"""
Shared test fixtures.

Schema is provisioned before every test (create_all + constraint sync from
core.database.create_tables are idempotent) so a freshly created test database
works without manual setup. pytest-asyncio runs every test in its own event
loop, while the app's async engine keeps a cross-test connection pool —
disposing the engine after each test keeps pooled connections from being
reused across loops.
"""
import pytest_asyncio

from core.database import engine, create_tables


@pytest_asyncio.fixture(autouse=True)
async def _schema():
    await create_tables()
    yield
    await engine.dispose()
