def test_allowed_requests_under_limit(client):
    for i in range(3):
        resp = client.post("/api/v1/demo/protected", json={"message": f"ok-{i}"})
        assert resp.status_code in (200, 403)
        assert "X-RateLimit-Limit" in resp.headers


def test_rate_limit_violation(client, settings):
    limit = settings.rate_limit_requests
    last = None
    for i in range(limit + 2):
        last = client.post(
            "/api/v1/demo/protected",
            json={"message": f"rl-{i}", "captcha_token": "mock-valid-token"},
        )
    assert last is not None
    assert last.status_code == 429
    assert last.json()["status"] == "rate_limited"
    assert "Retry-After" in last.headers or "X-RateLimit-Remaining" in last.headers

    # Violation recorded in events
    events = client.get("/api/v1/events", params={"outcome": "rate_limited"})
    assert events.status_code == 200
    assert events.json()["total"] >= 1
