


def test_default_tenant_resolution(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json().get("status") == "ok"


def test_tenant_not_found_returns_404(client):
    resp = client.get("/health", headers={"host": "unknown.example.com"})
    assert resp.status_code == 404

