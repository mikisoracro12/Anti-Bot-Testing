"""Schemas for dashboard analytics."""

from datetime import datetime

from pydantic import BaseModel, Field


class SummaryMetrics(BaseModel):
    total_requests: int = 0
    allowed_requests: int = 0
    blocked_requests: int = 0
    suspected_bot_requests: int = 0
    rate_limit_violations: int = 0
    captcha_failures: int = 0


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    total: int = 0
    allowed: int = 0
    blocked: int = 0
    rate_limited: int = 0
    suspected: int = 0


class DetectionReasonCount(BaseModel):
    reason: str
    count: int


class DashboardMetrics(BaseModel):
    summary: SummaryMetrics
    activity: list[TimeSeriesPoint] = Field(default_factory=list)
    detection_reasons: list[DetectionReasonCount] = Field(default_factory=list)
    recent_events: list[dict] = Field(default_factory=list)


class DetectionConfigOut(BaseModel):
    """Non-sensitive detection configuration exposed to the UI."""

    window_seconds: int
    frequency_threshold: int
    repeat_endpoint_threshold: int
    suspicious_score_threshold: int
    high_risk_score_threshold: int
    captcha_trigger_score: int
    rate_limit_enabled: bool
    rate_limit_requests: int
    rate_limit_window_seconds: int
    rate_limit_storage: str
    captcha_enabled: bool
    captcha_provider: str
    # Site key is public by design for Turnstile widget; secret is never included
    turnstile_site_key: str | None = None
    trust_forwarded_headers: bool
    notes: list[str] = Field(default_factory=list)


class RateLimitConfigOut(BaseModel):
    enabled: bool
    requests: int
    window_seconds: int
    storage: str
    redis_configured: bool
    limitations: list[str]


class CaptchaStatusOut(BaseModel):
    enabled: bool
    provider: str
    site_key_configured: bool
    secret_configured: bool
    mock_enabled: bool
    site_key: str | None = None
    ready: bool
    warnings: list[str] = Field(default_factory=list)
