"""Application configuration loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for BotShield Lab.

    Secrets must never be exposed through API responses.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "BotShield Lab"
    app_env: Literal["development", "production", "test"] = "development"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Database
    database_url: str = "sqlite:///./botshield.db"

    # Rate limiting
    rate_limit_enabled: bool = True
    rate_limit_requests: int = Field(default=10, ge=1, le=1000)
    rate_limit_window_seconds: int = Field(default=60, ge=1, le=3600)
    # "memory" for single-process; "redis" for multi-worker (requires redis_url)
    rate_limit_storage: Literal["memory", "redis"] = "memory"
    redis_url: str = "redis://localhost:6379/0"

    # Bot detection thresholds
    detection_window_seconds: int = Field(default=60, ge=5, le=3600)
    detection_frequency_threshold: int = Field(default=8, ge=2, le=500)
    detection_repeat_endpoint_threshold: int = Field(default=5, ge=2, le=500)
    detection_suspicious_score_threshold: int = Field(default=40, ge=1, le=99)
    detection_high_risk_score_threshold: int = Field(default=70, ge=2, le=100)
    detection_captcha_trigger_score: int = Field(default=50, ge=0, le=100)

    # CAPTCHA (Cloudflare Turnstile)
    captcha_enabled: bool = False
    captcha_provider: Literal["turnstile", "mock"] = "mock"
    turnstile_site_key: str = ""
    turnstile_secret_key: str = ""
    turnstile_verify_url: str = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    # Mock CAPTCHA must be explicitly enabled and only works outside production
    captcha_mock_enabled: bool = True
    captcha_mock_valid_token: str = "mock-valid-token"

    # Client identity (only trust forwarded headers when behind a trusted proxy)
    trust_forwarded_headers: bool = False
    trusted_proxy_ips: str = ""

    # Simulation safety limits
    simulation_max_requests: int = Field(default=50, ge=1, le=100)
    simulation_min_interval_ms: int = Field(default=100, ge=50, le=60000)
    simulation_allowed_host: str = "127.0.0.1,localhost"

    @field_validator("cors_origins", mode="before")
    @classmethod
    def strip_cors(cls, value: str) -> str:
        return value.strip() if isinstance(value, str) else value

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def trusted_proxy_ip_list(self) -> list[str]:
        return [ip.strip() for ip in self.trusted_proxy_ips.split(",") if ip.strip()]

    @property
    def simulation_allowed_hosts(self) -> list[str]:
        return [h.strip() for h in self.simulation_allowed_host.split(",") if h.strip()]

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    def validate_captcha_config(self) -> None:
        """Raise if CAPTCHA is misconfigured for the current environment."""
        if not self.captcha_enabled:
            return
        if self.captcha_provider == "mock":
            if self.is_production:
                raise ValueError(
                    "Mock CAPTCHA provider must never be used in production. "
                    "Set CAPTCHA_PROVIDER=turnstile and provide Turnstile keys."
                )
            if not self.captcha_mock_enabled:
                raise ValueError(
                    "Mock CAPTCHA is selected but CAPTCHA_MOCK_ENABLED is false."
                )
        elif self.captcha_provider == "turnstile":
            if not self.turnstile_secret_key or not self.turnstile_site_key:
                raise ValueError(
                    "Turnstile provider requires TURNSTILE_SITE_KEY and TURNSTILE_SECRET_KEY."
                )


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()
