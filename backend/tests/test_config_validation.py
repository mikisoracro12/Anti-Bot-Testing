import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_default_settings():
    # Explicit overrides so process env from conftest cannot skew assertions
    s = Settings(
        app_env="development",
        rate_limit_requests=10,
        rate_limit_storage="memory",
    )
    assert s.rate_limit_requests == 10
    assert s.rate_limit_storage == "memory"



def test_captcha_mock_blocked_in_production_validation():
    s = Settings(
        app_env="production",
        captcha_enabled=True,
        captcha_provider="mock",
        captcha_mock_enabled=True,
    )
    with pytest.raises(ValueError, match="never be used in production"):
        s.validate_captcha_config()


def test_turnstile_requires_keys():
    s = Settings(
        app_env="development",
        captcha_enabled=True,
        captcha_provider="turnstile",
        turnstile_site_key="",
        turnstile_secret_key="",
    )
    with pytest.raises(ValueError, match="TURNSTILE"):
        s.validate_captcha_config()


def test_rate_limit_bounds():
    with pytest.raises(ValidationError):
        Settings(rate_limit_requests=0)
