def test_event_persistence(client):
    resp = client.post(
        "/api/v1/demo/protected",
        json={"message": "persist", "captcha_token": "mock-valid-token"},
        headers={"User-Agent": "Mozilla/5.0 TestBrowser"},
    )
    assert resp.status_code == 200
    event_id = resp.json()["event_id"]
    assert event_id

    listed = client.get("/api/v1/events")
    assert listed.status_code == 200
    data = listed.json()
    assert data["total"] >= 1
    assert data["items"][0]["id"]

    single = client.get(f"/api/v1/events/{event_id}")
    assert single.status_code == 200
    assert single.json()["id"] == event_id


def test_event_pagination_and_filtering(client):
    for i in range(5):
        client.post(
            "/api/v1/demo/protected",
            json={"message": f"p-{i}", "captcha_token": "mock-valid-token"},
            headers={"User-Agent": "Mozilla/5.0"},
        )

    page1 = client.get("/api/v1/events", params={"page": 1, "page_size": 2})
    assert page1.status_code == 200
    body = page1.json()
    assert len(body["items"]) == 2
    assert body["page"] == 1
    assert body["total"] >= 5

    filtered = client.get("/api/v1/events", params={"outcome": "allowed"})
    assert filtered.status_code == 200
    assert all(i["outcome"] == "allowed" for i in filtered.json()["items"])


def test_dashboard_metrics(client):
    client.post(
        "/api/v1/demo/protected",
        json={"message": "metrics", "captcha_token": "mock-valid-token"},
        headers={"User-Agent": "Mozilla/5.0"},
    )
    resp = client.get("/api/v1/analytics/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["summary"]["total_requests"] >= 1
    assert "activity" in data
    assert "recent_events" in data


def test_config_endpoints_hide_secrets(client):
    det = client.get("/api/v1/config/detection")
    assert det.status_code == 200
    assert "turnstile_secret" not in det.text.lower()
    assert "secret_key" not in det.text.lower()

    cap = client.get("/api/v1/config/captcha")
    assert cap.status_code == 200
    body = cap.json()
    assert "secret" not in body or body.get("secret_configured") in (True, False)
    assert "turnstile_secret_key" not in body

    rl = client.get("/api/v1/config/rate-limits")
    assert rl.status_code == 200
    assert "limitations" in rl.json()


def test_event_not_found(client):
    resp = client.get("/api/v1/events/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404
