import pytest

from app.core.config import Settings
from app.services.captcha import CaptchaService


@pytest.mark.asyncio
async def test_mock_captcha_success():
    settings = Settings(
        app_env="test",
        captcha_enabled=True,
        captcha_provider="mock",
        captcha_mock_enabled=True,
        captcha_mock_valid_token="mock-valid-token",
    )
    svc = CaptchaService(settings)
    result = await svc.verify("mock-valid-token")
    assert result.success is True


@pytest.mark.asyncio
async def test_mock_captcha_failure():
    settings = Settings(
        app_env="test",
        captcha_enabled=True,
        captcha_provider="mock",
        captcha_mock_enabled=True,
        captcha_mock_valid_token="mock-valid-token",
    )
    svc = CaptchaService(settings)
    result = await svc.verify("wrong-token")
    assert result.success is False
    assert "invalid-input-response" in result.error_codes


@pytest.mark.asyncio
async def test_missing_token():
    settings = Settings(
        app_env="test",
        captcha_enabled=True,
        captcha_provider="mock",
        captcha_mock_enabled=True,
    )
    svc = CaptchaService(settings)
    result = await svc.verify(None)
    assert result.success is False
    assert "missing-input-response" in result.error_codes


@pytest.mark.asyncio
async def test_mock_forbidden_in_production():
    settings = Settings(
        app_env="production",
        captcha_enabled=True,
        captcha_provider="mock",
        captcha_mock_enabled=True,
        captcha_mock_valid_token="mock-valid-token",
    )
    svc = CaptchaService(settings)
    result = await svc.verify("mock-valid-token")
    assert result.success is False
    assert "mock-forbidden-in-production" in result.error_codes


def test_captcha_verify_endpoint_success(client):
    resp = client.post(
        "/api/v1/demo/captcha/verify", json={"token": "mock-valid-token"}
    )
    assert resp.status_code == 200
    assert resp.json()["success"] is True


def test_captcha_verify_endpoint_failure(client):
    resp = client.post("/api/v1/demo/captcha/verify", json={"token": "bad"})
    assert resp.status_code == 200
    assert resp.json()["success"] is False


def test_invalid_payload(client):
    resp = client.post("/api/v1/demo/captcha/verify", json={})
    assert resp.status_code == 422
