from app.core.config import Settings
from app.services.simulation import validate_base_url


def test_validate_rejects_remote_host():
    settings = Settings(
        app_env="test",
        simulation_allowed_host="127.0.0.1,localhost",
    )
    try:
        validate_base_url("https://evil.example.com", settings)
        assert False, "should have raised"
    except ValueError as exc:
        assert "not allowed" in str(exc)


def test_validate_allows_localhost():
    settings = Settings(
        app_env="test",
        simulation_allowed_host="127.0.0.1,localhost",
    )
    url = validate_base_url("http://127.0.0.1:8000", settings)
    assert url == "http://127.0.0.1:8000"


def test_simulation_limits_endpoint(client):
    resp = client.get("/api/v1/simulation/limits")
    assert resp.status_code == 200
    data = resp.json()
    assert data["max_requests"] <= 100
    assert "127.0.0.1" in data["allowed_hosts"] or "localhost" in data["allowed_hosts"]


def test_simulation_run_clamps_and_works(client):
    resp = client.post(
        "/api/v1/simulation/run",
        json={
            "mode": "normal",
            "request_count": 3,
            "interval_ms": 50,
            "endpoint": "health",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 3
    assert data["successful"] + data["rejected"] + data["failed"] == 3


def test_simulation_cancel(client):
    resp = client.post("/api/v1/simulation/cancel")
    assert resp.status_code == 200
    assert resp.json()["cancelled"] is True


def test_invalid_simulation_payload(client):
    resp = client.post(
        "/api/v1/simulation/run",
        json={"mode": "stealth", "request_count": 9999},
    )
    assert resp.status_code == 422
