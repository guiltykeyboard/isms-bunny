import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.skip(reason="Needs tenant + DB context; run in nightly with DB seeded")
def test_auth_method_requires_tenant():
    client = TestClient(app)
    resp = client.get("/auth/method", params={"email": "user@example.com"})
    assert resp.status_code in (400, 404)
