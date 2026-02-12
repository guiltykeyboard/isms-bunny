import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from fastapi.testclient import TestClient

from app.config import get_settings
from app.db import SessionLocal, engine
from app.main import app


@pytest.fixture(scope="session")
def client(event_loop):
    """Synchronous TestClient with tenancy header preset to localhost."""
    settings = get_settings()
    headers = {"host": settings.default_tenant_fqdn or "localhost"}
    return TestClient(app, headers=headers, raise_server_exceptions=False)


@pytest.fixture()
async def async_client():
    """Async client using the same event loop to avoid cross-loop issues."""
    settings = get_settings()
    transport = ASGITransport(app=app, lifespan="on")
    headers = {"host": settings.default_tenant_fqdn or "localhost"}
    async with AsyncClient(
        transport=transport, base_url="http://testserver", headers=headers
    ) as client:
        yield client


@pytest.fixture()
async def temp_user():
    """Create a transient user tied to the default tenant for API tests."""
    settings = get_settings()
    user_id = uuid.uuid4()
    async with SessionLocal() as session:
        await session.execute(
            """
            INSERT INTO users (id, email, full_name, status)
            VALUES (:id, :email, :name, 'active')
            """,
            {"id": user_id, "email": f"tester-{user_id}@example.com", "name": "Test User"},
        )
        await session.execute(
            """
            INSERT INTO memberships (user_id, tenant_id, roles)
            VALUES (:uid, :tid, ARRAY['viewer'])
            ON CONFLICT DO NOTHING
            """,
            {"uid": user_id, "tid": settings.default_tenant_id},
        )
        await session.commit()
    try:
        yield user_id
    finally:
        async with SessionLocal() as session:
            await session.execute("DELETE FROM memberships WHERE user_id=:uid", {"uid": user_id})
            await session.execute("DELETE FROM users WHERE id=:uid", {"uid": user_id})
            await session.commit()


@pytest.fixture(scope="session")
def event_loop():
    # Use a dedicated asyncio event loop for the entire test session.
    loop = asyncio.new_event_loop()
    yield loop
    loop.run_until_complete(engine.dispose())
    loop.close()
