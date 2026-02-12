
import pytest


@pytest.mark.anyio
async def test_default_tenant_resolution(async_client):
    resp = await async_client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


@pytest.mark.anyio
async def test_tenant_not_found_returns_404(async_client):
    resp = await async_client.get("/trust", headers={"host": "unknown.example.com"})
    assert resp.status_code == 404
